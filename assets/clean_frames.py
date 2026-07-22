"""
Filter raw video frames down to a clean, diverse, sharp set for CV training.

Problem with a plain "blur score > threshold" filter on video frames:
  - consecutive frames overlap heavily, so a lot of "sharp enough" frames
    are near-duplicates of each other -> wasted labeling effort
  - a single global threshold is content-dependent (a busy, high-texture
    frame scores higher than a sparse one at the same real sharpness),
    so it keeps/drops near-identical frames almost at random near the cutoff

Strategy used here:
  1. score every frame's sharpness (Tenengrad: mean squared Sobel gradient)
  2. drop anything below an adaptive floor (bottom FLOOR_PERCENTILE of the
     whole set) - catches genuinely blurry frames regardless of window
  3. slide a window of WINDOW consecutive frames, keep only the sharpest
     survivor in each window
  4. skip a kept candidate if it's nearly identical to the last frame we
     actually kept (dedup), so static stretches of video don't flood the
     output with repeats
  5. copy survivors to data/clean/ and write scores.csv with every
     decision so the run can be audited and re-tuned without guessing
"""

import csv
import os
import shutil

import cv2
import numpy as np

SRC = "data/raw"
DST = "data/clean"

WINDOW = 5              # keep at most 1 frame per this many consecutive frames
FLOOR_PERCENTILE = 10   # drop the blurriest this-% of frames outright
DEDUP_MAX_DIFF = 4.0    # mean abs pixel diff (0-255, downscaled) below this = duplicate

# Frames 0166-0196: manually reviewed. The whole stretch is motion-blurred
# (camera moving) with no sharp frame in any window, so "sharpest in window"
# still returns a blurry frame. The sharpness score alone can't distinguish
# this from a sparse-but-sharp scene (scores overlap), so these filenames
# are excluded outright regardless of score. Re-check by eye if the source
# video changes.
MANUAL_REJECT = {
    "frame_0167.jpg", "frame_0174.jpg", "frame_0177.jpg", "frame_0185.jpg",
    "frame_0190.jpg", "frame_0193.jpg", "frame_0196.jpg",
}


def sharpness(gray):
    sx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    return float(np.mean(sx**2 + sy**2))


def fingerprint(gray):
    # small, size-normalized version of the frame, used only to detect
    # near-duplicate content between consecutively kept frames
    return cv2.resize(gray, (64, 64), interpolation=cv2.INTER_AREA).astype(np.float32)


def frame_diff(fp_a, fp_b):
    return float(np.mean(np.abs(fp_a - fp_b)))


def main():
    os.makedirs(DST, exist_ok=True)
    for f in os.listdir(DST):
        os.remove(os.path.join(DST, f))

    files = sorted(os.listdir(SRC))

    frames = []  # list of dict: filename, gray, score
    for f in files:
        path = os.path.join(SRC, f)
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            print(f"Could not read: {f}")
            continue
        frames.append({"filename": f, "gray": img, "score": sharpness(img)})

    if not frames:
        print("No readable frames found.")
        return

    scores = np.array([fr["score"] for fr in frames])
    floor = float(np.percentile(scores, FLOOR_PERCENTILE))

    rows = []
    kept = 0
    last_kept_fp = None

    for start in range(0, len(frames), WINDOW):
        window = frames[start:start + WINDOW]
        candidates = [fr for fr in window if fr["score"] >= floor]

        if not candidates:
            for fr in window:
                rows.append([fr["filename"], f"{fr['score']:.1f}", "drop", "below_floor"])
            continue

        best = max(candidates, key=lambda fr: fr["score"])

        if best["filename"] in MANUAL_REJECT:
            for fr in window:
                reason = "manual_reject_motion_blur" if fr is best else (
                    "below_floor" if fr["score"] < floor else "not_sharpest_in_window")
                rows.append([fr["filename"], f"{fr['score']:.1f}", "drop", reason])
            continue

        for fr in window:
            if fr is not best:
                rows.append([fr["filename"], f"{fr['score']:.1f}", "drop",
                             "below_floor" if fr["score"] < floor else "not_sharpest_in_window"])

        best_fp = fingerprint(best["gray"])
        if last_kept_fp is not None:
            diff = frame_diff(best_fp, last_kept_fp)
            if diff < DEDUP_MAX_DIFF:
                rows.append([best["filename"], f"{best['score']:.1f}", "drop",
                             f"duplicate_of_previous_kept(diff={diff:.2f})"])
                continue

        shutil.copy(os.path.join(SRC, best["filename"]), os.path.join(DST, best["filename"]))
        rows.append([best["filename"], f"{best['score']:.1f}", "keep", "sharpest_in_window"])
        kept += 1
        last_kept_fp = best_fp

    with open(os.path.join(DST, "..", "scores.csv"), "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["filename", "sharpness_score", "decision", "reason"])
        writer.writerows(rows)

    print(f"Sharpness floor (p{FLOOR_PERCENTILE}): {floor:.1f}")
    print(f"Kept: {kept}")
    print(f"Dropped: {len(frames) - kept}")
    print(f"Total frames: {len(frames)}")
    print(f"Clean frames -> {DST}/")
    print(f"Audit log   -> data/scores.csv")


if __name__ == "__main__":
    main()
