"""Tests de l'expérience Alice : conduite par voiture, arbre (supervisé), RL sur Alice seule."""

import pytest

from alice import ALICE, measure, train_alice
from circuit import Circuit
from learning import QAgent
from policies import RulePolicy
from traffic import Traffic
from tree_model import FEATURES, RecorderPolicy, TreePolicy, collect, run_circuit, train


@pytest.fixture(scope="module")
def rows():
    """Petit jeu d'exemples (3 circuits) : suffit pour tester, rapide."""
    return collect(3)


def test_seule_alice_a_une_conduite_speciale():
    circuit = Circuit(10, 5)
    circuit.generate(1, 3, 6)
    special = RulePolicy()
    traffic = Traffic(circuit, 4, seed=1, policy=RulePolicy(), special={ALICE: special})
    assert traffic.policy_of(traffic.vehicles[0]) is special
    assert all(traffic.policy_of(v) is traffic.policy for v in traffic.vehicles[1:])


def test_exemples_bien_formes(rows):
    assert len(rows) > 100
    for row in rows:
        assert len(row) == len(FEATURES) + 1  # features + label
        assert row[-1] in (0, 1)
        assert 0 <= row[FEATURES.index("direction")] <= 2
        assert 0 <= row[FEATURES.index("allure")] <= 2


def test_il_y_a_des_collisions_dans_les_exemples(rows):
    labels = [row[-1] for row in rows]
    assert 0 < sum(labels) < len(labels)  # ni aucune, ni toutes : il y a quelque chose à apprendre


def test_collision_marque_la_decision_en_cours():
    recorder = RecorderPolicy()
    recorder.pending["voiture"] = [1, 1, 1, 0, 0, 1, 1, 0]
    recorder.on_collision(None, "voiture")
    recorder.on_arrival(None, "voiture")
    assert recorder.rows == [[1, 1, 1, 0, 0, 1, 1, 1]]


def test_arbre_fait_mieux_que_le_hasard_sur_les_collisions(rows):
    model, report = train(rows)
    assert report["collisions_detectees"] > 0.5  # au hasard, on en détecterait ~50 %
    assert model.get_depth() <= 4  # l'arbre reste lisible


def test_tree_policy_choisit_une_sortie_valide(rows):
    model, _ = train(rows)
    traffic = run_circuit(2, RulePolicy(), special={ALICE: TreePolicy(model)})
    assert traffic.vehicles[ALICE].laps >= 1  # Alice roule et termine des tours


def test_rl_alice_apprend_quelque_chose():
    agent = train_alice(episodes=20)
    assert isinstance(agent, QAgent)
    assert len(agent.q) > 0 and not agent.learning


def test_mesure_meme_seed_meme_resultat():
    assert measure(RulePolicy, seeds=[3]) == measure(RulePolicy, seeds=[3])


def test_troncon_long_prend_plus_de_temps_pour_alice():
    circuit = Circuit(10, 5)
    circuit.generate(1, 3, 6)
    traffic = Traffic(circuit, 2, seed=1, special={ALICE: RulePolicy()})
    alice, bruno = traffic.vehicles
    assert alice.distance_aware and not bruno.distance_aware
    frame = circuit.frames[0]
    short = (frame.get_node(2, 2), frame.get_node(3, 2))
    long = (frame.get_node(2, 3), frame.get_node(3, 4))  # diagonale côté extérieur de l'arc
    assert circuit.get_length(*long) > circuit.get_length(*short)
    for vehicle in (alice, bruno):
        vehicle.current, vehicle.target, vehicle.progress, vehicle.speed = *long, 0.0, 1.0
    alice.length = traffic.get_length(alice)
    traffic.time = 10
    traffic.update(0.1)
    assert alice.progress < bruno.progress  # même vitesse, mais Alice paie la longueur


def test_alice_voit_la_longueur_des_sorties():
    from alice import AliceAgent
    circuit = Circuit(10, 5)
    circuit.generate(1, 3, 6)
    traffic = Traffic(circuit, 1, seed=1)
    node = circuit.get_start()
    exits = traffic.get_exits(node)
    state = AliceAgent().get_state(traffic, traffic.vehicles[0], node, exits)
    assert len(state) == AliceAgent.state_size == 8
    assert all(value in (0, 1, 2, 3) for value in state[5:])


def test_les_autres_gardent_les_memes_regles():
    circuit = Circuit(10, 5)
    circuit.generate(1, 3, 6)
    traffic = Traffic(circuit, 5, seed=1)
    for _ in range(100):
        traffic.update(0.1)
    assert all(not v.distance_aware and v.length == 1.0 for v in traffic.vehicles)
