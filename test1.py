"""
Extraction de features — granulometrie / humidite du sterile

Ameliorations par rapport a la version initiale :
  1. MASQUAGE DU TAPIS : les features sont calculees uniquement sur les pixels
     "pierre". Avant, gray_mean correlait a +0.73 avec le taux de couverture :
     on mesurait la QUANTITE de pierre, pas son humidite.
  2. stone_coverage_frac devient une feature EXPLICITE (vraie info de debit,
     au lieu d'etre cachee dans la luminance).
  3. GLCM multi-echelle et multi-angle (avant : 1 seule distance, 1 seul angle
     horizontal, 256 niveaux). Moyenne sur les angles => invariance a la rotation.
  4. GLCM calculee en excluant les paires impliquant un pixel de tapis.

Entree  : dossier d'images (IMAGE_FOLDER)
Sortie  : features.csv (une ligne par image)

Lancer :  ./my_env/bin/python test1.py
"""

import os

import cv2
import numpy as np
import pandas as pd
from skimage.feature import graycomatrix, graycoprops, local_binary_pattern

# =====================================================================
# CONFIGURATION
# =====================================================================

IMAGE_FOLDER = "assets/data/clean_v1"
CSV_OUT = "features.csv"

# --- GLCM ------------------------------------------------------------
# Plusieurs distances = plusieurs echelles de texture (granulometrie).
# Plusieurs angles, moyennes ensuite = invariance a la rotation.
GLCM_DISTANCES = [1, 2, 4, 8]
GLCM_ANGLES = [0, np.pi / 4, np.pi / 2, 3 * np.pi / 4]
GLCM_LEVELS = 64          # quantification : 256 -> matrice creuse, lente, bruitee
GLCM_PROPS = ["contrast", "homogeneity", "energy", "correlation"]

# --- LBP -------------------------------------------------------------
LBP_RADIUS = 1
LBP_N_POINTS = 8 * LBP_RADIUS

# --- Masque pierre / tapis -------------------------------------------
# Le tapis est du caoutchouc sombre, la pierre est claire.
#
# Un simple seuil d'Otsu ne suffit PAS : le reflet du soleil sur le tapis
# mouille est une large tache brillante qui etait classee comme pierre
# (mesure : 12.8 % de l'image sur frame_0008). Ni la couleur ni la texture
# ne la separent proprement de la pierre — les distributions se recouvrent.
#
# Solution : transformation "top-hat blanc" = image - ouverture(image).
# Par construction, elle SUPPRIME les zones claires plus GRANDES que le noyau
# (le reflet, large et diffus) et CONSERVE les objets clairs plus PETITS
# (les cailloux). On seuille ensuite par Otsu sur le resultat.
# Effet mesure : plus grosse composante 12.8 % -> 1.3 % de l'image.
TOPHAT_KERNEL = 41        # doit etre > au plus gros caillou, < au reflet
MORPH_KERNEL = 5
# On erode le masque avant les stats de voisinage (LBP) pour eviter que les
# pixels de bordure pierre/tapis polluent la texture.
EROSION_KERNEL = 5
# Si le masque est aberrant, l'image est signalee plutot que silencieusement
# integree au jeu de donnees.
COVERAGE_MIN = 0.02
COVERAGE_MAX = 0.95


# =====================================================================
# MASQUE PIERRE / TAPIS
# =====================================================================

def construire_masque_pierre(gray):
    """Separe la pierre (claire) du tapis (sombre).

    Top-hat blanc puis Otsu : elimine le reflet du soleil sur le tapis mouille
    tout en conservant les cailloux (voir le commentaire sur TOPHAT_KERNEL).

    Retourne un masque booleen : True = pixel de pierre.
    """
    noyau_th = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (TOPHAT_KERNEL, TOPHAT_KERNEL))
    tophat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, noyau_th)

    _, brut = cv2.threshold(tophat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    noyau = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (MORPH_KERNEL, MORPH_KERNEL))
    # Ouverture : supprime les petits points brillants (reflets sur tapis mouille)
    masque = cv2.morphologyEx(brut, cv2.MORPH_OPEN, noyau)
    # Fermeture : rebouche les petits trous a l'interieur des cailloux
    masque = cv2.morphologyEx(masque, cv2.MORPH_CLOSE, noyau)

    return masque > 0


def eroder(masque):
    """Retire une bande de bordure : evite la contamination pierre/tapis."""
    noyau = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (EROSION_KERNEL, EROSION_KERNEL))
    return cv2.erode(masque.astype(np.uint8), noyau).astype(bool)


# =====================================================================
# GLCM MASQUEE
# =====================================================================

def glcm_masquee(gray, masque):
    """GLCM multi-distance / multi-angle, calculee sur la pierre uniquement.

    Astuce : on quantifie la pierre sur les niveaux 1..L et on met le tapis a 0,
    puis on supprime la ligne 0 et la colonne 0 de la matrice. Toutes les paires
    de pixels impliquant le tapis disparaissent ainsi du calcul — y compris les
    transitions pierre/tapis, qui sinon creeraient un faux contraste enorme.

    Retourne un dict {nom_feature: valeur}, moyenne sur les angles.
    """
    # Quantification sur 1..GLCM_LEVELS (0 est reserve au fond)
    q = (gray.astype(np.float64) / 256.0 * GLCM_LEVELS).astype(np.int32) + 1
    q = np.clip(q, 1, GLCM_LEVELS).astype(np.uint8)
    q[~masque] = 0

    glcm = graycomatrix(
        q,
        distances=GLCM_DISTANCES,
        angles=GLCM_ANGLES,
        levels=GLCM_LEVELS + 1,     # +1 pour le niveau 0 = fond
        symmetric=True,
        normed=False,               # graycoprops normalise lui-meme
    )

    # On jette tout ce qui touche au fond. graycoprops renormalise ensuite.
    glcm = glcm[1:, 1:, :, :]

    feats = {}
    for prop in GLCM_PROPS:
        with np.errstate(invalid="ignore", divide="ignore"):
            valeurs = graycoprops(glcm, prop)      # forme (n_distances, n_angles)
        # Moyenne sur les angles -> invariance a la rotation
        par_distance = np.nanmean(valeurs, axis=1)
        for d, val in zip(GLCM_DISTANCES, par_distance):
            feats[f"glcm_{prop}_d{d}"] = float(val)

    return feats


# =====================================================================
# EXTRACTION D'UNE IMAGE
# =====================================================================

def extraire_features(image_path):
    image = cv2.imread(image_path)
    if image is None:
        return None

    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    masque = construire_masque_pierre(gray)
    couverture = float(masque.mean())

    # Masque erode pour tout ce qui depend du voisinage (LBP)
    masque_lbp = eroder(masque)
    if not masque_lbp.any():          # cailloux trop fins pour survivre a l'erosion
        masque_lbp = masque

    if not masque.any():
        print(f"  !! masque vide, image ignoree : {os.path.basename(image_path)}")
        return None

    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    S = hsv[:, :, 1]
    V = hsv[:, :, 2]

    # --- Intensite et couleur, PIERRE UNIQUEMENT ---------------------
    gray_pierre = gray[masque]
    S_pierre = S[masque]
    V_pierre = V[masque]

    # --- LBP : calcul sur toute l'image (besoin du voisinage), --------
    #     statistiques sur la pierre erodee uniquement
    lbp = local_binary_pattern(gray, LBP_N_POINTS, LBP_RADIUS, method="uniform")
    lbp_pierre = lbp[masque_lbp]

    feats = {
        "image": os.path.basename(image_path),

        # Debit / remplissage : vraie information, desormais explicite
        "stone_coverage_frac": couverture,

        # Intensite (pierre seule)
        "gray_mean": float(np.mean(gray_pierre)),
        "gray_median": float(np.median(gray_pierre)),
        "gray_std": float(np.std(gray_pierre)),

        # HSV (pierre seule) — indices d'humidite, mais sensibles a l'eclairage
        "S_mean": float(np.mean(S_pierre)),
        "S_std": float(np.std(S_pierre)),
        "V_mean": float(np.mean(V_pierre)),
        "V_std": float(np.std(V_pierre)),

        # LBP (pierre seule)
        "lbp_mean": float(np.mean(lbp_pierre)),
        "lbp_std": float(np.std(lbp_pierre)),
    }

    feats.update(glcm_masquee(gray, masque))

    if not (COVERAGE_MIN <= couverture <= COVERAGE_MAX):
        print(f"  ! couverture suspecte ({couverture:.1%}) : "
              f"{os.path.basename(image_path)} — verifier le masque")

    return feats


# =====================================================================
# BOUCLE PRINCIPALE
# =====================================================================

def main():
    if not os.path.isdir(IMAGE_FOLDER):
        raise SystemExit(f"Dossier introuvable : {IMAGE_FOLDER}")

    fichiers = sorted(
        f for f in os.listdir(IMAGE_FOLDER)
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp"))
    )
    if not fichiers:
        raise SystemExit(f"Aucune image dans {IMAGE_FOLDER}")

    lignes = []
    for nom in fichiers:
        feats = extraire_features(os.path.join(IMAGE_FOLDER, nom))
        if feats is not None:
            lignes.append(feats)

    df = pd.DataFrame(lignes)
    df.to_csv(CSV_OUT, index=False)

    colonnes_features = [c for c in df.columns if c != "image"]
    print(f"\nImages traitees : {len(df)} / {len(fichiers)}")
    print(f"Features par image : {len(colonnes_features)}")
    print(f"Couverture pierre : {df['stone_coverage_frac'].min():.1%} "
          f"-> {df['stone_coverage_frac'].max():.1%}")
    print(f"Ecrit dans : {CSV_OUT}")

    # Garde-fou : avec moins de 10 echantillons par feature, un clustering
    # ne fait qu'ajuster du bruit.
    mini = 10 * len(colonnes_features)
    if len(df) < mini:
        print(f"\n! {len(df)} images pour {len(colonnes_features)} features.")
        print(f"  Il en faudrait ~{mini} pour un clustering fiable.")
        print("  -> filmer davantage avant d'interpreter des clusters.")


if __name__ == "__main__":
    main()
