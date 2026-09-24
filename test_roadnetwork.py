"""Tests pytest : une règle du projet = un test. Lancer : .venv/bin/pytest"""

import pytest

from check import check_divergence, check_network
from generator import count_intersections, generate_network
from models import NodeType
from network import RoadNetwork

SEEDS = range(20)


def build(columns=15, rows=9, seed=1, roads=4, intersections=None) -> RoadNetwork:
    """Crée et génère un réseau."""
    network = RoadNetwork(columns, rows)
    generate_network(network, seed, roads, intersections)
    return network


def snapshot(network: RoadNetwork) -> list:
    """Liste des segments sous forme de coordonnées (pour comparer deux réseaux)."""
    return [((s.start.x, s.start.y), (s.end.x, s.end.y)) for s in network.segments]


@pytest.mark.parametrize("seed", SEEDS)
def test_reseau_respecte_toutes_les_regles(seed):
    assert check_network(build(seed=seed, intersections=3)) == []


@pytest.mark.parametrize("seed", SEEDS)
def test_toutes_les_routes_vont_au_end(seed):
    network = build(seed=seed, roads=8)
    exits = {id(s.start) for s in network.segments}
    for node in network.nodes:
        if node.type not in (NodeType.UNUSED, NodeType.END):
            assert id(node) in exits, f"cul-de-sac en ({node.x}, {node.y})"


def test_start_au_milieu_de_la_premiere_colonne():
    network = build(rows=9)
    assert network.get_start() is network.get_node(0, 4)


def test_end_dans_la_derniere_colonne():
    network = build(columns=15)
    ends = [n for n in network.nodes if n.type is NodeType.END]
    assert len(ends) == 1 and ends[0].x == 14


def test_meme_seed_meme_reseau():
    assert snapshot(build(seed=42, intersections=4)) == snapshot(build(seed=42, intersections=4))


def test_seeds_differentes_reseaux_differents():
    assert snapshot(build(seed=1)) != snapshot(build(seed=2))


def test_segment_en_double_refuse():
    network = RoadNetwork(3, 3)
    a, b = network.get_node(0, 1), network.get_node(1, 1)
    assert network.create_segment(a, b) is not None
    assert network.create_segment(a, b) is None
    assert len(network.segments) == 1


def test_intersection_des_3_segments():
    network = RoadNetwork(3, 3)
    center = network.get_node(1, 1)
    for y in range(3):
        network.create_segment(center, network.get_node(2, y))
    assert center.type is NodeType.INTERSECTION


def test_nombre_d_intersections_demande_atteint():
    network = RoadNetwork(15, 9)
    assert generate_network(network, seed=3, roads=3, intersections=2) == 2
    assert count_intersections(network) == 2


@pytest.mark.parametrize("columns, rows", [(2, 1), (2, 2), (3, 1), (1 + 1, 9), (30, 20)])
@pytest.mark.parametrize("roads", [0, 1, 10])
def test_cas_limites_sans_crash(columns, rows, roads):
    assert check_network(build(columns, rows, roads=roads, intersections=15)) == []


@pytest.mark.parametrize("columns, rows", [(0, 5), (1, 5), (5, 0), (-3, 4), (2.5, 3)])
def test_grille_invalide_message_clair(columns, rows):
    with pytest.raises(ValueError, match="grille invalide"):
        RoadNetwork(columns, rows)


def test_vehicules_divergent_dans_la_fenetre_de_2_secondes():
    assert check_divergence() == []


def test_longueur_plus_court_chemin():
    network = build(seed=1, intersections=3)
    assert network.get_shortest_path_length() == len(network.get_shortest_path()) - 1


def test_longueur_plus_court_chemin_sans_reseau():
    network = RoadNetwork(3, 3)
    assert network.get_shortest_path_length() == 0
