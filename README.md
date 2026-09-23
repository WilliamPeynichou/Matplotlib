# RoadNetwork

Générateur procédural de réseau routier sur une grille, affiché et animé avec Matplotlib.
Projet du Bootcamp Python B3 – Sup de Vinci 2026-2027.

![Réseau généré](docs/images/reseau.png)

## Installation

Prérequis : Python 3.14.

```bash
# macOS / Linux
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt

# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Lancement

```bash
./.venv/bin/python main.py        # macOS / Linux
.\.venv\Scripts\python.exe main.py  # Windows
```

- La fenêtre s'ouvre et le réseau se construit segment par segment.
- **Randomize** : génère un nouveau réseau.
- La seed s'affiche dans le titre et dans le terminal. Pour rejouer un réseau, mettre `SEED = 4821` en haut de `main.py`.

Réglages (constantes en haut des fichiers) :

| Fichier | Constante | Effet |
|---|---|---|
| main.py | `COLUMNS`, `ROWS` | taille de la grille |
| main.py | `SEED` | `None` = au hasard, un nombre = réseau fixe |
| generator.py | `MIN_BRANCHES`, `MAX_BRANCHES` | nombre de branches |
| display.py | `CURVED_ROADS` | routes courbes ou droites |
| display.py | `ANIMATION_INTERVAL` | vitesse de l'animation (ms) |

## Vérifications

```bash
./.venv/bin/python check.py
```

Génère 400 réseaux (4 tailles de grille × 100 seeds) et vérifie les règles : 1 START au milieu de la 1ʳᵉ colonne, 1 END dans la dernière, rien hors grille, pas de doublon, pas de croisement en X, types cohérents, plus court chemin valide. Affiche la seed de chaque réseau en erreur, sinon `OK`.

## Fonctionnalités

- Grille de nodes et types : Unused, Start, End, Connection, Intersection.
- Chemin principal START → END, colonne par colonne, déplacements contraints (monter, rester, descendre).
- 2 à 4 branches qui fusionnent avec les routes existantes → intersections automatiques.
- Seed reproductible.
- Bouton Randomize.
- Animation de la construction.
- Routes courbes, légende.
- Plus court chemin START → END (parcours en largeur, BFS) surligné en bleu.

![Animation](docs/images/animation.gif)

## Architecture

| Fichier | Rôle |
|---|---|
| `models.py` | les briques : `NodeType`, `Node`, `Segment` |
| `network.py` | le plateau : `RoadNetwork` (grille, liens, plus court chemin) |
| `generator.py` | les règles : chemin principal, branches |
| `display.py` | l'écran : dessin, animation, bouton |
| `main.py` | le point d'entrée |
| `check.py` | l'outil de vérification |

Détails et choix justifiés : [docs/architecture.md](docs/architecture.md). Toute la documentation : [docs/](docs/README.md).

## Équipe

| Membre | Rôle |
|---|---|
| _à compléter_ | Données & réseau |
| _à compléter_ | Génération |
| _à compléter_ | Affichage |

## Sources

- Support de cours « Bootcamp Python B3 » – Alexandre Coirier.
- Documentation Matplotlib (`FuncAnimation`, `widgets.Button`, `patches.PathPatch`).
- Code réalisé avec l'aide d'un assistant IA (Claake Code), relu et expliqué par l'équipe.
