"""Tests du circuit (4 cadres en boucle) et des véhicules nominatifs."""

import pytest

from check import check_network
from circuit import FRAMES, Circuit
from models import NodeType
from traffic import NAMES, Traffic, make_name

SEEDS = range(15)


def build(seed=1, roads=3, intersections=6) -> Circuit:
    """Circuit 10 x 5 généré."""
    circuit = Circuit(10, 5)
    circuit.generate(seed, roads, intersections)
    return circuit


@pytest.mark.parametrize("seed", SEEDS)
def test_chaque_cadre_respecte_les_regles(seed):
    for frame in build(seed).frames:
        assert check_network(frame) == []


@pytest.mark.parametrize("seed", SEEDS)
def test_start_et_end_au_milieu_du_cadre(seed):
    for frame in build(seed).frames:
        assert frame.get_start() is frame.get_node(0, 2)
        end = [n for n in frame.nodes if n.type is NodeType.END]
        assert end == [frame.get_node(9, 2)]


def test_jonctions_au_meme_endroit_a_l_ecran():
    circuit = build()
    for i, frame in enumerate(circuit.frames):
        end = frame.get_node(9, 2)
        start = circuit.frames[(i + 1) % FRAMES].get_node(0, 2)
        ex, ey = circuit.to_screen(i, end.x, end.y)
        sx, sy = circuit.to_screen((i + 1) % FRAMES, start.x, start.y)
        assert (ex, ey) == pytest.approx((sx, sy))


def test_le_circuit_boucle():
    circuit = build()
    node = circuit.get_start()
    for _ in range(FRAMES):
        end = next(n for n in circuit.frames[node.frame].nodes if n.type is NodeType.END)
        node = circuit.get_next_start(end)
    assert node is circuit.get_start()


def test_meme_seed_meme_circuit():
    def snapshot(c):
        return [(s.start.frame, s.start.x, s.start.y, s.end.x, s.end.y) for s in c.segments]
    assert snapshot(build(42)) == snapshot(build(42))


def test_cadre_trop_petit_message_clair():
    with pytest.raises(ValueError, match="cadre invalide"):
        Circuit(2, 5)


def test_prenoms_uniques():
    names = [make_name(i) for i in range(3 * len(NAMES))]
    assert len(set(names)) == len(names)
    assert names[0] == "Alice" and names[len(NAMES)] == "Alice 2"


def test_les_vehicules_font_des_tours():
    circuit = build()
    traffic = Traffic(circuit, 5, seed=3)
    for _ in range(1200):
        traffic.update(0.05)
    assert all(v.laps >= 1 for v in traffic.vehicles)
    assert all(v.best_lap > 0 for v in traffic.vehicles)
    ranking = traffic.get_ranking()
    assert ranking[0].laps >= ranking[-1].laps


def test_vehicules_passent_par_les_4_cadres():
    circuit = build()
    traffic = Traffic(circuit, 1, seed=3)
    frames = set()
    for _ in range(400):
        traffic.update(0.05)
        frames.add(traffic.vehicles[0].current.frame)
    assert frames == set(range(FRAMES))
