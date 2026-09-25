"""Tests pytest : une règle du projet = un test. Lancer : .venv/bin/pytest"""

import pytest

from check import check_divergence, check_network
from display import CRASH_DURATION, get_recent_crashes
from generator import count_intersections, generate_network
from models import NodeType
from network import RoadNetwork
from policies import PACES, Policy, RandomPolicy, RulePolicy
from traffic import MAX_SPEED_FACTOR, MIN_SPEED_FACTOR, SPEED, Traffic

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


def test_generate_meme_seed_deux_fois_meme_reseau():
    network = build(seed=4821, intersections=4)
    first = snapshot(network)
    generate_network(network, 7, 4, 4)  # une autre seed entre les deux, comme avec Generate
    generate_network(network, 4821, 4, 4)
    assert snapshot(network) == first


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


def speeds(traffic: Traffic) -> list[float]:
    """Vitesse propre de chaque véhicule."""
    return [vehicle.base_speed for vehicle in traffic.vehicles]


def test_meme_seed_memes_vitesses():
    network = build(seed=1)
    assert speeds(Traffic(network, count=10, seed=5)) == speeds(Traffic(network, count=10, seed=5))


def test_vitesses_dans_l_intervalle_et_differentes():
    values = speeds(Traffic(build(seed=1), count=10, seed=5))
    assert all(SPEED * MIN_SPEED_FACTOR <= v <= SPEED * MAX_SPEED_FACTOR for v in values)
    assert len(set(values)) > 1


def test_vehicule_avance_a_sa_vitesse():
    traffic = Traffic(build(seed=1), count=1, seed=5)
    vehicle = traffic.vehicles[0]
    traffic.update(0.1)  # départ : choisit sa route
    traffic.update(0.1)  # roule
    assert vehicle.progress == pytest.approx(vehicle.speed * 0.1)


def hand_network(columns: int, rows: int, links: list, start: tuple, end: tuple) -> dict:
    """Réseau construit à la main. Renvoie {(x, y): node} pour poser les véhicules."""
    network = RoadNetwork(columns, rows)
    for (ax, ay), (bx, by) in links:
        network.create_segment(network.get_node(ax, ay), network.get_node(bx, by))
    network.get_node(*start).type = NodeType.START
    network.get_node(*end).type = NodeType.END
    return network, {(n.x, n.y): n for n in network.nodes}


def line_network():
    """Route droite START (0,0) -> (1,0) -> (2,0) -> END (3,0)."""
    return hand_network(4, 1, [((0, 0), (1, 0)), ((1, 0), (2, 0)), ((2, 0), (3, 0))],
                        (0, 0), (3, 0))


def merge_network():
    """Deux routes qui partent du START (0,1) et fusionnent en (2,1) avant le END (3,1)."""
    links = [((0, 1), (1, 0)), ((0, 1), (1, 2)), ((1, 0), (2, 1)), ((1, 2), (2, 1)),
             ((2, 1), (3, 1))]
    return hand_network(4, 3, links, (0, 1), (3, 1))


def place(vehicle, current, target, progress: float, speed: float) -> None:
    """Pose un véhicule sur un segment, déjà parti."""
    vehicle.departure = 0.0
    vehicle.current, vehicle.target = current, target
    vehicle.progress, vehicle.speed = progress, speed


def test_duree_d_un_trajet_start_end():
    network, _n = line_network()
    traffic = Traffic(network, count=1, seed=0)
    vehicle = traffic.vehicles[0]
    for _ in range(100):
        traffic.update(0.05)
    # 3 segments à sa vitesse propre, à quelques images près
    assert traffic.trip_times[0] == pytest.approx(3 / vehicle.base_speed, abs=4 * 0.05)


def test_rapide_derriere_lent_une_collision():
    network, n = line_network()
    traffic = Traffic(network, count=2, seed=0)
    slow, fast = traffic.vehicles
    place(slow, n[1, 0], n[2, 0], 0.5, speed=0.1)
    place(fast, n[1, 0], n[2, 0], 0.3, speed=1.5)
    for _ in range(10):
        traffic.update(0.05)
    assert traffic.collisions == 1


def test_vehicules_eloignes_aucune_collision():
    network, n = line_network()
    traffic = Traffic(network, count=2, seed=0)
    place(traffic.vehicles[0], n[1, 0], n[2, 0], 0.8, speed=1.0)
    place(traffic.vehicles[1], n[1, 0], n[2, 0], 0.1, speed=1.0)
    for _ in range(5):
        traffic.update(0.05)
    assert traffic.collisions == 0


def test_contact_qui_dure_compte_une_fois():
    network, n = line_network()
    traffic = Traffic(network, count=2, seed=0)
    a, b = traffic.vehicles
    place(a, n[1, 0], n[2, 0], 0.2, speed=1.0)
    place(b, n[1, 0], n[2, 0], 0.2, speed=1.0)
    for _ in range(5):
        traffic.update(0.05)
        assert (a, b) in traffic.contacts
    assert traffic.collisions == 1


def test_depassement_entre_deux_images():
    network, n = line_network()
    traffic = Traffic(network, count=2, seed=0)
    place(traffic.vehicles[0], n[1, 0], n[2, 0], 0.5, speed=0.0)
    place(traffic.vehicles[1], n[1, 0], n[2, 0], 0.3, speed=4.0)
    traffic.update(0)  # mémorise les positions : 0.2 d'écart, pas de contact
    traffic.update(0.1)  # le rapide saute de 0.3 à 0.7 : jamais à moins de MIN_GAP
    assert traffic.collisions == 1


def test_fusion_de_deux_routes():
    network, n = merge_network()
    traffic = Traffic(network, count=2, seed=0)
    place(traffic.vehicles[0], n[1, 0], n[2, 1], 0.9, speed=1.0)
    place(traffic.vehicles[1], n[1, 2], n[2, 1], 0.9, speed=1.0)
    traffic.update(0.05)
    assert traffic.collisions == 1
    _moment, a, b, _place = traffic.collision_events[0]
    assert (a.number, b.number) == (0, 1)


def test_pas_de_collision_autour_du_start():
    network, n = merge_network()
    traffic = Traffic(network, count=2, seed=0)
    place(traffic.vehicles[0], n[0, 1], n[1, 0], 0.02, speed=0.0)
    place(traffic.vehicles[1], n[0, 1], n[1, 2], 0.02, speed=0.0)
    traffic.update(0.05)
    assert traffic.collisions == 0


def paces_used(traffic: Traffic, steps: int = 200) -> set[float]:
    """Fait rouler le trafic et renvoie les allures vues (vitesse / vitesse propre)."""
    seen = set()
    for _ in range(steps):
        traffic.update(0.1)
        for vehicle in traffic.get_moving():
            seen.add(round(vehicle.speed / vehicle.base_speed, 6))
    return seen


def test_regle_par_defaut_a_allure_normale():
    traffic = Traffic(build(seed=1), count=6, seed=5)
    assert isinstance(traffic.policy, RulePolicy)
    assert paces_used(traffic) == {PACES["normal"]}


def test_hasard_utilise_toutes_les_allures():
    traffic = Traffic(build(seed=1), count=6, seed=5, policy=RandomPolicy())
    assert paces_used(traffic) == set(PACES.values())


def test_allure_choisie_appliquee():
    class AlwaysFast(Policy):
        def choose(self, traffic, vehicle, node, exits):
            return exits[0], "fast"

    traffic = Traffic(build(seed=1), count=1, seed=5, policy=AlwaysFast())
    vehicle = traffic.vehicles[0]
    traffic.update(0.1)
    assert vehicle.speed == pytest.approx(vehicle.base_speed * PACES["fast"])


def test_seules_les_collisions_recentes_sont_affichees():
    network, n = line_network()
    traffic = Traffic(network, count=2, seed=0)
    a, b = traffic.vehicles
    place_on = (n[1, 0], n[2, 0], 0.5)
    traffic.collision_events = [(0.0, a, b, place_on), (1.0, a, b, place_on)]
    traffic.time = 1.0 + CRASH_DURATION / 2
    crashes = get_recent_crashes(traffic)
    assert len(crashes) == 1  # celle de l'instant 0 est effacée
    assert crashes[0][2] == pytest.approx(0.5)  # à moitié effacée
