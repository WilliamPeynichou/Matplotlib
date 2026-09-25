# Architecture

Objectif : **simple à coder, simple à expliquer**. Le socle : 5 fichiers, 4 classes, rien de plus. La circulation (`traffic.py`, `policies.py`) et l'apprentissage (`learning.py`, `train.py`, `evaluate.py`) s'ajoutent à côté, sans modifier le socle.

## Arborescence

```
python_b3/
├── .venv/  .gitignore  requirements.txt  README.md  docs/
├── main.py        # lance le programme
├── models.py      # NodeType, Node, Segment   (les données)
├── network.py     # RoadNetwork               (la grille + les liens)
├── generator.py   # generate_network()        (le hasard)
├── display.py     # draw_network(), bouton    (le dessin)
├── traffic.py     # circulation, vitesses, collisions
├── policies.py    # conduites : règle de divergence, hasard
├── learning.py    # apprentissage : ce que voit un véhicule, agent Q-learning
├── train.py       # entraînement sans fenêtre -> q_table.json + courbe
├── evaluate.py    # compare hasard / règle / appris -> tableau + barres
└── check.py       # tests génération + trafic
```

Phrase pour l'oral : *« models = les briques, network = le plateau, generator = les règles, display = l'écran, main = le bouton ON. »*

## Qui importe qui

```
main ──► network, generator, display, learning
generator ──► network, models
display ──► network, models, traffic, learning
network ──► models
traffic ──► network, models, policies
policies ──► models
learning ──► traffic, policies, models
train ──► learning, traffic, policies, generator, network
evaluate ──► train, learning, policies
```
Une seule règle : `generator` ne dessine pas, `display` ne tire pas au hasard.

## Circulation – `traffic.py` et `policies.py`

`Traffic` gère l’horloge, les véhicules et les collisions. Chaque `Vehicle` garde sa position courante, sa prochaine destination, sa progression sur le segment et sa vitesse propre. Deux véhicules à moins de `MIN_GAP` l’un de l’autre (même segment, ou autour du même node) sont en contact : chaque nouveau contact compte une collision.

À chaque node, `Traffic` demande à sa **conduite** (`policies.py`) la sortie et l’allure : `choose(traffic, vehicle, node, exits) -> (sortie, allure)`. La vitesse du segment vaut vitesse propre × allure (`slow` 0,5, `normal` 1, `fast` 1,5).

- `RulePolicy` (par défaut) : la règle de divergence. `choose_exit()` cherche les sorties choisies à ce node dans les 2 dernières secondes et essaie d’en prendre une autre ; allure normale.
- `RandomPolicy` : sortie et allure au hasard, point de comparaison pour l’apprentissage (voir [ml_archi/tickets.md](../ml_archi/tickets.md)).

## Apprentissage – `learning.py`

`get_state()` résume ce que voit un véhicule arrêté sur un node en un petit tuple `(descendre, tout droit, monter, rapide, derrière)`. Chaque direction vaut : pas de sortie, libre, véhicule devant loin, ou danger (véhicule devant proche, ou arrivée en même temps qu’un autre au même node). `rapide` compare sa vitesse propre à la moyenne, `derrière` signale un véhicule qui le suit de près. 256 états possibles : c’est la clé de la table de Q-learning.

`QAgent` est une conduite (`Policy`) qui apprend. Sa table `q[état][action]` estime ce que rapporte chacune des 9 actions (3 directions × 3 allures). Chaque véhicule garde sa dernière décision ; à la suivante (ou à l’arrivée au END), la table est corrigée avec la récompense reçue entre-temps : −10 par collision, +1 à l’arrivée, −0,1 par seconde de route. `Traffic` prévient la conduite par `on_collision()` et `on_arrival()`. Tous les véhicules partagent la même table. `save()` / `load()` l’écrivent en JSON ; un agent chargé prend toujours la meilleure action et n’apprend plus.

`train.py` entraîne l’agent sans fenêtre : 3000 épisodes de 60 s simulées, chacun sur un réseau et un nombre de véhicules tirés au hasard. L’exploration `epsilon` descend de 1 (tout au hasard) à 0,05. Il écrit `q_table.json` et la courbe `docs/images/apprentissage.png`, où les niveaux du hasard et de la règle servent de repère.

`evaluate.py` fait rouler les trois conduites sur les 20 mêmes réseaux de test (seeds 0 à 19, jamais utilisées à l’entraînement) et compare collisions par minute, durée moyenne d’un trajet (`Traffic.trip_times`) et arrivées par minute. Il écrit `docs/images/comparaison.png`.

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
| generator.py | `build_network(network, rng, roads)` | chemin principal puis branches |
| generator.py | `find_path(network, rng, start, end)` | avance colonne par colonne, dy ∈ {-1, 0, 1}. Branche : s'arrête en retombant sur la route, vise toujours le END |
| generator.py | `add_path(network, path)` | crée les segments du chemin (seulement si le chemin est complet) |
| generator.py | `choose_next(network, rng, current, end)` | case suivante valide : dans la grille, END encore atteignable, pas déjà reliée, pas de croisement en X |
| generator.py | `creates_crossing(network, a, b)` | vrai si la diagonale a → b croise l'autre diagonale du carré |
| display.py | `draw_node(ax, node)` | un point coloré selon son type |
| display.py | `draw_network(ax, network)` | tous les segments puis tous les nodes |
| display.py | `draw_grid` / `draw_step` / `animate_network` | grille vide, puis un segment par image |
| display.py | `show(network, seed, on_randomize)` | fenêtre + bouton Randomize + animation |
| display.py | `draw_shortest_path` / `draw_legend` / `setup_axes` | chemin surligné, légende, repère |
| network.py | `get_shortest_path()` | BFS START → END : file d'attente + dict des parents |
| main.py | `create_seed()` | `SEED` fixée ou seed au hasard |

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
    def has_segment(self, a: Node, b: Node) -> bool: ...
    def create_segment(self, a: Node, b: Node) -> Segment | None: ...  # None si doublon
    def reset(self) -> None: ...
    def get_start(self) -> Node | None: ...
    def get_shortest_path(self) -> list[Node]: ...    # bonus F12 : BFS
    def build_path(self, parents: dict, end: Node) -> list[Node]: ...

# generator.py
def generate_network(network: RoadNetwork, seed: int, roads: int = 4,
                     intersections: int | None = None) -> int: ...
def find_path(network: RoadNetwork, rng: random.Random, start: Node,
              end: Node | None) -> list[Node] | None: ...
def add_path(network: RoadNetwork, path: list[Node]) -> None: ...

# display.py
def draw_node(ax, node: Node) -> None: ...
def draw_network(ax, network: RoadNetwork) -> None: ...
def animate_network(fig, ax, network: RoadNetwork, seed: int) -> FuncAnimation | None: ...
def show(network: RoadNetwork, seed: int, on_randomize) -> None: ...  # on_randomize() -> int (nouvelle seed)

# main.py
def main() -> None: ...
```

Tester sans attendre les autres : fabriquer un petit réseau à la main (3 nodes, 2 segments) ou utiliser le stub.

## Algorithme (4 étapes)

1. **Grille** : `columns × rows` nodes UNUSED, créés avec `create_node()`.
2. **Chemin principal** : START au milieu de la colonne 0. À chaque colonne suivante : monter, rester ou descendre (au hasard, sans sortir). Dernier node = END.
3. **Branches** : partir d'un node de la route, relancer `find_path`. La branche ne choisit que des cases d'où le END reste atteignable (`|y - end.y| <= end.x - x`). Elle s'arrête dès qu'elle retombe sur la route (qui mène déjà au END) ou sur le END. **Toutes les routes finissent donc au END, aucun cul-de-sac.** Si la branche est bloquée, on la jette (rien n'est dessiné). Interdit : deux diagonales qui se croisent en X sans node au milieu.
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
| Historique trafic de 2 secondes | respecter la règle demandée et donner priorité à une sortie différente si elle existe | choisir au hasard sans mémoire |
| Simulation trafic à temps réel | la position visuelle suit les courbes et la vitesse ne dépend pas directement du nombre d’images | déplacements par image, qui changent avec les performances |
| Une seule fonction `find_path` | chemin principal et branches = même règle | deux algos différents |
| BFS pour le plus court chemin | tous les segments ont le même coût → BFS suffit, plus simple que A* | A*, Dijkstra |
| Courbes = Bézier à tangentes horizontales | chaque segment va de x à x+1 → routes lisses sans calcul global | lissage de tout le chemin |
| Décalage organique seulement à l'écran (`get_position`) | les règles (grille, pas de X) restent simples et testées ; `JITTER < 0.5` garde l'ordre des nodes → aucun croisement visuel. Décalage tiré de `seed + case` → reproductible | déplacer les nodes dans le modèle (règles et tests à refaire) |
| Constantes en haut du fichier qui les utilise | pas de fichier en plus, facile à trouver | `config.py` séparé |
| Collision = événement compté, pas un blocage | les véhicules se traversent : on compte, on affiche, on punit. S'ils se bloquaient, aucune collision ne serait possible → rien à apprendre | véhicules qui s'arrêtent derrière les autres |
| Conduite = objet avec `choose()` | la règle, le hasard et l'agent se branchent au même endroit ; comparer = changer un argument | `if mode == ...` dans `traffic.py` |
| Q-learning **en table** | 256 états × 9 actions : une table suffit, chaque valeur se lit dans `q_table.json`, la formule tient en une ligne et s'explique à l'oral | réseau de neurones (PyTorch, stable-baselines3) : lourd, dépendances, impossible à expliquer ligne par ligne |
| État petit et fait main | 5 cases qu'on peut nommer ; l'agent apprend vite (30 s) | positions brutes de tous les véhicules : trop d'états, jamais vus deux fois |
| Une table partagée par tous les véhicules | ce que l'un apprend sert aux autres ; un seul fichier | une table par véhicule (chacun n'apprendrait que de ses propres trajets) |
| −0,1 par seconde de route | sans coût du temps, « toujours lent » serait gratuit | seulement collision et arrivée |
| Réseaux de test (seeds 0–19) jamais utilisés à l'entraînement (≥ 10 000) | mesurer ce que l'agent a appris, pas ce qu'il a retenu par cœur | évaluer sur les réseaux d'entraînement |
| Table absente ou abîmée → règle + message | la démo ne plante jamais (malus −3 si crash au lancement) | laisser l'erreur remonter |

## Ce qu'on ne fait pas
- Pas de bibliothèque de graphe (networkx) : on doit concevoir nous-mêmes.
- Pas de bibliothèque de ML (PyTorch, scikit-learn) : le Q-learning en table tient dans `learning.py` et s'explique ligne par ligne.
- Pas d'héritage (`StartNode`...) : le type change pendant la génération, un attribut suffit.
- Pas de diagonales croisées, pas d'algo compliqué avant que le socle marche.
- Les routes courbes (visibles sur l'exemple du cours) viennent **après** le socle, dans `display.py` uniquement (feature 11).
