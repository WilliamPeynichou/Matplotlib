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

La fenêtre propose des curseurs pour régler le nombre de routes, le nombre d'intersections visé et le nombre de véhicules. Clique **Randomize** pour changer de réseau. Les véhicules parcourent les routes ; à chaque intersection, ils prennent une autre sortie que le dernier véhicule passé dans les 2 secondes, si une autre sortie existe.

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

Réglages avancés dans `display.py` : `SPEED`, `SPAWN_DELAY`, `DIVERGE_WINDOW` dans `traffic.py` ; `CURVED_ROADS`, `CURVE_STRENGTH`, `FRAME_INTERVAL` dans `display.py`.

## Vérifications

```bash
./.venv/bin/python check.py
```

Teste les réseaux sur plusieurs tailles et seeds : départ/arrivée, liens, croisements, types, plus court chemin et règle de divergence des véhicules.

## Fonctionnalités

- Graphe de nodes et segments, cinq types de node.
- Chemin principal et nombre réglable de routes secondaires.
- Nombre d'intersections visé réglable ; génération cherche une solution proche.
- Seed reproductible, Randomize.
- Construction animée, routes courbes et légende.
- Plus court chemin START → END (BFS), surligné en bleu.
- Nombre réglable de véhicules, départs espacés.
- Règle de divergence : à une intersection, éviter la sortie choisie par un autre véhicule dans les 2 dernières secondes, si une autre sortie est disponible.

![Animation du réseau](docs/images/animation.gif)

## Architecture

| Fichier | Responsabilité |
|---|---|
| `models.py` | NodeType, Node, Segment |
| `network.py` | grille, liens, plus court chemin |
| `generator.py` | construction du réseau et branches |
| `traffic.py` | véhicules, mouvement, décisions de sortie |
| `display.py` | fenêtre, curseurs, dessin et animation |
| `main.py` | point d'entrée et réglages par défaut |
| `check.py` | vérifications automatiques |

Voir [docs/architecture.md](docs/architecture.md) et [docs/](docs/README.md).

## Équipe

| Membre | Contribution |
|---|---|
| _à compléter_ | _à compléter_ |
| _à compléter_ | _à compléter_ |
| _à compléter_ | _à compléter_ |

## Sources et outils

- Support de cours « Bootcamp Python B3 » – Alexandre Coirier.
- Matplotlib : animation, widgets, tracés et patches.
- Assistance IA utilisée et code relu par l'équipe.
