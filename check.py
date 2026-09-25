"""Vérifie génération, intersections demandées, divergence des véhicules et collisions."""

from generator import generate_network
from learning import DRIVINGS, make_policy
from models import NodeType
from network import RoadNetwork
from traffic import Traffic

SEEDS = 30
SIZES = [(15, 9), (3, 3), (2, 1), (30, 20)]


def expected_type(node) -> NodeType:
    """Type attendu d'un node selon son nombre de segments."""
    count = len(node.segments)
    if count == 0:
        return NodeType.UNUSED
    if count <= 2:
        return NodeType.CONNECTION
    return NodeType.INTERSECTION


def check_network(network: RoadNetwork) -> list[str]:
    """Renvoie la liste des erreurs trouvées dans un réseau."""
    errors = []
    starts = [n for n in network.nodes if n.type is NodeType.START]
    ends = [n for n in network.nodes if n.type is NodeType.END]
    if len(starts) != 1:
        errors.append(f"{len(starts)} START au lieu de 1")
    if len(ends) != 1:
        errors.append(f"{len(ends)} END au lieu de 1")
    if starts and starts[0] is not network.get_node(0, network.rows // 2):
        errors.append("START n'est pas au milieu de la première colonne")
    if ends and ends[0].x != network.columns - 1:
        errors.append("END n'est pas dans la dernière colonne")

    exits = {id(segment.start) for segment in network.segments}
    for node in network.nodes:
        if node.type not in (NodeType.UNUSED, NodeType.END) and id(node) not in exits:
            errors.append(f"cul-de-sac ({node.x}, {node.y}) : n'atteint pas le END")

    seen = set()
    for segment in network.segments:
        a, b = segment.start, segment.end
        if not network.is_inside(a.x, a.y) or not network.is_inside(b.x, b.y):
            errors.append(f"{segment} hors grille")
        key = frozenset(((a.x, a.y), (b.x, b.y)))
        if key in seen:
            errors.append(f"{segment} en double")
        seen.add(key)
        if abs(a.x - b.x) != 1 or abs(a.y - b.y) > 1:
            errors.append(f"{segment} déplacement invalide")
        if a.y != b.y and network.has_segment(
            network.get_node(a.x, b.y), network.get_node(b.x, a.y)
        ):
            errors.append(f"{segment} croisement en X")

    for node in network.nodes:
        if node.type in (NodeType.START, NodeType.END):
            if not node.segments:
                errors.append(f"{node} sans segment")
        elif node.type is not expected_type(node):
            errors.append(f"{node} devrait être {expected_type(node).name}")

    path = network.get_shortest_path()
    if not path or path[0].type is not NodeType.START or path[-1].type is not NodeType.END:
        errors.append("plus court chemin START -> END absent")
    elif any(not network.has_segment(a, b) for a, b in zip(path, path[1:])):
        errors.append("plus court chemin utilise un lien absent")
    return errors


def check_divergence() -> list[str]:
    """Simule des véhicules : deux passages proches à une intersection doivent diverger."""
    network = RoadNetwork(8, 7)
    generate_network(network, seed=4, roads=5, intersections=4)
    traffic = Traffic(network, count=12, seed=27)
    for _ in range(500):
        traffic.update(0.05)
    errors = []
    if not traffic.decisions:
        errors.append("aucune décision de route testée")
    for node, _moment, choice, exits, recent in traffic.decisions:
        if len(exits) > 1 and recent and choice is recent[-1]:
            errors.append(f"les véhicules ne divergent pas à {node}")
            break
    if traffic.forced_divergences == 0:
        errors.append("aucune divergence forcée observée pendant la simulation")
    return errors


def check_collisions(network: RoadNetwork, seed: int) -> list[str]:
    """Fait rouler 10 véhicules 20 s avec chaque conduite (hasard, règle, appris) et vérifie
    que la circulation reste cohérente : pas de crash, collisions et trajets bien comptés."""
    errors = []
    for driving in DRIVINGS:
        policy, _used = make_policy(driving)
        traffic = Traffic(network, count=10, seed=seed, policy=policy)
        for _ in range(200):
            traffic.update(0.1)
        if traffic.collisions != len(traffic.collision_events):
            errors.append(f"{driving} : compteur de collisions incohérent")
        if any(duration <= 0 for duration in traffic.trip_times):
            errors.append(f"{driving} : trajet de durée nulle ou négative")
        for vehicle in traffic.get_moving():
            if vehicle.target is not None and not network.has_segment(vehicle.current,
                                                                      vehicle.target):
                errors.append(f"{driving} : véhicule {vehicle.number} hors des routes")
            if not 0 <= vehicle.progress < 1:
                errors.append(f"{driving} : véhicule {vehicle.number} progress {vehicle.progress}")
    return errors


def main() -> None:
    """Teste plusieurs tailles, seeds, la règle de circulation puis les collisions."""
    failures = 0
    for columns, rows in SIZES:
        for seed in range(SEEDS):
            network = RoadNetwork(columns, rows)
            generate_network(network, seed, roads=4, intersections=3)
            for error in check_network(network) + check_collisions(network, seed):
                print(f"[{columns}x{rows}] seed {seed}: {error}")
                failures += 1
    for error in check_divergence():
        print(f"[trafic] {error}")
        failures += 1
    print("OK" if failures == 0 else f"{failures} erreur(s)")


if __name__ == "__main__":
    main()
