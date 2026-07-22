# STAGE_CV — État du projet / Handoff

**Dernière mise à jour :** 2026-07-22
**But du projet :** OCP / Laverie Beni Amir — détection d'humidité et granulométrie du stérile par vision par ordinateur, à partir de vidéos d'un convoyeur.

Ce document contient tout le contexte nécessaire pour reprendre le travail dans une nouvelle session, sans rien perdre.

---

## 1. Résumé exécutif — où on en est

| Question | Réponse |
|---|---|
| Combien d'images exploitables ? | **11** (toutes issues de v1.mp4) |
| Peut-on faire du clustering ? | **Non, pas encore** — 11 échantillons < 13 features |
| Blocage principal | **Manque de données valides**, pas un problème de code |
| Action prioritaire | **Filmer davantage** (caméra stabilisée, minerai propre) |

Le pipeline de code fonctionne. Ce qui manque, c'est la matière première.

---

## 2. Les vidéos — ce qui est valide et pourquoi

Confirmé avec le superviseur : **seule v1.mp4 contient des données valides.**

> **Définition de « donnée valide »** : la caméra capture de la **pierre propre** — pas de boue, pas de produit.
> Si de la boue / du produit est visible, **c'est un problème process** : il faut le **signaler au lavage**.
> (Ce n'est donc pas un défaut à corriger en code — c'est une anomalie terrain à remonter.)

| Vidéo | Durée | Résolution | Statut | Raison |
|---|---|---|---|---|
| **v1.mp4** | 20.3 s | 848×478 @30fps | ✅ **VALIDE** | Pierre propre, sèche, vérifiée visuellement (début/milieu/fin) |
| v2.mp4 | 64.9 s | 848×478 @30fps | ❌ invalide | boue / produit |
| v3.mp4 | 220.1 s | 848×478 @30fps | ❌ invalide | boue / produit |
| v4.mp4 | 26.2 s | 848×478 @30fps | ❌ invalide | + **100 % des images floues** (caméra bougée en continu) |
| v5.mp4 | 61.4 s | **478×850 (portrait !)** | ❌ invalide | + **100 % des images floues** ; orientation différente des autres |

⚠️ **v5 est en portrait**, contrairement à toutes les autres. À ne pas mélanger sans redimensionnement si un jour elle redevient utilisable.

### Cause du flou : caméra tenue à la main
L'utilisateur a confirmé avoir **filmé à main levée, sans chercher la stabilité**.
Preuve mesurée : à l'intérieur de la *même* vidéo (v3), la netteté varie de **~1 000 à ~25 000** (facteur 25×).
Un convoyeur à vitesse constante avec caméra fixe produirait un flou **constant**. Cette variance énorme = **tremblement de main**, pas le convoyeur.

**Conséquence :** ce flou est un artefact de captation, pas un signal physique. Le filtrer était correct.

---

## 3. Ce qui a été fait dans cette session

### 3.1 Correction du filtre de flou
`assets/blurry.py` était **cassé** : le script entier était collé deux fois, ligne 26 indentée → `IndentationError`. Il ne pouvait pas s'exécuter. *(Ce fichier a depuis été supprimé — il n'existe plus.)*

Remplacé par **`assets/clean_frames.py`** :
- **Score de netteté** : Tenengrad (énergie du gradient de Sobel) au lieu de la variance du Laplacien
- **Plancher adaptatif** : rejette les 10 % les plus flous (`FLOOR_PERCENTILE = 10`)
- **Le plus net par fenêtre** : garde 1 seule image par fenêtre de N images consécutives → supprime les quasi-doublons (les frames vidéo se chevauchent énormément)
- **Garde-fou anti-doublon** : ignore un candidat trop proche de la dernière image gardée
- **`MANUAL_REJECT`** : liste d'images rejetées à la main après contrôle visuel
- **Journal d'audit** : `scores.csv` avec chaque décision + sa raison

Résultat sur l'ancien jeu (196 images, 5 vidéos) : 196 → 31 images.

### 3.2 ⚠️ PIÈGE CONNU dans `clean_frames.py`
```python
MANUAL_REJECT = {"frame_0167.jpg", "frame_0174.jpg", ...}
```
Ces noms correspondent aux images **v5 de l'ancienne extraction** (1 image / 2 s sur les 5 vidéos).
**Si tu ré-extrais des images avec une numérotation différente, cette liste devient fausse et peut rejeter de bonnes images par accident.**
→ **Vider `MANUAL_REJECT` avant toute nouvelle extraction**, puis la reconstituer après contrôle visuel.

De même, `SRC = "data/raw"` et `DST = "data/clean"` sont **relatifs** : le script doit être lancé **depuis `assets/`**.

### 3.3 Clustering — le diagnostic a détecté une fuite
`clustering_humidite.py` contient déjà un excellent garde-fou : il compare les clusters à la vidéo d'origine (ARI / NMI).

Résultats sur les 31 images (avant que v2–v5 soient déclarées invalides) :

| Jeu de features | NMI (cluster vs vidéo) | Verdict |
|---|---|---|
| `toutes` | **0.887** | 🔴 les clusters = les vidéos, pas l'humidité |
| `robuste` (texture seule) | **0.640** | 🟡 dépendance partielle |
| v3 seule (n=23) | — | K=4 trouvé, mais DBSCAN classe 11/23 points en bruit |

**Conclusion : le « signal humidité » n'était que les conditions de prise de vue.**

### 3.4 Test : peut-on travailler sur les données brutes (non filtrées) ?
Testé sur les 196 images brutes. **Réponse : non.**

- **η² = 0.805** → 80.5 % de la variance de netteté est expliquée par l'appartenance au cluster
- `glcm_contrast` corrèle à **r = +0.88** avec le score de netteté
- `glcm_correlation` : r = −0.79 · PC1 : r = −0.72

**Raison physique :** le flou détruit exactement les hautes fréquences que GLCM et LBP mesurent. Un modèle entraîné sur données brutes apprendrait à **détecter le flou**, pas l'humidité.

### 3.5 Ré-extraction dense de v1 — plafond atteint
L'extraction d'origine (1 image / 2 s) ne tirait que **10 images** de v1. Ré-extraction à 5 fps → 102 images → **11 gardées**.

Vérification : ré-extraction à **15 fps → 305 images → exactement les mêmes 11 images gardées.**

➡️ **C'est un vrai plafond.** 20 secondes de vidéo ne contiennent qu'environ 11 « instants » indépendants de minerai. Échantillonner plus dense n'invente pas de contenu. **Le facteur limitant est la durée de tournage.**

### 3.6 🔬 Découverte importante : le tapis fausse les features
Les features actuelles sont calculées sur **toute l'image**, or l'image contient le **tapis noir** (fond) + la **pierre** (objet).

Mesuré sur les 11 images v1 :

| Mesure | Valeur |
|---|---|
| Couverture pierre | 18.2 % → 25.1 % (écart 6.9 pts) |
| **corr(couverture, `gray_mean` image entière)** | **+0.727** |
| corr(couverture, `gray_mean` pierre seule, masque Otsu) | −0.441 |

➡️ **`gray_mean` mesure surtout « combien de pierre il y a dans le cadre », pas « à quel point elle est humide ».**
C'est un confondant majeur, en plus de celui de l'éclairage. À corriger (voir §6).

*(Indicatif : n=11, mais le mécanisme physique est évident.)*

---

### 3.7 ✅ `test1.py` ameliore (fait)
Le masquage du tapis et la correction GLCM (§6.A et §6.B) **ont ete implementes**.

**Nouveau probleme decouvert et resolu au passage : le reflet du soleil.**
Un simple seuil d'Otsu classait la **large tache brillante du soleil sur le tapis mouille** comme de la pierre — **12.8 % de l'image** sur `frame_0008`.
- Ni la couleur ni la texture ne la separent : distributions trop recouvrantes
  (R−B median : reflet −9 / pierre +19, mais recouvrement massif)
- **Solution : top-hat blanc** (`image − ouverture`, noyau 41 px) avant Otsu.
  Par construction, supprime les zones claires **plus grandes** que le noyau (le reflet)
  et conserve les objets clairs **plus petits** (les cailloux)
- **Resultat : plus grosse composante 12.8 % → 1.3 %** de l'image ; 128–188 composantes detectees par image (= les cailloux). Verifie visuellement.

**Effet sur le confondant de couverture :**

| | corr(couverture, `gray_mean`) |
|---|---|
| Avant (image entiere) | **+0.727** |
| Apres (pierre seule + top-hat) | **−0.524** |

Le confondant d'intensite est donc **corrige**.

⚠️ **Mais un couplage subsiste sur les features de texture** : 12 des 24 features
(surtout GLCM contrast/homogeneity/correlation) correlent encore a |r| > 0.7 avec la couverture.
**Interpretation prudente : avec n = 11 issues d'une seule video de 20 s, on ne peut pas
distinguer un vrai couplage physique (couverture et granulometrie sont liees)
d'un artefact de petit echantillon.** A retrancher une fois plus de donnees disponibles.

---

## 4. Inventaire des fichiers

### ✅ À GARDER — code vivant

| Fichier | Rôle | État |
|---|---|---|
| `assets/clean_frames.py` | Filtre flou + doublons (le bon) | ✅ à jour — ⚠️ voir piège §3.2 |
| `clustering_humidite.py` | KMeans/DBSCAN + diagnostic de fuite | ✅ bon, garde-fou précieux |
| `test1.py` | Extraction de features (masque tapis + GLCM multi-échelle) | ✅ **amélioré** (§3.7) — 26 features |
| `assets/v1.mp4` | **La seule source de données valides** | ✅ **CRITIQUE — ne pas supprimer** |
| `my_env/` | Environnement Python (voir §7) | ✅ |
| `CV_Granulometry_Moisture_Roadmap.pdf` | Feuille de route du projet | 📄 référence |
| `DL_for_OreGranulometry.pdf` | Article deep learning granulométrie | 📄 référence |

### 🟡 À GARDER pour l'instant

| Fichier | Remarque |
|---|---|
| `assets/data/clean_v1/` (11 images) | **Le jeu de données actuel.** Régénérable depuis v1.mp4 |
| ~~`assets/data/scores_v1_dense.csv`~~ | ⚠️ **supprimé lors du nettoyage.** C'était le journal d'audit des 11 images — régénérable en relançant le filtrage (§5) |
| `assets/v2–v5.mp4` | Invalides pour l'entraînement, **mais utiles comme preuve** pour le signalement boue/produit au lavage |
| `visual.py` | Petit utilitaire histogrammes. ⚠️ 2 bugs mineurs : `plt.show()` hors de la boucle, et `xlabel`/`ylabel` inversés |

### ❌ À SUPPRIMER — obsolète

| Chemin | Pourquoi |
|---|---|
| `data/` (à la racine) | **Dossier vide**, créé par erreur quand `blurry.py` a tourné depuis le mauvais répertoire |
| `assets/data/raw/` (196 img) | Ancienne extraction 1 img/2 s des 5 vidéos — dont 4 invalides. Régénérable |
| `assets/data/clean/` (31 img) | 2 img de v1 + 6 de v2 + 23 de v3 → **29/31 proviennent de vidéos invalides** |
| `assets/data/scores.csv` | Audit de l'extraction obsolète ci-dessus |
| `assets/data/raw_v1_dense/` (102 img) | Intermédiaire — régénérable en 1 commande ffmpeg (§5) |
| `features.csv` | Calculé sur les 31 images (donc majoritairement données invalides) — **périmé** |
| `features_raw.csv` | Artefact du test §3.4 — conclusion déjà consignée ici |
| `resultats/*` (8 fichiers) | Tous issus du clustering sur données invalides — résultats consignés en §3.3 |
| `assets/contact_sheet.jpg` | Planche de contrôle visuel — régénérable |
| `.DS_Store` | Déchet macOS |

**Commande de nettoyage** (à relire avant de lancer) :
```bash
cd /Users/oussamahabiballah/ensa/STAGE_CV
rm -rf data                              # dossier vide à la racine
rm -rf assets/data/raw assets/data/clean assets/data/raw_v1_dense
rm -f  assets/data/scores.csv
rm -f  features.csv features_raw.csv
rm -rf resultats
rm -f  assets/contact_sheet.jpg
find . -name .DS_Store -delete
```
> ⚠️ Ne supprime **jamais** `assets/v1.mp4` ni `assets/data/clean_v1/`.
> Les v2–v5 sont à conserver tant que le signalement au lavage n'est pas fait.

---

## 5. Comment régénérer les 11 images v1 (reproductible)

```bash
cd /Users/oussamahabiballah/ensa/STAGE_CV

# 1. Extraction dense de v1 à 5 fps  -> 102 images candidates
mkdir -p assets/data/raw_v1_dense
ffmpeg -v error -i assets/v1.mp4 -vf fps=5 -qscale:v 2 \
       assets/data/raw_v1_dense/frame_%04d.jpg

# 2. Filtrage (paramètres utilisés : WINDOW=10, FLOOR_PERCENTILE=10, DEDUP_MAX_DIFF=4.0)
#    -> 11 images retenues
```
Images retenues : `frame_0008, 0011, 0021, 0039, 0045, 0057, 0065, 0079, 0084, 0092, 0102`
Statistiques de netteté : min 5 650 · médiane 7 989 · max 14 893 · plancher p10 = 6 455

> Aller au-delà de 5 fps est inutile : 15 fps donne exactement les mêmes 11 images.

---

## 6. Améliorer l'extraction de features — au-delà de `test1.py`

`test1.py` fonctionne, mais présente de vraies faiblesses. Par ordre d'impact :

### 🔴 A. Masquer le tapis (le plus important)
**Problème mesuré (§3.6) :** `gray_mean` corrèle à +0.73 avec la couverture de pierre. Les features mesurent la quantité de pierre, pas son humidité.

**Correction :** segmenter pierre / tapis (seuil d'Otsu suffit — le tapis est noir, la pierre claire), puis :
- calculer **toutes** les features **uniquement sur les pixels pierre**
- ajouter `stone_coverage_frac` comme feature **explicite et séparée** (c'est une vraie information granulométrique — un débit, pas un parasite déguisé)

### 🔴 B. GLCM mal paramétré
Actuellement : `DISTANCE=1`, `ANGLE=0`, `levels=256`.
- Une seule distance de 1 px et **un seul angle (horizontal)** → aveugle aux structures verticales/diagonales, et à toute texture plus grossière qu'un pixel
- `levels=256` → matrice 256×256 très creuse, lente et bruitée

**Correction standard :**
```python
distances = [1, 2, 4, 8]                          # multi-échelle
angles    = [0, np.pi/4, np.pi/2, 3*np.pi/4]      # 4 directions
# quantifier en 32 ou 64 niveaux avant graycomatrix
# puis MOYENNER sur les angles -> invariance à la rotation
```

### 🟠 C. Passer à la granulométrie par segmentation (vrai objectif métier)
Les features de texture globale sont un **proxy faible** de la granulométrie. Le vrai livrable industriel, c'est une **distribution de tailles de particules** (D50, D80…).

Approches, de la plus simple à la plus lourde :
1. **Watershed classique** (OpenCV) — segmentation des cailloux individuels, puis mesure d'aire / diamètre équivalent. Pas d'annotation nécessaire, marche bien si les cailloux se touchent peu (**c'est le cas sur v1** : couverture ~20 %, cailloux bien séparés)
2. **SAM (Segment Anything)** — segmentation zero-shot, aucun entraînement, très robuste
3. **Mask R-CNN** — nécessite des annotations manuelles (cf. `DL_for_OreGranulometry.pdf`)

➡️ **Vu la faible couverture (~20 %) et les cailloux bien séparés sur v1, le watershed est un excellent point de départ** et donne directement les métriques métier.

### 🟠 D. Embeddings de réseau pré-entraîné (alternative au handcrafted)
Au lieu de GLCM/LBP, extraire des embeddings d'un CNN pré-entraîné (ResNet, ou **DINOv2** qui est excellent en non-supervisé) et clusteriser dessus. Souvent bien plus robuste que les features manuelles — mais **moins interprétable**, ce qui compte pour un rapport de stage.

### 🟡 E. L'humidité a besoin d'une référence
L'humidité se voit par l'assombrissement et la réflexion spéculaire — donc **directement confondue avec l'éclairage**. Sans contrôle, impossible de séparer « pierre mouillée » de « nuage devant le soleil ».

**Corrections possibles :**
- placer une **mire de référence** (carton gris/blanc) dans le champ → normaliser la luminance de chaque image
- ou filmer sous **éclairage contrôlé / constant**
- ou obtenir des **mesures réelles d'humidité** au moment du tournage, pour valider les clusters contre une vérité terrain

---

## 7. Environnement technique

- **Python : 3.14.6** dans `my_env/` — ⚠️ toujours utiliser `./my_env/bin/python`, pas le `python` système
- Paquets : opencv-python 5.0.0.93 · numpy 2.5.1 · pandas 3.0.3 · scikit-learn 1.9.0 · scikit-image 0.26.0 · matplotlib 3.11.0
- `ffmpeg` / `ffprobe` disponibles dans `/usr/local/bin/`
- ❌ Pas de lecteur PDF installé (les 2 PDF n'ont pas pu être lus automatiquement)
- ❌ Le projet **n'est pas un dépôt git** → aucun historique, aucune sauvegarde. **Fortement recommandé : `git init`**

---

## 8. Plan d'action — que faire maintenant

### Priorité 1 — Filmer plus (débloque tout le reste)
Rien d'autre ne peut avancer sérieusement avec 11 images.

- [ ] **Stabiliser le téléphone** : le poser sur la rambarde / le carter du convoyeur, le scotcher ou le caler. Pas besoin d'un vrai trépied — le but est juste que le téléphone ne bouge **pas indépendamment** du tapis
- [ ] **Filmer plus longtemps** : ~20 s → 11 images, donc **~3 minutes de minerai propre ≈ 90–100 images exploitables** (ordre de grandeur, à confirmer)
- [ ] **Garder distance et angle constants** entre les prises → supprime le confondant « session » détecté en §3.3
- [ ] **Vérifier la validité pendant toute la durée** (pierre propre, pas de boue/produit) — pas seulement au démarrage
- [ ] Si possible : **mire de référence** dans le champ (§6.E)
- [ ] Si possible : **noter l'humidité réelle** au moment du tournage → vérité terrain

### Priorité 2 — Signalement process (indépendant de la CV)
- [ ] Remonter au **lavage** la présence de boue / produit constatée sur v2–v5
- [ ] Extraire des images horodatées de v2–v5 comme **preuve** à joindre au signalement

### Priorité 3 — Améliorer le code (faisable dès maintenant, sans nouvelles données)
- [x] ~~Ajouter le **masquage du tapis** + `stone_coverage_frac` (§6.A)~~ ✅ fait (§3.7)
- [x] ~~Corriger les **paramètres GLCM** (§6.B)~~ ✅ fait (§3.7)
- [ ] ⚠️ **Le masque est calibré sur v1** (`TOPHAT_KERNEL = 41`). Sur de nouvelles vidéos
      (distance/angle différents → cailloux plus gros ou plus petits en pixels),
      **revérifier visuellement le masque** et réajuster le noyau si besoin
- [ ] Prototyper la **granulométrie par watershed** sur les 11 images v1 (§6.C) — c'est le livrable métier
      (le masque pierre/tapis de `test1.py` en est déjà la première étape)
- [ ] Vider `MANUAL_REJECT` dans `clean_frames.py` avant toute nouvelle extraction (§3.2)
- [ ] `git init` + premier commit

### Priorité 4 — Quand les données seront là
- [ ] Relancer extraction → filtrage → features → clustering
- [ ] **Toujours vérifier le NMI cluster-vs-source** : si > 0.45, le résultat n'est pas de l'humidité
- [ ] Viser **au moins 10 échantillons par feature** (donc ≥ 130 images pour 13 features) avant de croire un clustering

---

## 9. Règles à ne pas oublier

1. **Le diagnostic de fuite de `clustering_humidite.py` n'est pas décoratif.** NMI > 0.45 = le résultat reflète les conditions de tournage, pas le minerai.
2. **Ne jamais entraîner sur données floues non filtrées** — le modèle apprendra à détecter le flou (η² = 0.805, §3.4).
3. **« Le plus net de la fenêtre » ne garantit pas « net »** — si toute la fenêtre est floue, il ressort quand même une image floue. D'où `MANUAL_REJECT` et le contrôle visuel.
4. **Toujours contrôler visuellement** (planche contact) avant de valider un jeu de données. C'est ce qui a permis de détecter le problème sur v5.
5. **Le flou de ces vidéos vient de la main, pas du convoyeur.** Un futur flou dû à la vitesse du tapis avec caméra fixe serait, lui, légitime et à conserver — mais il devra être **constant**.
