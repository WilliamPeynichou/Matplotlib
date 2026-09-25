"""Génération procédurale : toutes les routes finissent au END (features 5, 8 et 14)."""

import random

from models import Node, NodeType
from network import RoadNetwork

MOVES = [-1, 0, 1]  # descendre, rester, monter
DEFAULT_ROADS = 4  # chemin principal + 3 branches
MAX_ATTEMPTS = 200  # essais pour atteindre le nombre d'intersections demandé


def generate_network(network: RoadNetwork, seed: int, roads: int = DEFAULT_ROADS,
                     intersections: int | None = None, fixed_end: bool = False) -> int:
    """Génère `roads` routes. Si `intersections` est donné, fait plusieurs essais
    et garde le réseau le plus proche. Renvoie le nombre d'intersections obtenu."""
    roads = max(1, roads)  # au moins la route principale
    rng = random.Random(seed)
    best_state, best_score = None, None
    for _ in range(MAX_ATTEMPTS if intersections is not None else 1):
        state = rng.getstate()
        built = build_network(network, rng, roads, fixed_end)
        count = count_intersections(network)
        target = count if intersections is None else intersections
        score = (roads - built, abs(count - target))  # d'abord toutes les routes, puis l'écart
        if best_score is None or score < best_score:
            best_state, best_score = state, score
        if score == (0, 0):
            return count
    rng.setstate(best_state)  # rejoue le meilleur essai (même hasard = même réseau)
    build_network(network, rng, roads, fixed_end)
    return count_intersections(network)


def build_network(network: RoadNetwork, rng: random.Random, roads: int,
                  fixed_end: bool = False) -> int:
    """Un essai : chemin principal START -> END, puis des branches qui rejoignent
    la route. Renvoie le nombre de routes construites."""
    network.reset()
    start = network.get_node(0, network.rows // 2)
    start.type = NodeType.START
    if fixed_end:  # circuit : END au milieu de la dernière colonne (jonction avec le cadre suivant)
        end = network.get_node(network.columns - 1, network.rows // 2)
        end.type = NodeType.END
        add_path(network, find_path(network, rng, start, end, min_length=2))
    else:
        path = find_path(network, rng, start, None)
        add_path(network, path)
        end = path[-1]
        end.type = NodeType.END
    built = 1
    for _ in range(roads - 1):
        on_road = [n for n in network.nodes if n.type is not NodeType.UNUSED and n is not end]
        branch = find_path(network, rng, rng.choice(on_road), end)
        if branch:
            add_path(network, branch)
            built += 1
    return built


def find_path(network: RoadNetwork, rng: random.Random, start: Node,
              end: Node | None, min_length: int = 3) -> list[Node] | None:
    """Avance d'une colonne par pas jusqu'à la dernière colonne (route principale)
    ou jusqu'à retomber sur la route (branche). Une branche vise toujours le END :
    elle ne peut pas finir en cul-de-sac. Renvoie None si bloqué."""
    path = [start]
    current = start
    while current.x < network.columns - 1:
        following = choose_next(network, rng, current, end)
        if following is None:
            return None
        path.append(following)
        current = following
        if end is not None and following.type is not NodeType.UNUSED:
            break  # rejoint la route existante, qui mène déjà au END
    if end is not None and len(path) < min_length:
        return None  # branche trop courte : doublon inutile
    return path


def add_path(network: RoadNetwork, path: list[Node]) -> None:
    """Crée les segments du chemin."""
    for a, b in zip(path, path[1:]):
        network.create_segment(a, b)


def choose_next(network: RoadNetwork, rng: random.Random, current: Node,
                end: Node | None) -> Node | None:
    """Case suivante valide au hasard dans la colonne de droite."""
    moves = MOVES.copy()
    rng.shuffle(moves)
    for dy in moves:
        target = network.get_node(current.x + 1, current.y + dy)
        if target is None:
            continue  # hors grille
        if end is not None and abs(target.y - end.y) > end.x - target.x:
            continue  # trop loin : ne pourrait plus atteindre le END
        if end is not None and target.x == end.x and target is not end:
            continue  # dernière colonne : seul le END est permis
        if network.has_segment(current, target) or creates_crossing(network, current, target):
            continue  # déjà relié ou croisement en X
        return target
    return None


def creates_crossing(network: RoadNetwork, a: Node, b: Node) -> bool:
    """Vrai si la diagonale a -> b croise l'autre diagonale du même carré (forme un X)."""
    if a.y == b.y:
        return False
    return network.has_segment(network.get_node(a.x, b.y), network.get_node(b.x, a.y))


def count_intersections(network: RoadNetwork) -> int:
    """Nombre de nodes de type INTERSECTION."""
    return sum(1 for node in network.nodes if node.type is NodeType.INTERSECTION)
