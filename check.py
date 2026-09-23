"""Vérifie automatiquement les règles de génération (feature 7)."""

from generator import generate_network
from models import NodeType
from network import RoadNetwork

SEEDS = 100
SIZES = [(15, 9), (3, 3), (2, 1), (30, 20)]


def expected_type(node) -> NodeType:
    """Type attendu d'un node (hors START / END) selon son nombre de segments."""
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

    seen = set()
    for segment in network.segments:
        a, b = segment.start, segment.end
        if not network.is_inside(a.x, a.y) or not network.is_inside(b.x, b.y):
            errors.append(f"{segment} hors grille")
        key = frozenset([(a.x, a.y), (b.x, b.y)])
        if key in seen:
            errors.append(f"{segment} en double")
        seen.add(key)

    start = network.get_node(0, network.rows // 2)
    if start.type is not NodeType.START:
        errors.append("START n'est pas au milieu de la 1re colonne")
    if ends and ends[0].x != network.columns - 1:
        errors.append("END n'est pas dans la dernière colonne")

    for segment in network.segments:
        a, b = segment.start, segment.end
        if abs(a.x - b.x) != 1 or abs(a.y - b.y) > 1:
            errors.append(f"{segment} n'est pas un déplacement autorisé")
        if a.y != b.y and network.has_segment(network.get_node(a.x, b.y), network.get_node(b.x, a.y)):
            errors.append(f"{segment} croise une diagonale")

    path = network.get_shortest_path()
    if not path or path[0].type is not NodeType.START or path[-1].type is not NodeType.END:
        errors.append("plus court chemin START -> END introuvable")
    elif len(path) != network.columns:
        errors.append(f"plus court chemin de {len(path)} nodes au lieu de {network.columns}")
    elif any(not network.has_segment(a, b) for a, b in zip(path, path[1:])):
        errors.append("plus court chemin passe par un lien inexistant")

    for node in network.nodes:
        if node.type in (NodeType.START, NodeType.END):
            if not node.segments:
                errors.append(f"{node} n'est relié à rien")
        elif node.type is not expected_type(node):
            errors.append(f"{node} devrait être {expected_type(node).name}")
    return errors


def main() -> None:
    """Génère des réseaux sur plusieurs tailles et affiche les seeds en erreur."""
    failures = 0
    for columns, rows in SIZES:
        for seed in range(SEEDS):
            network = RoadNetwork(columns, rows)
            generate_network(network, seed)
            for error in check_network(network):
                print(f"[{columns}x{rows}] seed {seed} : {error}")
                failures += 1
    print("OK" if failures == 0 else f"{failures} erreur(s)")


if __name__ == "__main__":
    main()
