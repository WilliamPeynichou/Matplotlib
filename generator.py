"""Les règles de génération procédurale (features 5, 8 et 14)."""

import random

from models import Node, NodeType
from network import RoadNetwork

MOVES = [-1, 0, 1]  # descendre, rester, monter
DEFAULT_ROADS = 4  # chemin principal + 3 branches
MIN_BRANCH_LENGTH = 2
MAX_ATTEMPTS = 200  # essais pour atteindre le nombre d'intersections demandé


def generate_network(network: RoadNetwork, seed: int, roads: int = DEFAULT_ROADS,
                     intersections: int | None = None) -> int:
    """Génère un réseau de `roads` routes. Si `intersections` est donné, fait plusieurs
    essais et garde le réseau le plus proche. Renvoie le nombre d'intersections obtenu."""
    rng = random.Random(seed)
    best_state, best_score = None, None
    for _ in range(MAX_ATTEMPTS if intersections is not None else 1):
        state = rng.getstate()
        built = build_network(network, rng, roads)
        count = count_intersections(network)
        target = count if intersections is None else intersections
        score = (roads - built, abs(count - target))  # d'abord toutes les routes, puis l'écart
        if best_score is None or score < best_score:
            best_state, best_score = state, score
        if score == (0, 0):
            return count
    rng.setstate(best_state)  # rejoue le meilleur essai (même hasard = même réseau)
    build_network(network, rng, roads)
    return count_intersections(network)


def build_network(network: RoadNetwork, rng: random.Random, roads: int) -> int:
    """Un essai : chemin principal + branches. Renvoie le nombre de routes construites."""
    network.reset()
    start = network.get_node(0, network.rows // 2)
    start.type = NodeType.START
    path = generate_path(network, rng, start)
    path[-1].type = NodeType.END
    return 1 + generate_branches(network, rng, roads - 1)


def count_intersections(network: RoadNetwork) -> int:
    """Nombre de nodes de type INTERSECTION."""
    return sum(1 for node in network.nodes if node.type is NodeType.INTERSECTION)


def generate_branches(network: RoadNetwork, rng: random.Random, count: int) -> int:
    """Fait partir `count` branches depuis la route existante. Renvoie le nombre réussi."""
    max_length = max(MIN_BRANCH_LENGTH, network.columns // 2)
    built = 0
    for _ in range(count):
        candidates = [
            node for node in network.nodes
            if node.type in (NodeType.CONNECTION, NodeType.INTERSECTION)
            and node.x < network.columns - 1
        ]
        if not candidates:
            break
        length = rng.randint(MIN_BRANCH_LENGTH, max_length)
        branch = generate_path(network, rng, rng.choice(candidates), length)
        if len(branch) > 1:
            built += 1
    return built


def generate_path(
    network: RoadNetwork, rng: random.Random, start: Node, max_steps: int | None = None
) -> list[Node]:
    """Avance d'une colonne par pas. S'arrête au bord, après max_steps, ou en rejoignant la route."""
    path = [start]
    current = start
    while current.x < network.columns - 1:
        if max_steps is not None and len(path) > max_steps:
            break
        following = choose_next(network, rng, current)
        if following is None:
            break
        joins_road = following.type is not NodeType.UNUSED
        network.create_segment(current, following)
        path.append(following)
        current = following
        if joins_road:  # fusion avec une route existante : on s'arrête
            break
    return path


def choose_next(network: RoadNetwork, rng: random.Random, current: Node) -> Node | None:
    """Choisit au hasard la case suivante valide dans la colonne de droite."""
    moves = MOVES.copy()
    rng.shuffle(moves)
    for dy in moves:
        target = network.get_node(current.x + 1, current.y + dy)
        if target is None:
            continue  # hors grille
        if network.has_segment(current, target):
            continue  # déjà relié
        if creates_crossing(network, current, target):
            continue  # croiserait une diagonale
        return target
    return None


def creates_crossing(network: RoadNetwork, a: Node, b: Node) -> bool:
    """Vrai si la diagonale a -> b croise l'autre diagonale du même carré (forme un X)."""
    if a.y == b.y:
        return False
    return network.has_segment(network.get_node(a.x, b.y), network.get_node(b.x, a.y))
