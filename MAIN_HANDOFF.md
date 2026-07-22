# Projet Vision par Ordinateur — Détection d'Humidité du Stérile
## Document de reprise de session (handoff — zéro perte de contexte) — v2

> **Comment utiliser ce fichier :** colle l'intégralité de son contenu au début d'une
> nouvelle conversation. Il contient tout le contexte du projet, les décisions prises,
> l'état d'avancement réel (données déjà collectées, bug résolu, scripts déjà écrits)
> et les prochaines étapes, pour reprendre exactement là où on s'est arrêté.
>
> **Différence avec la v1 :** la collecte terrain a démarré (3 vidéos tournées) et un
> changement de stratégie important a eu lieu — **pas d'accès labo**, donc les points
> d'ancrage deviennent des jugements visuels d'opérateur plutôt que des mesures
> d'humidité en %.

*Dernière mise à jour : 19 juillet 2026*

---

## 1. Contexte du projet

- **Qui :** étudiant en 1ʳᵉ année Génie Informatique, ENSA Khouribga (Maroc).
- **Où :** stage à **OCP S.A.**, site **Laverie Béni Amir**, Khouribga.
- **Sujet initial :** « Utilisation de la computer vision pour analyser la
  granulométrie du stérile et détecter la présence excessive d'eau ou d'humidité. »
- **Niveau :** débutant en vision par ordinateur et en machine learning.
- **Langue de travail des livrables :** français.

---

## 2. Décisions clés déjà prises

1. **Recentrage sur l'HUMIDITÉ.** La granulométrie reste un module **optionnel**
   (activé seulement si le temps le permet).
2. **Approche NON SUPERVISÉE.** Aucune donnée labellisée au départ → **clustering**
   (K-means / DBSCAN), puis interprétation des groupes obtenus.
3. **Collecte des données SUR LE TERRAIN, par l'étudiant lui-même**, avec caméra
   personnelle, sur le **convoyeur des refus et rejets**.
4. **Points d'ancrage = validation.** Le clustering seul ne dit jamais « ce groupe =
   humide » ; il faut des points de référence réels associés à des images précises
   pour donner un sens physique aux clusters.
5. **🆕 Pas d'accès labo → ancrages qualitatifs.** Aucun accès à l'étuve / au labo
   n'est possible pour ce stage. Les points d'ancrage ne seront donc **pas** des
   pourcentages d'humidité mesurés, mais des **jugements visuels d'un opérateur
   expérimenté** (sec / normal / humide) notés avec l'heure et la zone au moment de la
   prise de vue. Conséquence assumée : le système sera un **classifieur relatif**
   (comparaison / tendance dans le temps), pas un capteur de pourcentage absolu. À
   présenter dans le rapport comme un choix méthodologique justifié par la contrainte
   terrain, pas comme une lacune.
6. **🆕 Vidéo ET photos, la diversité prime sur le volume.** La vidéo reste pratique
   pour capturer un convoyeur en mouvement, mais **une vidéo de 2-3 min ne compte que
   pour quelques échantillons réellement différents** (le matériau change peu sur
   cette durée). La vraie diversité vient du nombre de **sorties terrain distinctes**
   (jours, heures, météo, zones), pas du nombre de frames extraites d'une même vidéo.
7. **🆕 Pas de data augmentation pour le clustering.** Décision explicite d'écarter
   flip / rotation / luminosité / contraste artificiels pour la Phase 4. Raison : les
   features utilisées (intensité, HSV, texture GLCM) **sont** le signal d'humidité —
   une augmentation photométrique le fausse directement, et une augmentation
   géométrique ne crée que des quasi-doublons qui biaisent la méthode du coude et le
   score de silhouette. À reconsidérer seulement en **Phase 5** (Random Forest / SVM
   supervisé), et uniquement avec des transformations géométriques (flip, léger crop)
   — jamais photométriques.

---

## 3. État actuel

- ✅ Sujet clarifié et recadré sur l'humidité.
- ✅ Stratégie technique définie (non supervisé + validation par ancrages qualitatifs).
- ✅ Deux feuilles de route DOCX déjà produites :
  - `CV_Granulometry_Moisture_Roadmap.docx` — v1, généraliste, désormais secondaire.
  - `Roadmap_Humidite_Non_Supervise.docx` — v2, référence technique détaillée
    (⚠️ ses mentions de « prélèvement labo » sont remplacées par la décision n°5
    ci-dessus).
- ✅ **3 vidéos terrain déjà tournées** (2-3 minutes chacune, convoyeur des rejets).
- ✅ Bug d'extraction ffmpeg identifié et corrigé : le dossier `data/raw/` n'existait
  pas encore, et le nom de fichier réel ne correspondait pas au `video.mp4` d'exemple
  (script corrigé en section 9).
- ✅ Script anti-flou (variance du Laplacien) écrit et prêt à l'emploi (section 9) —
  nécessaire car le convoyeur est rapide et les vidéos captées sont un peu floues.
- ⏳ Extraction + nettoyage des frames des 3 vidéos existantes : à lancer.
- ⏳ **2 sorties terrain prévues (demain + après-demain)** pour compléter la collecte,
  avec réglages caméra améliorés contre le flou (section 8).
- ⏳ Setup de l'environnement Python : probablement fait, à confirmer avec le script
  de test (section 9c).
- ⏳ Aucune feature extraite pour l'instant, Phase 3 pas commencée.
- ⏳ Aucun jugement d'opérateur (ancrage qualitatif) collecté pour l'instant.

---

## 4. L'approche technique en une phrase

> Prendre des images terrain → extraire un **vecteur de features** par image
> (intensité, couleur HSV, texture GLCM) → **regrouper** ces vecteurs par clustering
> (K-means / DBSCAN) → **interpréter** chaque groupe en niveau d'humidité *relatif*
> grâce à des **jugements visuels d'opérateurs horodatés** (ancrages qualitatifs,
> faute d'accès labo) → **alerter** si le groupe correspond à un niveau jugé excessif.

---

## 5. Feuille de route (Phases 0 → 7)

| Phase | Nom | Durée | Statut |
|---|---|---|---|
| 0 | Fondations & environnement Python | 2–3 j | À confirmer |
| 1 | Traitement d'image : couleur & texture | ≈ 1 sem | À faire |
| 2 | **Collecte de données terrain** (CŒUR) | continu | 🟡 En cours (3 vidéos tournées, 2 sorties à venir) |
| 3 | **Extraction de features d'humidité** (CŒUR) | 1–2 sem | À faire |
| 4 | **Clustering non supervisé & validation** (CŒUR, ancrages qualitatifs) | 1–2 sem | À faire |
| 5 | Évolution vers le semi-supervisé | optionnel | Plus tard |
| 6 | Granulométrie (watershed) | optionnel | Plus tard |
| 7 | Intégration & dashboard Streamlit | 1–2 sem | À faire |

**Chemin principal = Phases 0 → 4 + Phase 7.** Les phases 5 et 6 sont des extensions.

### Détail rapide de chaque phase

- **Phase 0 :** comprendre qu'une image est une matrice de nombres ; installer Python
  + OpenCV + scikit-image + scikit-learn ; manipuler niveaux de gris, HSV, histogrammes.
- **Phase 1 :** filtrage du bruit (médian/gaussien), seuillage (Otsu/adaptatif) pour
  isoler la zone de matériau (ROI), bases de morphologie, intuition de la texture.
- **Phase 2 :** filmer/photographier le convoyeur sur plusieurs sorties variées ;
  extraire les frames ; filtrer le flou ; recueillir des **jugements opérateur
  horodatés** (remplace les prélèvements labo) ; organiser `data/raw/`, `data/clean/`
  + `ancrages.csv`.
- **Phase 3 :** fonction `extraire_features(image)` → intensité (moyenne/médiane), HSV
  (Valeur, Saturation), texture GLCM (contraste, homogénéité, énergie, corrélation).
  Sortie : `features.csv` (une ligne par image, ~8-15 valeurs).
- **Phase 4 :** standardiser (StandardScaler) → choisir K (méthode du coude + score de
  silhouette) → K-means puis DBSCAN → PCA pour visualiser en 2D → **superposer les
  ancrages qualitatifs (jugements opérateur)** pour interpréter les clusters.
- **Phase 5 :** quand ≥ 20-30 ancrages, entraîner un Random Forest / SVM léger
  (évaluer avec validation croisée + matrice de confusion). Augmentation géométrique
  uniquement autorisée ici.
- **Phase 6 :** watershed pour séparer les grains, calibration px→mm (objet de taille
  connue), courbe granulométrique (PSD, D50/D80). Ne nécessite aucun entraînement.
- **Phase 7 :** pipeline unique piloté par config ; mode batch ; dashboard Streamlit
  (badge humidité vert/orange/rouge, nuage PCA, historique, export CSV) ; stockage SQLite.

---

## 6. Architecture du système cible

```
[Caméra perso : vidéo + photos, convoyeur des rejets]
            │
            ▼
[Extraction de frames : 1 frame / 1–2 s + filtre anti-flou (variance Laplacien)]
            │
            ▼
[Prétraitement : extraction ROI matériau + normalisation éclairage]
            │
            ├──────────────────────────────┐
            ▼                               ▼
[MOTEUR HUMIDITÉ — non supervisé]   [Granulométrie — OPTIONNEL, en pointillés]
  1. Features (intensité, HSV, GLCM)   (watershed, sans entraînement)
  2. Standardisation + PCA
  3. Clustering K-means / DBSCAN
            │
            │◄─── [VALIDATION TERRAIN : jugements opérateur horodatés
            │      (sec/normal/humide) = ancrages qualitatifs, pas de labo]
            ▼
[INTERPRÉTATION & DÉCISION :
  clusters ↔ ancrages → niveau d'humidité relatif + confiance
  comparaison aux seuils → alerte opérateur]
            │
            ├───────────────────────┐
            ▼                       ▼
[Stockage SQLite/MySQL]     [Dashboard Streamlit :
  historique + réf images     badge, tendance, alertes, export CSV]
```

**Principe de conception le plus important :** un cluster **sans** ancrage reste
étiqueté « groupe non interprété » — jamais « sec » ou « humide » par défaut.
Traçabilité totale : chaque résultat garde un lien vers son image source.

---

## 7. Combien de données faut-il ?

| Scénario | Images terrain | Ancrages qualitatifs (jugements opérateur) | Fiabilité |
|---|---|---|---|
| Prototype rapide | 40 – 50 | 3 – 5 | Exploration |
| Système solide | 100 – 150 | 5 – 10 | Interprétation crédible |
| Robuste / déployable | 200+ | 10+ | Confiance élevée |

**Règles importantes :**
- Le **ratio** compte plus que le volume. 100 images + 0 ancrage = rien de prouvé.
- **Piège vidéo :** des centaines de frames extraites de quelques minutes de vidéo du
  même tas ≠ autant d'images différentes. Mieux vaut **50 images vraiment variées**
  (zones, moments, niveaux d'humidité perçus) que 500 quasi-identiques.
- Sans labo, chaque ancrage qualitatif vaut cher : à collecter avec soin (heure
  précise, zone précise, avis d'un opérateur qui connaît bien le matériau).

---

## 8. Checklist terrain (mise à jour)

**Avant de partir :**
- [ ] Autorisation confirmée auprès de l'encadrant OCP (filmer/photographier avec
      appareil perso).
- [ ] Caméra/smartphone chargé + espace de stockage suffisant.
- [ ] EPI requis (casque, gilet, chaussures de sécurité).
- [ ] Objet de taille connue (mètre) pour la référence d'échelle.
- [ ] Carte grise/blanche pour la normalisation d'éclairage (si possible).
- [ ] Carnet / notes téléphone : zone, heure, conditions de chaque prise.
- [ ] 🆕 Repérer un opérateur disponible pour donner un avis rapide (sec / normal /
      humide) à chaque prise, avec l'heure notée — **remplace le prélèvement labo**.
- [ ] Sac/contenant propre si un échantillon physique doit être gardé pour référence
      visuelle plus tard.

**🆕 Réglages caméra contre le flou (convoyeur rapide) :**
- [ ] Mode manuel/pro si disponible, forcer un **shutter rapide** (1/500s ou plus).
- [ ] Filmer en **60 fps** si l'option existe (force souvent un shutter plus rapide).
- [ ] Chercher la lumière la plus forte possible.
- [ ] Stabiliser la caméra (appui sur un support, pas juste à main levée).
- [ ] Privilégier un angle où le matériau ne traverse pas le cadre perpendiculairement
      à son mouvement (réduit le flou apparent).

---

## 9. Scripts déjà produits (à copier tel quel)

**a) Extraction de frames (corrigée)**
```bash
mkdir -p data/raw
ffmpeg -i "NOM_EXACT_DE_LA_VIDEO.mp4" -vf fps=1/2 data/raw/frame_%04d.jpg
```
Pour les 3 vidéos, préfixer pour éviter l'écrasement mutuel :
```bash
ffmpeg -i video1.mp4 -vf fps=1/2 data/raw/v1_%04d.jpg
ffmpeg -i video2.mp4 -vf fps=1/2 data/raw/v2_%04d.jpg
ffmpeg -i video3.mp4 -vf fps=1/2 data/raw/v3_%04d.jpg
```
💡 Toujours vérifier le nom exact avec `ls` avant de lancer la commande, et mettre le
nom entre guillemets s'il contient des espaces.

**b) Filtre anti-flou (variance du Laplacien)**
```python
import cv2, os, shutil

src, keep = "data/raw", "data/clean"
os.makedirs(keep, exist_ok=True)

for f in sorted(os.listdir(src)):
    img = cv2.imread(os.path.join(src, f), cv2.IMREAD_GRAYSCALE)
    score = cv2.Laplacian(img, cv2.CV_64F).var()
    if score > 100:   # seuil à ajuster après avoir regardé les scores
        shutil.copy(os.path.join(src, f), os.path.join(keep, f))
    print(f, round(score, 1))
```
Le script imprime le score de chaque image. Regarder à l'œil quelles valeurs
correspondent à des images nettes vs floues, puis ajuster le seuil `100` en conséquence.

**c) Test de l'environnement Python (Phase 0)**
```python
import cv2, skimage, sklearn, numpy, pandas, matplotlib
print(cv2.__version__, skimage.__version__, sklearn.__version__)
```
Si ça affiche des versions sans erreur → l'environnement est prêt. Sinon :
```bash
pip install opencv-python scikit-image scikit-learn numpy pandas matplotlib jupyter streamlit
```

---

## 10. Stack technique

- **Langage :** Python 3.10+
- **Vision / image :** OpenCV, scikit-image
- **Machine learning :** scikit-learn (K-means, DBSCAN, PCA, StandardScaler, plus tard
  RandomForest/SVM)
- **Calcul / données :** NumPy, pandas
- **Visualisation :** matplotlib
- **Extraction frames :** ffmpeg
- **Dashboard :** Streamlit
- **Stockage :** SQLite (MySQL plus tard)
- **Pas de GPU nécessaire** pour cette approche (features + clustering classiques).

---

## 11. Calendrier suggéré (8 semaines)

| Sem | Focus | Livrable | Statut |
|---|---|---|---|
| 1 | Phase 0 + 1 ; sorties terrain n° 1-3 | Env prêt ; 3 vidéos tournées, frames en cours d'extraction | 🟡 En cours |
| 2 | Suite collecte (nouvelles sorties) ; extraction frames | ≥ 50 images propres ; `ancrages.csv` (jugements opérateur) en cours | À faire |
| 3 | Phase 3 — features sur tout le dataset | `features.csv` complet | À faire |
| 4 | Phase 4 — clustering, choix de K | Notebook clustering + PCA | À faire |
| 5 | Phase 4 — validation via ancrages qualitatifs | Interprétation des clusters documentée | À faire |
| 6 | Compléter collecte + validation | ≥ 8-10 ancrages qualitatifs | À faire |
| 7 | Phase 7 — intégration + Streamlit | Système bout en bout | À faire |
| 8 | Buffer (Phase 5/6) + rédaction rapport | Rapport final + démo OCP | À faire |

---

## 12. Glossaire des concepts

- **Apprentissage non supervisé :** découvrir des groupes dans des données sans étiquette.
- **Clustering :** regrouper des observations similaires (K-means, DBSCAN).
- **K-means :** place K centroïdes et assigne chaque point au plus proche, en itérant.
- **Centroïde :** point central (moyenne) d'un cluster.
- **Inertie :** somme des distances² au centroïde ; base de la méthode du coude.
- **Méthode du coude :** sur un graphe inertie vs K, repérer où ajouter un cluster
  n'apporte plus grand-chose.
- **Score de silhouette :** qualité d'assignation d'un point à son cluster (−1 à 1).
- **DBSCAN :** clustering par densité ; pas besoin de fixer K ; détecte les aberrants.
- **Standardisation (StandardScaler) :** remettre les features à la même échelle avant
  clustering (sinon l'intensité 0–255 écrase les features GLCM 0–1).
- **PCA :** réduction de dimension pour visualiser en 2D.
- **Point d'ancrage :** image associée à une référence connue, servant à interpréter
  les clusters.
- **🆕 Ancrage qualitatif :** point d'ancrage basé sur un jugement humain (sec/normal/
  humide) plutôt que sur une mesure physique — utilisé ici faute d'accès labo.
- **GLCM :** matrice de co-occurrence des niveaux de gris → features de texture
  (contraste, homogénéité, énergie, corrélation).
- **ROI :** Region Of Interest, la portion de l'image contenant le matériau.
- **Variance du Laplacien :** mesure de netteté d'une image (plus la valeur est basse,
  plus l'image est floue) ; utilisée ici pour filtrer les frames floues.
- **Ground truth / vérité terrain :** la référence servant à valider un résultat (ici,
  un jugement opérateur, pas une mesure labo).
- **Semi-supervisé :** combine peu de données étiquetées + beaucoup de non étiquetées.
- **Watershed :** algo de segmentation qui sépare les grains qui se touchent (module
  granulométrie optionnel).
- **PSD / D50 / D80 :** distribution de taille des particules ; taille sous laquelle
  se trouvent 50 % / 80 % du matériau.

---

## 13. Prochaines étapes immédiates

1. Corriger et lancer l'extraction de frames sur les 3 vidéos déjà tournées (script
   9a — `mkdir -p data/raw` d'abord, puis vérifier le nom exact du fichier).
2. Lancer le filtre anti-flou (script 9b), regarder les scores, ajuster le seuil, voir
   combien d'images exploitables restent.
3. Confirmer l'environnement Python avec le script de test (9c).
4. Sorties terrain demain + après-demain : appliquer les réglages anti-flou
   (section 8), viser des zones/moments variés, collecter des jugements d'opérateur
   horodatés.
5. Une fois ≥ 50 images propres et variées + quelques jugements d'opérateur récoltés
   → passer à la Phase 3 (extraction de features).

---

## 14. Questions ouvertes / à confirmer

- ~~Le labo peut-il fournir 5-10 mesures d'humidité ?~~ → **Non, confirmé : pas
  d'accès labo.** Question restante : y a-t-il un opérateur disponible et fiable pour
  donner des avis visuels cohérents sur plusieurs sorties ?
- Filmer/photographier avec un appareil personnel est-il bien autorisé sur site ?
- Quel est le livrable exact attendu par la laverie : alerte binaire (OK / trop
  humide) ? multi-classe (sec / normal / trop humide) ? tendance relative dans le temps ?
- Existe-t-il déjà une caméra ou un éclairage fixe sur zone, ou tout part de zéro ?
- Si un accès labo devient possible plus tard dans le stage, comment reconvertir les
  ancrages qualitatifs déjà collectés en points de calibration quantitatifs ?

---

*Fin du document de reprise (v2). Colle-le en entier au début d'une nouvelle session
pour repartir sans perte de contexte : contexte projet, décisions (y compris le
changement de stratégie sans labo), état réel des données et scripts déjà écrits, et
prochaines étapes.*