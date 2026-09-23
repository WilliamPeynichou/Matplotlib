"""Les règles de génération procédurale (features 5 et 8)."""

import random

from models import Node, NodeType
from network import RoadNetwork

MOVES = [-1, 0, 1]  # descendre, rester, monter
MIN_BRANCHES = 2
MAX_BRANCHES = 4
MIN_BRANCH_LENGTH = 2


def generate_network(network: RoadNetwork, seed: int) -> None:
    """Génère le chemin principal START -> END, puis les branches."""
    rng = random.Random(seed)
    start = network.get_node(0, network.rows // 2)
    start.type = NodeType.START
    path = generate_path(network, rng, start)
    path[-1].type = NodeType.END
    generate_branches(network, rng, path)


def generate_branches(network: RoadNetwork, rng: random.Random, main_path: list[Node]) -> None:
    """Fait partir quelques branches depuis des nodes du chemin principal."""
    candidates = main_path[1:-1]  # ni START, ni END
    count = min(rng.randint(MIN_BRANCHES, MAX_BRANCHES), len(candidates))
    max_length = max(MIN_BRANCH_LENGTH, network.columns // 2)
    for node in rng.sample(candidates, count):
        length = rng.randint(MIN_BRANCH_LENGTH, max_length)
        generate_path(network, rng, node, length)


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
