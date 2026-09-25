# Expérience Alice : du Machine Learning sur UNE seule voiture

> Objectif : **comprendre** le ML en voyant une différence de comportement.
> Alice (voiture n°0) change de conduite, les autres gardent la Règle. On compare.

## 0. Lancer (dans l'ordre)

```bash
.venv/bin/python -m pip install -r requirements.txt   # ajoute scikit-learn
.venv/bin/python tree_model.py      # 1. collecte + entraîne l'arbre (~25 s)
.venv/bin/python alice.py           # 2. entraîne le RL d'Alice + compare les 4 conduites (~30 s)
.venv/bin/python main.py            # 3. regarde Alice rouler (contour noir, « Alice* »)
```

Dans `main.py` : `ALICE = "rl"`, `"tree"` ou `None`.

---

## 1. Le vocabulaire (à savoir par cœur)

| Mot | Sens simple | Dans notre projet |
|---|---|---|
| **Modèle** | une « fonction » qui a appris à partir d'exemples | l'arbre, ou la table Q |
| **Feature** (X) | une information donnée au modèle | « la sortie tout droit est dangereuse ? » |
| **Label** (y) | la bonne réponse, connue pour les exemples | « collision : oui (1) / non (0) » |
| **Entraîner** | le modèle règle ses paramètres sur les exemples | `model.fit(X, y)` |
| **Prédire** | le modèle répond sur un cas nouveau | `model.predict_proba(X)` |
| **Jeu de test** | exemples cachés pendant l'entraînement, pour noter le modèle | 20 % des décisions |
| **Surapprentissage** | le modèle apprend par cœur, marche mal sur du neuf | on limite la profondeur à 4 |
| **Politique** | règle qui dit quoi faire dans chaque situation | `choose()` → (sortie, allure) |

## 2. Deux familles de ML

| | **Supervisé** (arbre) | **Par renforcement** (RL, Q-learning) |
|---|---|---|
| Analogie | apprendre avec un livre de corrigés | apprendre à faire du vélo en tombant |
| A besoin de | exemples + bonnes réponses | un environnement + des récompenses |
| Apprend | « cette action est-elle risquée **maintenant** ? » | « cette action rapporte quoi **au total**, futur compris ? » |
| Fichier | `tree_model.py` | `learning.py` (agent) + `alice.py` (entraînement Alice) |

---

## 3. Ce que « voit » Alice (les features)

À chaque node, avant de choisir, Alice regarde (fonction `get_state` de `learning.py`) :

| Feature | Valeurs | Sens |
|---|---|---|
| `descendre`, `tout_droit`, `monter` | 0 pas de sortie · 1 libre · 2 occupée (loin) · 3 **danger** | l'état de chaque sortie |
| `rapide` | 0 / 1 | Alice roule plus vite que la moyenne ? |
| `derriere` | 0 / 1 | quelqu'un arrive juste derrière elle ? |
| `direction` | 0 descendre · 1 tout droit · 2 monter | ce qu'elle **choisit** |
| `allure` | 0 lent · 1 normal · 2 rapide | ce qu'elle **choisit** |

Exemple de ligne dans `data/decisions.csv` :
```
descendre,tout_droit,monter,rapide,derriere,direction,allure,collision
1,3,0,1,0,1,2,1
```
→ « descendre libre, tout droit DANGER, pas de montée, je suis rapide, personne derrière ; j'ai pris **tout droit en rapide** → **collision** ». Logique.

---

## 4. Supervisé : l'arbre de décision (`tree_model.py`)

### Étape 1 : collecter
`RecorderPolicy` fait conduire tout le monde **au hasard** (pour voir toutes les situations) et note chaque décision :
- à la décision : on ouvre une ligne avec label 0 ;
- si une collision arrive avant la décision suivante : label → 1 ;
- à la décision suivante : la ligne est rangée.

150 circuits × 60 s → **~97 000 décisions**, dont **~14 % de collisions**.

### Étape 2 : entraîner
```python
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, stratify=y)
model = DecisionTreeClassifier(max_depth=4, class_weight="balanced")
model.fit(x_train, y_train)
```
- **`train_test_split`** : 80 % pour apprendre, 20 % cachés pour noter.
- **`max_depth=4`** : 4 questions max → l'arbre reste lisible (`docs/images/arbre.png`, `docs/arbre.txt`).
- **`class_weight="balanced"`** : voir piège n°1.

Un arbre, c'est une suite de questions. Extrait de `docs/arbre.txt` :
```
|--- derriere <= 0.50                  (personne derrière ?)
|   |--- tout_droit <= 1.50            (tout droit libre ou absent ?)
|   |   |--- monter <= 1.50
|   |   |   |--- descendre <= 1.50  -> class: 0   (tout est libre : OK)
```

### Étape 3 : utiliser (`TreePolicy`)
Pour chaque action possible (≤ 9), l'arbre donne une **probabilité de collision**. Alice prend l'action au plus petit `risque + petit malus si lent` (sinon elle roulerait lentement partout).

### Les résultats (lancer `tree_model.py` pour les voir)
| Mesure | Valeur | Lecture |
|---|---|---|
| Précision modèle « bête » (répond toujours « pas de collision ») | 85,5 % | le piège ! |
| Précision de l'arbre | 75,5 % | plus bas… |
| Collisions détectées (rappel) | 76,5 % | …mais il repère 3 collisions sur 4, le « bête » 0 |
| Précision sur l'entraînement | 75,8 % | ≈ test → **pas de surapprentissage** |

### ⚠️ Piège n°1 : la précision ment quand une classe est rare
86 % des décisions sont sans collision. Un modèle qui dit toujours « pas de collision » a 86 % de précision… et ne sert à rien. C'est pour ça qu'on regarde le **rappel** (part des collisions détectées) et qu'on met `class_weight="balanced"` (une erreur sur une collision coûte plus cher).

---

## 5. Renforcement : le Q-learning d'Alice (`alice.py`)

Pas d'exemples : Alice **essaie**, reçoit des **récompenses**, et retient.

| Événement | Récompense |
|---|---|
| collision | −10 |
| fin d'un cadre | +1 |
| chaque seconde de route | −0,1 (sinon rouler lentement serait gratuit) |

Elle tient une table `q[état][action]` = « combien ça rapporte ». Après chaque segment :
```
q = q + 0.1 × (récompense + 0.9 × meilleur q de la situation suivante − q)
         ↑ ALPHA : vitesse d'apprentissage      ↑ GAMMA : poids du futur
```
**Exploration** : au début Alice choisit au hasard (epsilon = 1), puis de moins en moins (epsilon → 0,05). Sans exploration, elle ne découvrirait jamais les bonnes actions.

3000 épisodes (~2 min). Seule Alice apprend, les 9 autres roulent à la Règle. Table → `q_alice.json` (lisible).

---

## 6. Les distances : un tronçon long prend plus de temps (Alice seule)

**Problème observé** : Alice choisissait presque toujours « rapide ». Normal : elle ne voyait pas la route. Tous les tronçons duraient pareil, qu'ils soient courts ou longs.

**Correction** (seulement pour Alice, les autres gardent les mêmes règles) :
- Vitesse de base générale, identique pour tous.
- Temps sur un tronçon = longueur / vitesse. Dans le code : `progress += speed × dt / length`.
- Longueur = longueur **réelle à l'écran** (`Circuit.get_length`) : l'extérieur de l'arc est plus long que l'intérieur, une diagonale plus longue qu'un tout droit. Entre 0,9 et 2,0 cases.
- Alice **voit** la longueur de chaque sortie : 3 features de plus (`long_descendre`, `long_tout_droit`, `long_monter`), valeurs 0 pas de sortie · 1 court (< 1,15) · 2 moyen (< 1,45) · 3 long.
  - RL : `AliceAgent` (état de 8 nombres au lieu de 5).
  - Arbre : 10 features au lieu de 7.

**Observabilité** : chaque voiture compte ses allures (`pace_counts`) et sa distance.
- À l'écran : sous le classement, l'allure actuelle d'Alice, la longueur du tronçon et la répartition lent / normal / rapide.
- Dans le terminal : `alice.py` affiche la répartition des allures pour chaque conduite.

## 7. La comparaison (30 circuits jamais vus)

![Comparaison](images/alice.png)

| Conduite d'Alice | Collisions d'Alice / min | Tours / 60 s | Collisions des autres / min | Allures lent / normal / rapide |
|---|---:|---:|---:|---|
| Hasard | 9,23 | 1,03 | 3,47 | 31 % / 34 % / 35 % |
| Règle | 6,57 | 1,20 | 3,14 | 0 % / 100 % / 0 % |
| Arbre (supervisé) | **2,53** | **2,27** | **2,73** | 0 % / 0 % / 100 % |
| RL (Q-learning, 3000 épisodes) | 2,77 | 1,97 | 2,76 | 2 % / 7 % / 91 % |

### Lecture
- **Le ML marche** : Arbre et RL ont environ 3× moins de collisions que la Règle et 3,5× moins que le Hasard.
- **Pourquoi la Règle fait moins bien qu'avant (6,57 au lieu de 2,13)** : Alice ralentit maintenant sur les longs tronçons, pas les autres. Avec la Règle, elle roule à allure normale et se fait **rattraper par derrière**. Les modèles l'ont compris : rouler vite = ne pas se faire percuter.
- **« Rapide » reste le choix principal, et c'est logique.** Dans ce monde, rouler vite ne coûte rien : pas de carburant, pas de risque de sortie de route. Et rester lente fait rattraper Alice. Le RL, lui, varie un peu (9 % lent ou normal) selon la situation.
- **L'observabilité a servi** : sans le compteur d'allures, on n'aurait pas vu que l'arbre roule à 100 % en rapide.

### ⚠️ Piège n°2 : un modèle optimise ce qu'on lui demande, pas ce qu'on imagine
Si « rapide » gagne toujours, ce n'est pas un bug du modèle, c'est la règle du jeu. Pour qu'Alice module sa vitesse, il faut que **rouler vite coûte quelque chose**. Pistes (exercices) :
- malus de vitesse dans la récompense (ex. −0,05 par tronçon en rapide = carburant) ;
- rapide plus dangereux : distance de contact (`MIN_GAP`) plus grande quand on roule vite ;
- limitation de vitesse sur les tronçons longs ou courbes.

### ⚠️ Piège n°3 : toujours comparer à conditions égales
Mêmes 30 circuits (seeds 0-29), jamais utilisés pour apprendre (entraînement sur seeds ≥ 10 000), même trafic autour d'Alice, et Alice roule aux vraies distances **dans toutes les conduites**. Sinon la différence pourrait venir du hasard, pas du modèle.

### Pourquoi l'arbre ne voit que l'instant présent
Il prédit « collision sur CE tronçon ? ». Le RL, avec GAMMA, compte aussi la suite. Ici l'arbre gagne de peu, parce que « rouler vite » est une bonne réponse à court terme comme à long terme.

## 8. Qui fait quoi dans le code

| Fichier | Rôle |
|---|---|
| `traffic.py` | `Traffic(..., special={0: conduite})` : Alice a sa conduite (`policy_of`) et roule aux vraies distances (`distance_aware`, `get_length`). Compte les allures (`pace_counts`) |
| `circuit.py` / `network.py` | `get_length(a, b)` : longueur réelle d'un tronçon |
| `learning.py` | `get_state` (features), `QAgent` (RL), inchangés |
| `tree_model.py` | collecte (`RecorderPolicy`), entraînement (`train`), conduite (`TreePolicy`) |
| `alice.py` | `AliceAgent` (voit les longueurs), RL d'Alice (`train_alice`), comparaison (`measure`), graphique |
| `display.py` / `main.py` | `ALICE = "rl"/"tree"/None`, Alice en contour noir, `Alice*` dans le classement |
| `test_alice.py` | 8 tests : conduite spéciale, exemples bien formés, arbre > hasard, RL apprend, mesure reproductible |

## 9. Questions d'oral probables
- *Différence supervisé / renforcement ?* → corrigés vs essais-récompenses (tableau §2).
- *Pourquoi une seule voiture ?* → pour isoler l'effet de la conduite (§7, piège 3).
- *Pourquoi l'arbre a 75 % et le modèle bête 86 % ?* → classe rare, regarder le rappel (§4, piège 1).
- *Pourquoi Alice roule surtout vite ?* → rouler vite ne coûte rien et évite de se faire rattraper. Le modèle optimise la règle du jeu (§7, piège 2).
- *Pourquoi ajouter la longueur dans l'état ?* → si le temps dépend de la longueur, Alice doit la voir pour décider (observabilité).
- *Surapprentissage ?* → précision entraînement ≈ test, profondeur limitée à 4.
