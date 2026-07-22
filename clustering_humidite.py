"""
Phase 4 — Clustering non supervise des features d'humidite
Projet OCP / Laverie Beni Amir — detection d'humidite du sterile

Entree  : features.csv (une ligne par image)
Sorties : clusters.csv, elbow.png, silhouette.png, pca.png, pca_par_source.png

Lancer :  python clustering_humidite.py
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.metrics import (silhouette_score, adjusted_rand_score,
                             normalized_mutual_info_score)

# =====================================================================
# 1. CONFIGURATION  --  la seule partie a modifier
# =====================================================================

CSV_IN = "features.csv"
OUT_DIR = "resultats"

# --- Jeux de features -------------------------------------------------
# "toutes"  : tout, y compris la luminosite/couleur (sensible au soleil)
# "robuste" : uniquement texture + dispersion, beaucoup moins sensible
#             a l'eclairage global. C'est le controle a comparer.
FEATURES_TOUTES = [
    "gray_mean", "gray_median", "gray_std",
    "S_mean", "S_std", "V_mean", "V_std",
    "glcm_contrast", "glcm_homogeneity", "glcm_energy", "glcm_correlation",
    "lbp_mean", "lbp_std",
]
FEATURES_ROBUSTE = [
    "gray_std",
    "glcm_contrast", "glcm_homogeneity", "glcm_energy", "glcm_correlation",
    "lbp_mean", "lbp_std",
]

JEU = "robuste"          # <- mettre "robuste" pour le second passage
K_MIN, K_MAX = 2, 8

# --- Origine de chaque image (GARDE-FOU ANTI-CONFUSION) ---------------
# Sert UNIQUEMENT au diagnostic : jamais au clustering lui-meme.
# Adapter aux bornes reelles de tes videos / sorties terrain.
BORNES_SOURCE = {
    "video_1": (1, 10),
    "video_2": (11, 42),
    "video_3": (43, 152),
    "video_4": (153, 165),   # aucune image n'a survecu au filtre flou (video entiere trop bougee)
    "video_5": (166, 196),   # idem : aucune image n'a survecu au filtre flou
}

# Restreindre l'analyse a une seule session (eclairage ~constant).
# None = tout le dataset ; "video_3" = analyse intra-session.
FILTRE_SOURCE = None


def source_de(nom_image):
    """Deduit la video d'origine a partir du numero dans le nom de fichier."""
    num = int("".join(c for c in nom_image if c.isdigit())[-4:])
    for nom, (debut, fin) in BORNES_SOURCE.items():
        if debut <= num <= fin:
            return nom
    return "inconnu"


# =====================================================================
# 2. CHARGEMENT ET STANDARDISATION
# =====================================================================

os.makedirs(OUT_DIR, exist_ok=True)
df = pd.read_csv(CSV_IN)
df["source"] = df["image"].apply(source_de)

if FILTRE_SOURCE is not None:
    df = df[df["source"] == FILTRE_SOURCE].reset_index(drop=True)
    print(f"ANALYSE INTRA-SESSION : {FILTRE_SOURCE} uniquement\n")

features = FEATURES_TOUTES if JEU == "toutes" else FEATURES_ROBUSTE
X = df[features].values

print(f"{len(df)} images, {len(features)} features (jeu = '{JEU}')")
print(df["source"].value_counts().to_string(), "\n")

# Indispensable : sans ca, gray_mean (0-255) ecrase glcm_energy (0-0.05)
X_std = StandardScaler().fit_transform(X)


# =====================================================================
# 3. CHOIX DE K : methode du coude + score de silhouette
# =====================================================================

inerties, silhouettes, Ks = [], [], list(range(K_MIN, K_MAX + 1))

for k in Ks:
    km = KMeans(n_clusters=k, n_init=20, random_state=42).fit(X_std)
    inerties.append(km.inertia_)
    silhouettes.append(silhouette_score(X_std, km.labels_))
    print(f"K={k}  inertie={km.inertia_:8.1f}  silhouette={silhouettes[-1]:.3f}")

plt.figure(figsize=(6, 4))
plt.plot(Ks, inerties, "o-")
plt.xlabel("Nombre de clusters K"); plt.ylabel("Inertie")
plt.title("Methode du coude"); plt.grid(alpha=.3); plt.tight_layout()
plt.savefig(f"{OUT_DIR}/elbow.png", dpi=120); plt.close()

plt.figure(figsize=(6, 4))
plt.plot(Ks, silhouettes, "o-", color="darkorange")
plt.xlabel("Nombre de clusters K"); plt.ylabel("Score de silhouette")
plt.title("Silhouette (plus haut = mieux separe)"); plt.grid(alpha=.3); plt.tight_layout()
plt.savefig(f"{OUT_DIR}/silhouette.png", dpi=120); plt.close()

K = Ks[int(np.argmax(silhouettes))]
print(f"\n-> K retenu (meilleure silhouette) : {K}")


# =====================================================================
# 4. K-MEANS FINAL + DBSCAN DE CONTROLE
# =====================================================================

kmeans = KMeans(n_clusters=K, n_init=20, random_state=42).fit(X_std)
df["cluster"] = kmeans.labels_

db = DBSCAN(eps=1.5, min_samples=5).fit(X_std)   # eps a ajuster si besoin
df["dbscan"] = db.labels_
n_bruit = int((db.labels_ == -1).sum())
print(f"DBSCAN : {len(set(db.labels_)) - (1 if n_bruit else 0)} groupes, "
      f"{n_bruit} points aberrants")


# =====================================================================
# 5. DIAGNOSTIC CRITIQUE : les clusters = les videos ?
# =====================================================================

if df["source"].nunique() < 2:
    print("\n(Une seule session : diagnostic cluster-vs-video sans objet.)")
else:
    print("\n" + "=" * 62)
    print("TABLE DE CONFUSION  cluster x video d'origine")
    print("=" * 62)
    croise = pd.crosstab(df["cluster"], df["source"])
    print(croise.to_string())

    # ARI / NMI proches de 1 => le clustering ne fait que retrouver tes videos.
    ari = adjusted_rand_score(df["source"], df["cluster"])
    nmi = normalized_mutual_info_score(df["source"], df["cluster"])
    print(f"\nARI (cluster vs video) = {ari:.3f}   NMI = {nmi:.3f}")

    if nmi > 0.80:
        print("!! ALERTE FORTE : les clusters reproduisent tes videos.")
        print("   Ce n'est PAS un resultat d'humidite.")
    elif nmi > 0.45:
        print("!  Dependance partielle : une partie de la separation vient")
        print("   des conditions de prise de vue. A interpreter avec prudence.")
    else:
        print("OK : les clusters melangent les videos -> signal plutot intra-scene.")

    print("\nRepartition de chaque video entre les clusters (en %) :")
    print((croise / croise.sum(axis=0) * 100).round(1).to_string())


# =====================================================================
# 6. PROFIL PHYSIQUE DE CHAQUE CLUSTER  (pour l'interpretation)
# =====================================================================

print("\n" + "=" * 62)
print("MOYENNE DES FEATURES PAR CLUSTER (valeurs brutes)")
print("=" * 62)
profil = df.groupby("cluster")[features].mean().round(3)
print(profil.to_string())
profil.to_csv(f"{OUT_DIR}/profil_clusters.csv")


# =====================================================================
# 7. VISUALISATION PCA
# =====================================================================

pca = PCA(n_components=2)
P = pca.fit_transform(X_std)
var = pca.explained_variance_ratio_
print(f"\nPCA : PC1={var[0]:.1%}, PC2={var[1]:.1%} de variance expliquee")

plt.figure(figsize=(7, 5.5))
sc = plt.scatter(P[:, 0], P[:, 1], c=df["cluster"], cmap="viridis", s=45,
                 edgecolor="k", linewidth=.3)
plt.colorbar(sc, label="cluster")
plt.xlabel(f"PC1 ({var[0]:.0%})"); plt.ylabel(f"PC2 ({var[1]:.0%})")
plt.title(f"Clusters K-means (K={K}) — jeu '{JEU}'")
plt.grid(alpha=.3); plt.tight_layout()
plt.savefig(f"{OUT_DIR}/pca.png", dpi=120); plt.close()

plt.figure(figsize=(7, 5.5))
for nom in sorted(df["source"].unique()):
    m = df["source"] == nom
    plt.scatter(P[m, 0], P[m, 1], s=45, label=nom, edgecolor="k", linewidth=.3)
plt.legend(); plt.xlabel(f"PC1 ({var[0]:.0%})"); plt.ylabel(f"PC2 ({var[1]:.0%})")
plt.title("Meme nuage, colore par video d'origine")
plt.grid(alpha=.3); plt.tight_layout()
plt.savefig(f"{OUT_DIR}/pca_par_source.png", dpi=120); plt.close()

# Contribution des features a PC1 : quelle grandeur porte la separation ?
poids = pd.Series(pca.components_[0], index=features).sort_values(key=abs,
                                                                  ascending=False)
print("\nFeatures qui pesent le plus sur PC1 :")
print(poids.head(6).round(3).to_string())


# =====================================================================
# 8. SAUVEGARDE
# =====================================================================

df.to_csv(f"{OUT_DIR}/clusters.csv", index=False)
print(f"\nTermine. Resultats dans ./{OUT_DIR}/")
print("Compare pca.png et pca_par_source.png : si les deux se ressemblent,")
print("tes clusters ne mesurent que les conditions de prise de vue.")