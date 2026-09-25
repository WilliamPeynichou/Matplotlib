"""Tests pytest : une règle du projet = un test. Lancer : .venv/bin/pytest"""

import matplotlib.pyplot as plt
import pytest

from check import check_divergence, check_network
from display import NetworkView
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


def build_view(network: RoadNetwork, settings: dict | None = None) -> NetworkView:
    """Construit une fenêtre pour ce réseau, avec Randomize décoché."""
    settings = settings or {"roads": 4, "intersections": 4, "vehicles": 0}

    def generate(seed, roads, intersections):
        return generate_network(network, seed, roads, intersections)

    view = NetworkView(network, 1, settings, generate, lambda: 0, 99999)
    view.seed_controls.randomize_var.set(False)  # Generate garde la seed du champ
    return view


def submit_seed_text(view: NetworkView, text: str) -> None:
    """Simule une saisie suivie d'Entrée dans le champ Seed."""
    view.seed_controls.seed_var.set(text)
    view.on_seed_entry_submit()


def build_view_from_seed_box(seed_text: str) -> RoadNetwork:
    """Construit une fenêtre, décoche Randomize puis saisit une seed dans le champ Seed."""
    network = RoadNetwork(15, 9)
    view = build_view(network)
    submit_seed_text(view, seed_text)
    plt.close(view.fig)
    return network


def test_meme_seed_saisie_deux_fois_meme_reseau():
    assert (snapshot(build_view_from_seed_box("777"))
            == snapshot(build_view_from_seed_box("777")))


def test_seed_invalide_dans_le_champ_ne_plante_pas():
    network = RoadNetwork(15, 9)
    generate_network(network, seed=1, roads=4, intersections=4)
    before = snapshot(network)

    view = build_view(network)
    submit_seed_text(view, "pas un entier")
    assert "invalide" in view.info.get_text()
    assert snapshot(network) == before
    plt.close(view.fig)


def test_generate_lit_la_seed_tapee_sans_appuyer_sur_entree():
    """Generate doit utiliser la seed tapée même sans valider avec Entrée (Randomize décoché)."""
    network = RoadNetwork(15, 9)
    view = build_view(network)
    view.seed_controls.seed_var.set("777")  # simule une frappe, sans Entrée
    view.on_generate_click()
    assert view.seed == 777
    assert snapshot(network) == snapshot(build_view_from_seed_box("777"))
    plt.close(view.fig)


def test_generate_avec_randomize_ignore_le_champ_seed():
    network = RoadNetwork(15, 9)
    settings = {"roads": 4, "intersections": 4, "vehicles": 0}

    def generate(seed, roads, intersections):
        return generate_network(network, seed, roads, intersections)

    seeds = iter([111, 222])
    view = NetworkView(network, 1, settings, generate, lambda: next(seeds), 99999)
    view.on_generate_click()  # Randomize coché par défaut
    assert view.seed == 111
    assert view.seed_controls.get_text() == "111"
    plt.close(view.fig)


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
