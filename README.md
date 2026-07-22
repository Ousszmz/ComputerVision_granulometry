# ComputerVision_granulometry

Detection d'humidite et granulometrie du sterile par vision par ordinateur.
Projet de stage — OCP / Laverie Beni Amir.

Analyse d'images d'un convoyeur pour caracteriser le minerai : taux de
remplissage, texture, et a terme distribution granulometrique.

---

## 📄 Documentation

**➡️ [`HANDOFF.md`](HANDOFF.md) contient l'etat complet du projet** : donnees valides,
resultats mesures, pieges connus et plan d'action. **A lire en premier.**

---

## Pipeline

```
video  ──►  clean_frames.py  ──►  test1.py  ──►  clustering_humidite.py
            filtre flou           features        KMeans / DBSCAN
            + doublons            (26 par image)  + diagnostic de fuite
```

| Script | Role |
|---|---|
| [`assets/clean_frames.py`](assets/clean_frames.py) | Filtre les images floues et les quasi-doublons (Tenengrad + plus net par fenetre) |
| [`test1.py`](test1.py) | Extrait 26 features : masque pierre/tapis, GLCM multi-echelle, LBP, HSV |
| [`clustering_humidite.py`](clustering_humidite.py) | KMeans + DBSCAN, avec diagnostic de fuite cluster-vs-video |
| [`visual.py`](visual.py) | Histogrammes rapides des features |

## Installation

```bash
python3 -m venv my_env
./my_env/bin/pip install opencv-python numpy pandas scikit-learn scikit-image matplotlib
```
`ffmpeg` est requis pour l'extraction des images.

## Utilisation

```bash
./my_env/bin/python test1.py               # -> features.csv
./my_env/bin/python clustering_humidite.py # -> resultats/
```
> Toujours utiliser `./my_env/bin/python`, pas le `python` systeme.

---

## ⚠️ Etat actuel : donnees insuffisantes

**11 images exploitables** seulement (toutes issues de v1.mp4, 20 s).
C'est moins que le nombre de features (26) : **tout clustering serait de
l'ajustement de bruit.** Il en faudrait ~260.

Le code fonctionne — c'est la matiere premiere qui manque.
**Priorite : filmer davantage, camera stabilisee, minerai propre.**
Details dans [`HANDOFF.md`](HANDOFF.md) section 8.

## Note sur les donnees

Les videos sources ne sont pas versionnees (voir [`.gitignore`](.gitignore)).
**`assets/v1.mp4` est la seule donnee valide du projet — a sauvegarder ailleurs.**
