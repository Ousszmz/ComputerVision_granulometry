# Projet Vision par Ordinateur — Granulométrie & Humidité du Stérile
## Document de reprise global (handoff — zéro perte de contexte)

> **Comment utiliser ce fichier :** colle-le en entier au début d'une nouvelle
> conversation. Il contient TOUT : contexte projet, décisions stratégiques, état réel
> des données, constats techniques mesurés, scripts produits, pièges connus et plan
> d'action. Il remplace et fusionne les anciens `MAIN_HANDOFF.md` (cadre projet, 19/07)
> et `HANDOFF.md` (constats techniques, 22/07).

*Dernière mise à jour : 23 juillet 2026*

---

## 0. ⚡ L'essentiel en 30 secondes

- **Projet :** détecter l'**humidité** (cœur) et la **granulométrie** (optionnel) du
  stérile sur un convoyeur, par vision par ordinateur. Stage OCP, Laverie Béni Amir.
- **Approche :** non supervisée (clustering), validée par **jugements d'opérateur**
  (pas d'accès labo → pas de % d'humidité mesuré).
- **🔴 Changement de cadrage majeur (23/07) :** l'exploitation est **surtout en LIT
  DENSE** (minerai remplissant le tapis, comme v2-v5). Le régime **épars** de v1 est le
  **cas particulier**, pas la norme. Tout le pipeline doit cibler le lit dense en priorité.
- **🟢 Opportunité clé (23/07) :** l'ingénieur a confirmé une photo « 90% valide, 10% =
  humidité/boue ». Ce 10% n'est **pas un déchet à jeter — c'est le SIGNAL à détecter**,
  identifié par un expert. C'est le **premier ancrage de vérité terrain** du projet.
- **État données :** 5 vidéos + 1 photo. Seule v1 avait passé le filtrage (11 images
  éparses). Le vrai jeu utile reste à constituer sur le régime dense.
- **Blocage :** pas technique — **manque de données valides étiquetées**. Le code marche.
- **Prochaine action à plus fort levier :** faire **marquer par l'ingénieur les zones
  humides** sur quelques images denses → premières étiquettes → débloque la validation.

---

## 1. Contexte du projet

- **Qui :** étudiant en 1ʳᵉ année Génie Informatique, ENSA Khouribga (Maroc). Débutant
  en vision par ordinateur et machine learning.
- **Où :** stage à **OCP S.A.**, site **Laverie Béni Amir**, Khouribga.
- **Sujet :** « Utilisation de la computer vision pour analyser la granulométrie du
  stérile et détecter la présence excessive d'eau ou d'humidité. »
- **Convoyeur filmé :** convoyeur des refus et rejets. **Rapide, toujours en marche.**
- **Langue des livrables :** français.

---

## 2. Décisions stratégiques (cadre du projet)

1. **Cœur = HUMIDITÉ.** La granulométrie est un module **optionnel** (si le temps le permet).
2. **Approche NON SUPERVISÉE** : clustering (K-means / DBSCAN), puis interprétation des
   groupes. Aucune donnée labellisée au départ.
3. **Collecte terrain par l'étudiant**, caméra personnelle (smartphone).
4. **Ancrages = validation.** Le clustering seul ne dit jamais « ce groupe = humide » ;
   il faut des points de référence réels liés à des images précises pour donner un sens
   physique aux clusters. **Un cluster sans ancrage reste « groupe non interprété ».**
5. **Pas d'accès labo → ancrages QUALITATIFS.** Les points d'ancrage ne sont pas des %
   d'humidité mesurés, mais des **jugements visuels d'un opérateur/ingénieur** (sec /
   normal / humide), notés avec l'heure et la zone. Conséquence assumée : le système est
   un **classifieur relatif** (tendance dans le temps), pas un capteur de % absolu. À
   présenter dans le rapport comme un **choix méthodologique justifié**, pas une lacune.
   → *Le « 10% = humidité » de l'ingénieur (§4) EST un ancrage qualitatif de ce type.*
6. **Diversité > volume.** Une vidéo de 2-3 min ne vaut que **quelques échantillons
   réellement différents** (le matériau change peu sur la durée). La vraie diversité
   vient du **nombre de sorties distinctes** (jours, heures, météo, zones, débits).
7. **Pas de data augmentation pour le clustering.** Flip/rotation/luminosité artificiels
   écartés en Phase 4 : les features (intensité, HSV, texture) **sont** le signal
   d'humidité — une augmentation photométrique le fausse, une géométrique crée des
   quasi-doublons qui biaisent coude et silhouette. À reconsidérer seulement en Phase 5
   (supervisé), et uniquement en géométrique (flip, léger crop) — jamais photométrique.

---

## 3. 🔴 Les deux régimes visuels (recadrage du 23/07)

Le taux de remplissage du tapis **varie avec le débit**. Il y a donc DEUX régimes visuels
très différents, et l'exploitation est **surtout en régime dense** :

| | Régime ÉPARS (v1) | Régime DENSE (v2-v5, photo 23/07) — **la norme** |
|---|---|---|
| Matière | cailloux isolés (~15-20%) | lit **dense** remplissant le tapis |
| Cailloux | **séparés** (faciles à segmenter) | **collés** (segmentation difficile) |
| Tapis | sombre, mouillé, très visible | visible surtout sur les bords |
| Représentativité | **cas particulier** (bas débit) | **cas courant** |

**Conséquences capitales :**
- **On ne peut pas mélanger les deux régimes dans un même jeu de clustering** : les
  clusters sépareraient « dense » de « épars » (= le débit / les conditions de prise de
  vue), pas l'humidité. C'est exactement la fuite déjà mesurée (§5.3). **Un régime = un
  jeu cohérent**, ou un traitement qui gère explicitement le remplissage.
- **Le masquage actuel de `test1.py` ne marche que sur l'épars** (voir §7 et §9.B). Il
  faut une segmentation **adaptative au remplissage** pour le régime dense.
- **`stone_coverage_frac` (taux de remplissage) est une vraie variable d'exploitation**
  (le débit), pas un parasite — d'où son statut de feature explicite. Mais elle
  dominera tout clustering brut si le remplissage varie : à normaliser ou traiter comme
  axe séparé.

---

## 4. 🟢 La photo du 23/07 & la première vérité terrain

L'ingénieur a confirmé sur une photo de **lit dense** : **« 90% valide, 10% = humidité/boue »**.

**Reformulation cruciale :** ce n'est PAS « 90% à garder + 10% à jeter ». C'est une image
**quasi-sèche de référence, avec des zones humides identifiées par un expert**. Le 10%
humide **est le phénomène qu'on cherche à détecter** — donc du signal étiqueté, pas du bruit.

**Pourquoi c'est décisif :** depuis le début, le projet bute sur UN problème — impossible
de distinguer « pierre mouillée » de « ombre / éclairage / tapis qui transparaît » (le
clustering a toujours suivi les conditions de prise de vue, pas l'humidité, cf. §5.3).
Un avis d'expert « ici c'est humide, là c'est sec » est **exactement l'ancrage
qualitatif** prévu par la décision §2.5, et **la seule façon de valider** qu'une feature
détecte vraiment l'humidité.

**➡️ Action à plus fort levier du moment :** demander à l'ingénieur de **marquer/entourer
les zones humides** sur cette photo (et 2-3 autres) — même un cercle au feutre sur une
capture suffit. Ça crée le **premier jeu étiqueté** et débloque toute la validation.

**Limites de cette photo à garder en tête :**
- C'est **une photo fixe unique**, pas un jeu de données. Nette (photo) mais isolée.
- **Perspective oblique** (prise de la passerelle en biais) : les cailloux du haut sont
  plus loin → plus petits en pixels à taille physique égale. **Biais direct pour la
  granulométrie.** Corriger : angle plus perpendiculaire, et/ou objet de taille connue
  dans le champ pour calibrer px→mm.

---

## 5. Constats techniques mesurés (session du 22/07)

### 5.1 Les vidéos — validité
| Vidéo | Durée | Résolution | Statut | Raison |
|---|---|---|---|---|
| **v1.mp4** | 20.3 s | 848×478 @30fps | ✅ valide | Pierre propre, **mais éparse** (bas débit, peu représentatif) |
| v2.mp4 | 64.9 s | 848×478 @30fps | ❌ invalide | boue / produit *(mais bon régime : dense)* |
| v3.mp4 | 220.1 s | 848×478 @30fps | ❌ invalide | boue / produit *(bon régime : dense)* |
| v4.mp4 | 26.2 s | 848×478 @30fps | ❌ invalide | boue + **100% flou** (caméra bougée en continu) |
| v5.mp4 | 61.4 s | **478×850 (portrait !)** | ❌ invalide | boue + **100% flou** ; orientation différente |

⚠️ **v5 est en portrait**, contrairement aux autres — ne pas mélanger sans redimensionnement.

**Nuance importante (23/07) :** v2-v5 sont « invalides » à cause de la **boue** (qui est
justement le signal humidité !) et du **flou**, PAS parce qu'elles sont denses. Leur
densité est au contraire **représentative**. À réexploiter une fois le flou géré et les
zones humides étiquetées.

### 5.2 Cause du flou : caméra tenue à la main
L'utilisateur a confirmé filmer **à main levée, sans stabilité**. Preuve : dans la *même*
vidéo (v3), la netteté varie de ~1 000 à ~25 000 (**facteur 25×**). Un convoyeur à vitesse
constante + caméra fixe donnerait un flou **constant**. Cette variance = **tremblement de
main**, pas le convoyeur. Donc ce flou est un **artefact de captation**, à filtrer.
*(Un futur flou dû à la vitesse du tapis avec caméra fixe serait, lui, légitime et
constant — à conserver le cas échéant.)*

### 5.3 Le clustering a détecté une fuite (données de prise de vue, pas humidité)
`clustering_humidite.py` compare les clusters à la vidéo d'origine (ARI / NMI) :

| Jeu de features | NMI (cluster vs vidéo) | Verdict |
|---|---|---|
| `toutes` | **0.887** | 🔴 les clusters = les vidéos, pas l'humidité |
| `robuste` (texture seule) | **0.640** | 🟡 dépendance partielle |
| v3 seule (n=23) | — | K=4, mais DBSCAN classe 11/23 en bruit |

**Conclusion : le « signal humidité » n'était que les conditions de prise de vue.** D'où
l'importance des ancrages (§4).

### 5.4 Données brutes (non filtrées) : dominées par le flou
Test sur 196 images brutes : **η² = 0.805** (80.5% de la variance de netteté expliquée par
le cluster) ; `glcm_contrast` corrèle à **r = +0.88** avec la netteté. Raison physique : le
flou détruit les hautes fréquences que GLCM/LBP mesurent. **Entraîner sur données floues
non filtrées = apprendre à détecter le flou, pas l'humidité.**

### 5.5 v1 plafonne à ~11 images
Extraction dense de v1 : 5 fps → 102 images → **11 gardées**. Vérifié : 15 fps → 305
images → **exactement les mêmes 11**. Vrai plafond : 20 s ne contiennent que ~11 instants
indépendants. **Le facteur limitant est la durée de tournage, pas l'échantillonnage.**

### 5.6 `test1.py` amélioré + reflet du soleil résolu
Masquage du tapis + GLCM corrigée implémentés (§9). Problème découvert au passage : un
simple Otsu classait la **large tache de reflet du soleil sur tapis mouillé** comme pierre
(**12.8% de l'image** sur `frame_0008`). Ni couleur ni texture ne la séparent proprement.
**Solution : top-hat blanc** (noyau 41 px) avant Otsu → supprime les zones claires plus
grandes que le noyau (reflet) et garde les cailloux. **Résultat : 12.8% → 1.3%.**

Effet sur le confondant de couverture :

| | corr(couverture, `gray_mean`) |
|---|---|
| Avant (image entière) | **+0.727** |
| Après (pierre seule + top-hat) | **−0.524** |

⚠️ Couplage résiduel : 12/24 features corrèlent encore à |r|>0.7 avec la couverture. Avec
n=11 d'une seule vidéo, **impossible de distinguer** un vrai couplage physique (couverture
↔ granulométrie) d'un artefact de petit échantillon. À retrancher avec plus de données.

---

## 6. L'approche technique en une phrase

> Images terrain → **vecteur de features** par image (remplissage, intensité, HSV,
> texture GLCM/LBP, sur la pierre uniquement) → **clustering** (K-means / DBSCAN) →
> **interprétation** de chaque groupe en humidité *relative* via des **ancrages
> qualitatifs horodatés** (jugements d'opérateur/ingénieur) → **alerte** si excessif.

---

## 7. Inventaire des fichiers

### ✅ Code vivant
| Fichier | Rôle | État |
|---|---|---|
| `assets/clean_frames.py` | Filtre flou (Tenengrad) + doublons, journal d'audit | ✅ à jour — ⚠️ voir piège §8 |
| `test1.py` | Extraction 26 features (masque pierre/tapis, GLCM multi-échelle) | ✅ amélioré (§9) — ⚠️ **calibré épars** |
| `clustering_humidite.py` | KMeans/DBSCAN + diagnostic de fuite cluster-vs-source | ✅ bon, garde-fou précieux |
| `visual.py` | Histogrammes rapides. ⚠️ 2 bugs mineurs : `plt.show()` hors boucle, `xlabel`/`ylabel` inversés | 🟡 |

### 🟡 Données & vidéos
| Fichier | Remarque |
|---|---|
| `assets/v1.mp4` | Seule vidéo « valide » (mais éparse). ⚠️ **NON sauvegardée hors disque — à copier ailleurs** |
| `assets/v2–v5.mp4` | Denses = bon régime, mais boue+flou. Utiles comme **preuve** pour le signalement lavage, et réexploitables plus tard |
| `assets/data/clean_v1/` (11 img) | Jeu épars actuel. Régénérable depuis v1 (§10) |
| `assets/data/scores.csv` | ⚠️ obsolète (ancienne extraction 5 vidéos) — à ignorer/supprimer |
| `features.csv` | 26 features × 11 images (régime épars) |
| ~~`scores_v1_dense.csv`~~ | Supprimé au nettoyage — régénérable (§10) |

### ❌ Non versionné (`.gitignore`)
`my_env/` (949 Mo), toutes les `*.mp4` (84 Mo), les `*.pdf` (dont le roadmap **interne
OCP** — ne pas publier), `resultats/`, données intermédiaires, `.claude/`, `.DS_Store`.

> **Rappel dépôt GitHub :** https://github.com/Ousszmz/ComputerVision_granulometry —
> ⚠️ **PUBLIC** et contient des photos d'installation OCP. Envisager de le passer en privé
> (Settings → Danger Zone) et vérifier avec l'encadrant.

---

## 8. ⚠️ Piège connu dans `clean_frames.py`
- `MANUAL_REJECT = {...}` liste des noms d'images d'une **ancienne** extraction. Si tu
  ré-extrais avec une numérotation différente, **cette liste devient fausse et peut
  rejeter de bonnes images**. → **La vider avant toute nouvelle extraction**, la
  reconstituer après contrôle visuel.
- `SRC`/`DST` sont **relatifs** → lancer le script **depuis `assets/`**.

---

## 9. `test1.py` — features et améliorations restantes

**Fait (session 22/07) :** 26 features, calculées sur la **pierre uniquement** (masque
top-hat + Otsu), GLCM **multi-distance [1,2,4,8] × 4 angles** quantifiée 64 niveaux
(moyenne sur angles = invariance rotation), `stone_coverage_frac` explicite.

**À faire, par ordre d'impact :**

- **A. 🔴 Segmentation ADAPTATIVE aux deux régimes.** Le masque actuel (top-hat noyau 41)
  est calibré pour l'**épars** ; il **efface l'intérieur d'un lit dense**. Pour le régime
  dense (la norme), refaire la segmentation — idéalement classifier chaque pixel en
  **tapis / pierre / fines-humides** plutôt qu'un simple seuil. ⚠️ **Ne pas coder à
  l'aveugle : attendre 1-2 images étiquetées** (§4) pour pouvoir vérifier.
- **B. Recalibrer `TOPHAT_KERNEL`** selon distance/angle de prise de vue (les cailloux
  changent de taille en pixels). **Revérifier visuellement le masque** à chaque nouveau
  régime.
- **C. 🟠 Granulométrie par segmentation (vrai livrable métier).** Les features de texture
  globale sont un proxy faible. Le livrable, c'est une **distribution de tailles (D50,
  D80)**. Options : **watershed** (simple, sans annotation — marche bien sur l'épars ;
  sur le dense les grains se touchent, plus dur), **SAM** (zero-shot, robuste), **Mask
  R-CNN** (nécessite annotations). Le masque pierre/tapis en est déjà la 1ʳᵉ étape.
- **D. 🟠 Embeddings pré-entraînés (DINOv2)** comme alternative aux features manuelles —
  souvent plus robuste, mais moins interprétable (compte pour le rapport).
- **E. 🟡 Humidité ↔ éclairage.** L'humidité se voit par assombrissement + reflet
  spéculaire → confondue avec l'éclairage. **Mire de référence** (carton gris) dans le
  champ, ou éclairage constant, ou les ancrages de §4 pour valider.

---

## 10. Régénérer les 11 images v1 (reproductible)

```bash
cd /Users/oussamahabiballah/ensa/STAGE_CV
mkdir -p assets/data/raw_v1_dense
ffmpeg -v error -i assets/v1.mp4 -vf fps=5 -qscale:v 2 \
       assets/data/raw_v1_dense/frame_%04d.jpg
# puis filtrage : WINDOW=10, FLOOR_PERCENTILE=10, DEDUP_MAX_DIFF=4.0  -> 11 images
```
Images retenues : `frame_0008, 0011, 0021, 0039, 0045, 0057, 0065, 0079, 0084, 0092, 0102`.
Aller au-delà de 5 fps est inutile (15 fps → mêmes 11 images).

---

## 11. Feuille de route (Phases 0 → 7)

| Phase | Nom | Statut |
|---|---|---|
| 0 | Fondations & environnement Python | ✅ fait (§14) |
| 1 | Traitement d'image : couleur & texture | ✅ largement fait |
| 2 | **Collecte de données terrain** (CŒUR) | 🟡 en cours — recadrer sur le **lit dense** |
| 3 | **Extraction de features** (CŒUR) | ✅ v1 ; 🔴 à adapter au dense (§9.A) |
| 4 | **Clustering non supervisé & validation** (CŒUR) | 🟡 pipeline prêt ; bloqué sur données+ancrages |
| 5 | Semi-supervisé (RandomForest/SVM) | Plus tard (≥ 20-30 ancrages) |
| 6 | Granulométrie (watershed / SAM) | Optionnel (§9.C) |
| 7 | Intégration & dashboard Streamlit | À faire |

**Chemin principal = Phases 0→4 + Phase 7.**

**Architecture cible :** frames → filtre flou → ROI matériau + normalisation éclairage →
[moteur humidité : features → PCA → clustering] ← **validation par ancrages opérateur
horodatés** → interprétation (cluster ↔ ancrage → humidité relative + alerte) → stockage
SQLite + dashboard Streamlit (badge vert/orange/rouge, nuage PCA, historique, export CSV).
Granulométrie en branche optionnelle. **Un cluster sans ancrage = « non interprété ».**

---

## 12. Combien de données ?

| Scénario | Images terrain | Ancrages qualitatifs | Fiabilité |
|---|---|---|---|
| Prototype | 40 – 50 | 3 – 5 | Exploration |
| Solide | 100 – 150 | 5 – 10 | Interprétation crédible |
| Déployable | 200+ | 10+ | Confiance élevée |

- **Le ratio compte plus que le volume.** 100 images + 0 ancrage = rien de prouvé.
- **Piège vidéo :** des centaines de frames de quelques minutes du même tas ≠ autant
  d'images différentes. 50 images vraiment variées > 500 quasi-identiques.
- **Garde-fou chiffré :** viser **≥ 10 images par feature** avant de croire un clustering
  (donc ≥ 260 pour 26 features). `test1.py` l'affiche en avertissement.

---

## 13. Checklist terrain (mise à jour 23/07)

**Avant de partir :**
- [ ] Autorisation encadrant OCP (filmer avec appareil perso) confirmée.
- [ ] Smartphone chargé + stockage suffisant ; EPI (casque, gilet, chaussures).
- [ ] **Objet de taille connue** (mètre/règle) dans le champ → calibration px→mm.
- [ ] **Carte grise/blanche** de référence → normalisation d'éclairage (si possible).
- [ ] Carnet/notes : zone, heure, conditions de chaque prise.
- [ ] **Opérateur/ingénieur dispo pour un avis sec/normal/humide** à chaque prise, avec
      l'heure — c'est l'ancrage qualitatif (§4). **Idéalement : faire marquer les zones
      humides sur l'image.**

**Réglages caméra (contre le flou — cause n°1 de perte de données) :**
- [ ] **Stabiliser** : poser le téléphone sur la rambarde/le carter, le caler ou le
      scotcher. **Ne pas filmer à main levée** (cause confirmée du flou, §5.2).
- [ ] Mode pro → **shutter rapide** (1/500s+). Filmer en **60 fps** si possible.
- [ ] Chercher la **lumière la plus forte**.
- [ ] **Angle plus perpendiculaire** au tapis (réduit flou ET distorsion de perspective).
- [ ] **Filmer plus longtemps** : ~20 s → 11 images ; viser **~3 min de matière propre**
      ≈ 90-100 images exploitables (ordre de grandeur).
- [ ] Vérifier la validité (pierre propre / boue) **sur toute la durée**, pas juste au départ.
- [ ] Privilégier le **régime dense** (la norme d'exploitation), pas les moments à bas débit.

---

## 14. Environnement & stack

- **Python : 3.14.6** dans `my_env/` — ⚠️ toujours `./my_env/bin/python`, jamais le
  `python` système.
- Paquets : opencv-python 5.0.0.93 · numpy 2.5.1 · pandas 3.0.3 · scikit-learn 1.9.0 ·
  scikit-image 0.26.0 · matplotlib 3.11.0.
- `ffmpeg` / `ffprobe` dans `/usr/local/bin/`.
- Prévu plus tard (Phase 7) : Streamlit + SQLite. **Pas de GPU nécessaire.**
- ❌ Pas de lecteur PDF installé (les 2 PDF de référence n'ont pas pu être lus auto).
- ✅ Dépôt git initialisé et poussé (voir §7).

---

## 15. Règles à ne jamais oublier

1. **Le diagnostic de fuite de `clustering_humidite.py` n'est pas décoratif.** NMI > 0.45
   = le résultat reflète les conditions de tournage (vidéo, régime, éclairage), pas le
   minerai.
2. **Ne jamais mélanger régime dense et épars** dans un même jeu de clustering (§3).
3. **Ne jamais entraîner sur données floues non filtrées** (η²=0.805, §5.4).
4. **« Le plus net de la fenêtre » ≠ « net »** : si toute la fenêtre est floue, il ressort
   quand même une image floue. D'où `MANUAL_REJECT` + contrôle visuel.
5. **Toujours contrôler visuellement** (planche contact, overlay du masque) avant de
   valider un jeu de données ou un masque — c'est ce qui a révélé le reflet du soleil.
6. **Un cluster sans ancrage = « non interprété »** — jamais « sec »/« humide » par défaut.
7. **Le 10% humide n'est pas un déchet, c'est le signal** (§4).

---

## 16. Plan d'action

### Priorité 1 — Vérité terrain (débloque tout)
- [ ] Faire **marquer par l'ingénieur les zones humides** sur la photo dense du 23/07 (+
      2-3 autres) → premières étiquettes (§4).
- [ ] Consigner chaque avis avec **heure + zone** (`ancrages.csv`).

### Priorité 2 — Collecte recadrée sur le lit dense
- [ ] Refilmer le **régime dense** (la norme), **caméra stabilisée**, angle
      perpendiculaire, objet de taille connue, ~3 min de matière propre (§13).
- [ ] Garder distance/angle constants entre sorties (supprime le confondant « session »).

### Priorité 3 — Code (faisable maintenant)
- [ ] Adapter la **segmentation au régime dense** (§9.A) — **après** avoir 1-2 images
      étiquetées, pas avant.
- [ ] Prototyper la **granulométrie (watershed/SAM)** (§9.C).
- [ ] Vider `MANUAL_REJECT` avant toute nouvelle extraction (§8).

### Priorité 4 — Signalement process (indépendant de la CV)
- [ ] Remonter au **lavage** la boue/produit constatée sur v2-v5.
- [ ] Extraire des images horodatées de v2-v5 comme **preuve**.

### Priorité 5 — Sauvegarde
- [ ] **Copier `v1.mp4` (et les futures vidéos valides) hors du disque** (externe/Drive).

### Quand les données seront là
- [ ] Extraction → filtrage → features → clustering, **par régime**.
- [ ] Toujours vérifier le **NMI cluster-vs-source** ; superposer les **ancrages**.
- [ ] Viser **≥ 10 images/feature** avant de croire un résultat (§12).

---

## 17. Questions ouvertes

- Y a-t-il un **opérateur/ingénieur fiable et disponible** pour donner des avis visuels
  cohérents sur plusieurs sorties ? *(Un avis déjà obtenu le 23/07 — cf. §4.)*
- Filmer avec un appareil perso est-il bien **autorisé** sur site ?
- Livrable exact attendu par la laverie : alerte binaire (OK / trop humide) ? multi-classe
  (sec / normal / trop humide) ? tendance relative dans le temps ?
- Existe-t-il déjà une **caméra ou un éclairage fixe** sur zone, ou tout part de zéro ?
  *(Impact fort : une caméra fixe supprimerait le flou de main et fixerait la perspective.)*
- Si un **accès labo** devient possible, comment reconvertir les ancrages qualitatifs en
  points de calibration quantitatifs ?

---

## 18. Glossaire

- **Non supervisé :** découvrir des groupes sans étiquette. · **Clustering :** regrouper
  des observations similaires. · **K-means :** K centroïdes, assignation au plus proche,
  itéré. · **Centroïde :** moyenne d'un cluster. · **Inertie :** somme des distances² au
  centroïde (base du coude). · **Méthode du coude :** repérer le K au-delà duquel ajouter
  un cluster n'apporte plus grand-chose. · **Silhouette :** qualité d'assignation (−1 à 1).
- **DBSCAN :** clustering par densité, sans K fixé, détecte les aberrants. ·
  **StandardScaler :** remet les features à la même échelle (sinon l'intensité 0-255
  écrase la GLCM 0-1). · **PCA :** réduction de dimension pour visualiser en 2D.
- **GLCM :** matrice de co-occurrence des niveaux de gris → contraste, homogénéité,
  énergie, corrélation. · **LBP :** motif binaire local (texture). · **ROI :** portion de
  l'image contenant le matériau. · **Top-hat :** `image − ouverture`, isole les objets
  clairs plus petits que le noyau (utilisé pour retirer le reflet du soleil).
- **Variance du Laplacien / Tenengrad :** mesures de netteté (filtrage du flou). ·
  **η² (eta²) :** part de variance d'une grandeur expliquée par l'appartenance au cluster.
  · **NMI / ARI :** mesures d'accord entre deux partitions (ici : clusters vs source, pour
  détecter la fuite).
- **Point d'ancrage :** image liée à une référence connue, pour interpréter les clusters.
  · **Ancrage qualitatif :** ancrage basé sur un jugement humain (sec/normal/humide),
  faute de labo. · **Vérité terrain :** la référence qui valide un résultat.
- **Watershed :** segmentation qui sépare les grains qui se touchent. · **SAM :** Segment
  Anything Model (segmentation zero-shot). · **DINOv2 :** réseau pré-entraîné pour
  embeddings non supervisés. · **PSD / D50 / D80 :** distribution de tailles ; taille sous
  laquelle se trouvent 50% / 80% du matériau.

---

*Fin du document de reprise global. Colle-le en entier au début d'une nouvelle session.*
