# RoadNetwork

Générateur procédural de réseau routier sur une grille, avec animation de routes et circulation de véhicules.
Projet du Bootcamp Python B3 – Sup de Vinci 2026-2027.

![Réseau généré](docs/images/reseau.png)

## Installation

Prérequis : Python 3.14.

```bash
# macOS / Linux
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt

# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Lancement

```bash
./.venv/bin/python main.py          # macOS / Linux
.\.venv\Scripts\python.exe main.py  # Windows
```

La fenêtre propose des curseurs pour régler le nombre de routes, le nombre d'intersections visé et le nombre de véhicules. Clique **Randomize** pour changer de réseau. Les boutons **Conduite** (en bas à droite) choisissent comment roulent les véhicules : **Hasard** (sortie et allure au hasard), **Règle** (à chaque intersection, une autre sortie que le dernier véhicule passé dans les 2 secondes) ou **Appris** (la conduite apprise par Q-learning, voir `train.py`).

Pour réentraîner la conduite apprise (environ 30 s, sans fenêtre ; écrit `q_table.json` et `docs/images/apprentissage.png`) :

```bash
./.venv/bin/python train.py         # 3000 épisodes ; train.py 500 pour un essai court
./.venv/bin/python evaluate.py      # compare hasard / règle / appris (~1 s)
```

La seed apparaît dans le titre et le terminal. Pour rejouer un réseau, mettre `SEED = 4821` dans `main.py`.

Les intersections sont un nombre **visé** : si la combinaison taille de grille / nombre de routes ne permet pas le nombre demandé, le titre indique le nombre obtenu et le nombre demandé. La génération cherche le meilleur réseau après un nombre limité d'essais.

## Réglages par défaut (`main.py`)

| Constante | Valeur | Rôle |
|---|---:|---|
| `COLUMNS`, `ROWS` | 15, 9 | taille de la grille |
| `SEED` | `None` | au hasard ; un entier rejoue le même réseau |
| `ROADS` | 4 | nombre de chemins (principal inclus) |
| `INTERSECTIONS` | 4 | intersections visées |
| `VEHICLES` | 6 | véhicules |
| `DRIVING` | `"rule"` | conduite au démarrage : `"random"`, `"rule"` ou `"learned"` |

Réglages avancés : `SPEED` (vitesse moyenne), `MIN_SPEED_FACTOR` et `MAX_SPEED_FACTOR` (écart de vitesse entre véhicules), `SPAWN_DELAY`, `MIN_GAP` (distance de collision) dans `traffic.py` ; `DIVERGE_WINDOW`, `PACES` (allures) dans `policies.py` ; `CURVED_ROADS`, `CURVE_STRENGTH`, `FRAME_INTERVAL` dans `display.py`.

## Vérifications (QA)

```bash
./.venv/bin/python -m pip install -r requirements-dev.txt   # une fois : pytest + ruff
./run_checks.sh                                             # style + tests + check.py
```

| Outil | Ce qu'il vérifie |
|---|---|
| `ruff` | style, imports, noms, bugs courants (config dans `pyproject.toml`) |
| `pytest` (`test_roadnetwork.py` + `test_learning.py`, 137 tests) | une règle du projet = un test : START/END, toutes les routes vont au END, pas de croisement en X, types, doublons, même seed = même réseau, cas limites (grille 2×1, 0 et 10 routes), grille invalide = message clair, divergence des véhicules, vitesse propre de chaque véhicule, collisions (rattrapage, fusion, dépassement, contact compté une fois), conduites (règle, hasard, allure), collisions affichées, ce que voit un véhicule (sortie libre, véhicule devant, fusion, derrière), Q-learning (mise à jour calculée à la main, exploration, sauvegarde JSON), entraînement reproductible, durée des trajets, la conduite apprise bat le hasard et la règle, table apprise absente ou abîmée = retour à la règle, circulation cohérente avec les 3 conduites |
| `check.py` | balayage de 120 réseaux (4 tailles × 30 seeds) ; sur chacun, les 3 conduites roulent 20 s : collisions bien comptées, trajets de durée positive, véhicules toujours sur une route |

Grille invalide (`COLUMNS < 2` ou `ROWS < 1`) : le programme affiche un message clair au lieu de planter.

## Fonctionnalités

- Graphe de nodes et segments, cinq types de node.
- Chemin principal et nombre réglable de routes secondaires.
- Nombre d'intersections visé réglable ; génération cherche une solution proche.
- Seed reproductible, Randomize.
- Construction animée, routes courbes et légende.
- Aspect organique : chaque node est légèrement décalé à l'écran (`JITTER` dans `display.py`), même seed = même forme. Le modèle reste une grille, donc les règles et les tests ne changent pas.
- Toutes les routes rejoignent le END (aucun cul-de-sac).
- Animation optimisée (blitting : seuls les véhicules sont redessinés).
- Plus court chemin START → END (BFS), surligné en bleu, avec sa longueur affichée à l'écran.
- Nombre réglable de véhicules, départs espacés, chacun avec sa propre vitesse (les rapides rattrapent les lents).
- Collisions : deux véhicules trop proches comptent une collision, affichée par une croix rouge qui s'efface, et un compteur à l'écran.
- Règle de divergence : à une intersection, éviter la sortie choisie par un autre véhicule dans les 2 dernières secondes, si une autre sortie est disponible.
- Trois conduites au choix dans la fenêtre : hasard, règle, ou apprise par Q-learning (voir ci-dessous).

![Animation du réseau](docs/images/animation.gif)

## Apprentissage (ML) : des véhicules qui apprennent à ne pas se heurter

Les véhicules apprennent seuls, par **Q-learning**, à choisir leur sortie et leur allure (lente, normale, rapide) à chaque node pour éviter les collisions. Aucune bibliothèque de ML : environ 170 lignes de Python dans `learning.py`, commentaires compris.

**Comment ça marche, en 4 idées**

1. **Ce que voit un véhicule** (l'état) : pour chaque sortie, est-elle absente, libre, occupée plus loin, ou dangereuse (véhicule juste devant, ou un autre qui arrive au même node en même temps) ? Roule-t-il plus vite que la moyenne ? Quelqu'un le suit-il de près ? Soit 256 états possibles.
2. **Ce qu'il peut faire** (l'action) : une direction × une allure, soit 9 actions au plus.
3. **Ce qu'il reçoit** (la récompense) : −10 par collision, +1 à l'arrivée au END, −0,1 par seconde de route (sinon rouler toujours lentement serait gratuit).
4. **Ce qu'il retient** (la table Q) : `q[état][action]` = ce que rapporte cette action dans cet état. Après chaque segment : `q ← q + 0,1 × (récompense + 0,9 × meilleur q suivant − q)`. Tous les véhicules partagent la même table, enregistrée dans `q_table.json` (une ligne par état, lisible).

**Entraînement** (`train.py`, ~30 s) : 3000 épisodes de 60 s simulées, chacun sur un réseau et un nombre de véhicules tirés au hasard. Au début, les véhicules choisissent surtout au hasard pour explorer ; à la fin, surtout ce qu'ils ont appris.

![Courbe d'apprentissage](docs/images/apprentissage.png)

**Résultat** (`evaluate.py`) : sur 20 réseaux de test jamais vus à l'entraînement, 10 véhicules, 60 s.

| Conduite | Collisions / min | Trajet moyen (s) | Arrivées / min |
|---|---:|---:|---:|
| hasard | 86,2 | 12,2 | 41,0 |
| règle | 35,4 | 10,1 | 50,8 |
| **apprise** | **9,8** | **9,1** | **57,0** |

La conduite apprise fait moins de collisions que la règle sur les 20 réseaux, avec des trajets plus courts.

![Comparaison des conduites](docs/images/comparaison.png)

**Limites, honnêtement** : une règle écrite à la main (réserver le node suivant quelques instants) pourrait aussi supprimer les collisions ; l'intérêt ici est de montrer qu'un agent les évite **sans qu'on lui dise comment**. Les collisions ne bloquent pas les véhicules (ils se traversent) : elles sont seulement comptées et punies. Détail des choix et des mesures : [ml_archi/tickets.md](ml_archi/tickets.md).

## Circuit

Par défaut (`CIRCUIT = True` dans `main.py`) : 4 grilles reliées en boucle, le END de chacune est le START de la suivante. Chaque voiture a un prénom unique, compte ses tours et son meilleur tour ; classement en haut à gauche. Détails : `docs/circuit.md`. `CIRCUIT = False` = réseau simple START → END.

## Expérience Alice (ML sur une seule voiture)

Alice (voiture n°0) conduit avec un modèle de ML, les autres avec la Règle : on voit la différence.

```bash
.venv/bin/python tree_model.py   # apprentissage supervisé : arbre de décision
.venv/bin/python alice.py        # apprentissage par renforcement (Q-learning) + comparaison
```

Guide pas à pas pour débutant : `docs/ml_alice.md`. Choix dans `main.py` : `ALICE = "rl"`, `"tree"` ou `None`.

## Architecture

| Fichier | Responsabilité |
|---|---|
| `models.py` | NodeType, Node, Segment |
| `network.py` | grille, liens, plus court chemin |
| `generator.py` | construction du réseau et branches |
| `traffic.py` | véhicules, mouvement, vitesses, collisions |
| `policies.py` | conduites : règle de divergence, hasard (sortie + allure) |
| `learning.py` | apprentissage : ce que voit un véhicule (état), agent Q-learning `QAgent` |
| `train.py` | entraînement sans fenêtre : écrit `q_table.json` et la courbe d'apprentissage |
| `q_table.json` | la conduite apprise (table Q), une ligne par état |
| `evaluate.py` | compare hasard, règle et conduite apprise sur 20 réseaux de test |
| `display.py` | fenêtre, curseurs, dessin et animation |
| `circuit.py` | 4 cadres en boucle, coordonnées écran |
| `tree_model.py` | ML supervisé : collecte, arbre de décision, conduite `TreePolicy` |
| `alice.py` | RL sur Alice seule + comparaison des 4 conduites |
| `main.py` | point d'entrée et réglages par défaut |
| `check.py` | vérifications automatiques (balayage) |
| `test_roadnetwork.py` | tests pytest, une règle = un test |
| `test_learning.py` | tests pytest de l'apprentissage |
| `run_checks.sh` | QA en une commande |

Voir [docs/architecture.md](docs/architecture.md) et [docs/](docs/README.md).

## Équipe

| Membre | Contribution |
|---|---|
| Yusuf | _à compléter_ |
| _à compléter_ | _à compléter_ |
| _à compléter_ | _à compléter_ |

## Sources et outils

- Support de cours « Bootcamp Python B3 » – Alexandre Coirier.
- Matplotlib : animation, widgets, tracés et patches.
- Assistance IA utilisée et code relu par l'équipe.
