# Architecture

Objectif : **simple à coder, simple à expliquer**. 5 fichiers, 4 classes, rien de plus.

## Arborescence

```
python_b3/
├── .venv/  .gitignore  requirements.txt  README.md  docs/
├── main.py        # lance le programme
├── models.py      # NodeType, Node, Segment   (les données)
├── network.py     # RoadNetwork               (la grille + les liens)
├── generator.py   # generate_network()        (le hasard)
├── display.py     # draw_network(), bouton    (le dessin)
└── check.py       # outil de test (feature 7), pas lancé par main
```

Phrase pour l'oral : *« models = les briques, network = le plateau, generator = les règles, display = l'écran, main = le bouton ON. »*

## Qui importe qui

```
main ──► network, generator, display
generator ──► network, models
display ──► network, models
network ──► models
```
Une seule règle : `generator` ne dessine pas, `display` ne tire pas au hasard.

## Les classes

```python
class NodeType(Enum):
    UNUSED, START, END, CONNECTION, INTERSECTION

class Node:        # x, y, type, segments
    update_type()  # 3 segments ou plus -> INTERSECTION (sauf START/END)

class Segment:     # start, end

class RoadNetwork: # columns, rows, nodes (liste plate), segments (liste)
    create_node(x, y)       # nom imposé par le cours (séance 2)
    get_node(x, y)
    is_inside(x, y)
    create_segment(a, b)    # nom imposé par le cours
    reset()
    get_shortest_path()     # bonus F12 : BFS START → END
```

## Les fonctions

| Fichier | Fonction | Rôle |
|---|---|---|
| generator.py | `generate_network(network, seed)` | chemin principal + branches |
| generator.py | `generate_path(network, rng, start_node)` | avance colonne par colonne, dy ∈ {-1, 0, 1} |
| display.py | `draw_node(ax, node)` | un point coloré selon son type |
| display.py | `draw_network(ax, network)` | tous les segments puis tous les nodes |
| display.py | `show(network, on_randomize)` | fenêtre + bouton Randomize + animation |

## Contrat

Signatures **figées** au round 0 pour que les 3 devs codent en parallèle. Round 0 : on les pousse sur `main` en *stubs* (corps = `pass` ou valeur vide + docstring). Modification seulement en fin de round, à 3.

```python
# models.py
class NodeType(Enum): UNUSED, START, END, CONNECTION, INTERSECTION

class Node:
    def __init__(self, x: int, y: int): ...        # type = UNUSED, segments = []
    def update_type(self) -> None: ...

class Segment:
    def __init__(self, start: Node, end: Node): ...

# network.py
class RoadNetwork:
    def __init__(self, columns: int, rows: int): ...  # crée la grille
    def create_node(self, x: int, y: int) -> Node: ...
    def get_node(self, x: int, y: int) -> Node | None: ...  # None si hors grille
    def is_inside(self, x: int, y: int) -> bool: ...
    def create_segment(self, a: Node, b: Node) -> Segment | None: ...  # None si doublon
    def reset(self) -> None: ...
    def get_shortest_path(self) -> list[Node]: ...    # bonus F12

# generator.py
def generate_network(network: RoadNetwork, seed: int) -> None: ...
def generate_path(network: RoadNetwork, rng: random.Random, start: Node) -> list[Node]: ...

# display.py
def draw_node(ax, node: Node) -> None: ...
def draw_network(ax, network: RoadNetwork) -> None: ...
def show(network: RoadNetwork, seed: int, on_randomize) -> None: ...  # on_randomize() -> int (nouvelle seed)

# main.py
def main() -> None: ...
```

Tester sans attendre les autres : fabriquer un petit réseau à la main (3 nodes, 2 segments) ou utiliser le stub.

## Algorithme (4 étapes)

1. **Grille** : `columns × rows` nodes UNUSED, créés avec `create_node()`.
2. **Chemin principal** : START au milieu de la colonne 0. À chaque colonne suivante : monter, rester ou descendre (au hasard, sans sortir). Dernier node = END.
3. **Branches** : choisir quelques nodes du chemin principal, relancer `generate_path` depuis eux. Si une branche tombe sur un node déjà utilisé, on relie et on s'arrête. Une branche ne crée jamais de 2ᵉ END : elle s'arrête en CONNECTION.
4. **Types** : `create_segment` met à jour les types automatiquement → les intersections apparaissent toutes seules.

Même fonction pour le chemin principal et les branches = moins de code, moins à expliquer.

## Choix et justifications

| Choix | Pourquoi | Écarté |
|---|---|---|
| 5 fichiers | cours 1.10 : un module, une responsabilité. Assez pour être clair, pas trop pour se perdre | tout dans `main.py` (illisible) / 10 fichiers (trop à expliquer) |
| `Node` + `Segment` | un réseau routier = un graphe (cours 1.1) | tuples `(x1, y1, x2, y2)` : pas de type, illisible |
| Enum `NodeType` | cours 1.9 : faute de frappe = erreur immédiate | chaînes `"start"` |
| Node garde ses `segments` | intersection = `len(node.segments) >= 3`, une ligne | recompter dans tout le réseau à chaque fois |
| Nodes en liste plate `x * rows + y` | formule du cours 1.7, déjà connue | liste de listes, dictionnaire |
| `create_segment()` seul moyen de relier | un seul endroit met à jour les types → pas d'incohérence | `append` partout |
| `RoadNetwork` garde tout | Randomize = `reset()` + regénérer | variables globales |
| Segments dans l'ordre de création | l'animation rejoue la liste, zéro code en plus | — |
| `random.Random(seed)` | même seed = même réseau → bug reproductible, démo sûre | `random` global |
| Une seule fonction `generate_path` | chemin principal et branches = même règle | deux algos différents |
| Constantes en haut du fichier qui les utilise | pas de fichier en plus, facile à trouver | `config.py` séparé |

## Ce qu'on ne fait pas
- Pas de bibliothèque de graphe (networkx) : on doit concevoir nous-mêmes.
- Pas d'héritage (`StartNode`...) : le type change pendant la génération, un attribut suffit.
- Pas de diagonales croisées, pas d'algo compliqué avant que le socle marche.
- Les routes courbes (visibles sur l'exemple du cours) viennent **après** le socle, dans `display.py` uniquement (feature 11).
