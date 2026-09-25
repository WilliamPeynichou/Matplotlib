"""Tests pytest de l'apprentissage (ML-5 et suivants). Lancer : .venv/bin/pytest"""

import random

import pytest

from check import SIZES, check_collisions
from evaluate import compare, evaluate
from learning import (
    ACTIONS,
    BUSY,
    DANGER,
    FREE,
    NO_EXIT,
    TABLE_FILE,
    QAgent,
    get_state,
    make_policy,
)
from policies import PACES, RandomPolicy, RulePolicy
from test_roadnetwork import build, hand_network, line_network, place
from traffic import SPEED, Traffic
from train import FIRST_NETWORK_SEED, make_episodes, moving_average, train


def fork_network():
    """N (1,1) a deux sorties : tout droit vers (2,1) et en montant vers (2,2).
    Une autre route (1,0) -> (2,1) rejoint la sortie tout droit (fusion)."""
    links = [((0, 1), (1, 1)), ((0, 1), (1, 0)),
             ((1, 1), (2, 1)), ((1, 1), (2, 2)), ((1, 0), (2, 1)),
             ((2, 1), (3, 1)), ((2, 2), (3, 1))]
    return hand_network(4, 3, links, (0, 1), (3, 1))


def state_at_fork(setup=None, base_speed: float = SPEED):
    """État du véhicule 0 arrêté sur N ; `setup(other, n)` place le véhicule 1."""
    network, n = fork_network()
    traffic = Traffic(network, count=2, seed=0)
    me, other = traffic.vehicles
    place(me, n[1, 1], n[1, 1], 0.0, speed=base_speed)
    me.base_speed = base_speed
    if setup is None:
        other.departure = 99.0  # pas encore parti
    else:
        setup(other, n)
    node = n[1, 1]
    return get_state(traffic, me, node, traffic.get_exits(node))


def test_etat_sorties_libres():
    assert state_at_fork() == (NO_EXIT, FREE, FREE, 0, 0)


def test_etat_vehicule_devant_loin():
    state = state_at_fork(lambda other, n: place(other, n[1, 1], n[2, 1], 0.7, speed=SPEED))
    assert state[:3] == (NO_EXIT, BUSY, FREE)


def test_etat_vehicule_devant_proche():
    state = state_at_fork(lambda other, n: place(other, n[1, 1], n[2, 2], 0.1, speed=SPEED))
    assert state[:3] == (NO_EXIT, FREE, DANGER)


def test_etat_fusion_en_meme_temps():
    # L'autre part du début de sa route à la même vitesse : arrivée en même temps en (2,1).
    state = state_at_fork(lambda other, n: place(other, n[1, 0], n[2, 1], 0.0, speed=SPEED))
    assert state[:3] == (NO_EXIT, DANGER, FREE)


def test_etat_fusion_decalee():
    # L'autre arrive presque : il sera passé bien avant nous.
    state = state_at_fork(lambda other, n: place(other, n[1, 0], n[2, 1], 0.9, speed=SPEED))
    assert state[:3] == (NO_EXIT, BUSY, FREE)


def test_etat_vehicule_juste_derriere():
    state = state_at_fork(lambda other, n: place(other, n[0, 1], n[1, 1], 0.8, speed=SPEED))
    assert state[4] == 1


def test_etat_vehicule_derriere_mais_loin():
    state = state_at_fork(lambda other, n: place(other, n[0, 1], n[1, 1], 0.2, speed=SPEED))
    assert state[4] == 0


@pytest.mark.parametrize("factor, fast", [(0.8, 0), (1.2, 1)])
def test_etat_vitesse_propre(factor, fast):
    assert state_at_fork(base_speed=SPEED * factor)[3] == fast


def alone_at_fork():
    """Un seul véhicule, arrêté sur N (1,1), vitesse moyenne. Son état : (0, 1, 1, 0, 0)."""
    network, n = fork_network()
    traffic = Traffic(network, count=1, seed=0)
    vehicle = traffic.vehicles[0]
    place(vehicle, n[1, 1], n[1, 1], 0.0, speed=SPEED)
    vehicle.base_speed = SPEED
    return traffic, vehicle, n


def test_mise_a_jour_q_en_fin_de_trajet():
    traffic, vehicle, _n = alone_at_fork()
    agent = QAgent(learning=True)
    state = (NO_EXIT, FREE, FREE, 0, 0)
    agent.memory[vehicle] = [state, 4, 0.0, 0.0]  # action 4 choisie à l'instant 0
    traffic.time = 2.0
    agent.on_collision(traffic, vehicle)  # -10
    agent.on_arrival(traffic, vehicle)  # +1, et 2 s de route : -0.2 ; pas de futur
    assert agent.q[state][4] == pytest.approx(0.1 * (-10 + 1 - 0.2))  # -0.92
    assert vehicle not in agent.memory


def test_mise_a_jour_q_avec_le_futur_et_meilleure_action():
    traffic, vehicle, n = alone_at_fork()
    node = n[1, 1]
    before, now = (FREE, FREE, FREE, 0, 0), (NO_EXIT, FREE, FREE, 0, 0)
    best = ACTIONS.index((2, "fast"))  # monter, rapide
    agent = QAgent(learning=True)
    agent.q[now] = [0.0] * len(ACTIONS)
    agent.q[now][best] = 5.0
    agent.q[now][ACTIONS.index((0, "fast"))] = 99.0  # descendre : pas de sortie, interdit
    agent.memory[vehicle] = [before, 0, 0.0, 0.0]
    traffic.time = 1.0
    target, pace = agent.choose(traffic, vehicle, node, traffic.get_exits(node))
    assert agent.q[before][0] == pytest.approx(0.1 * (-0.1 * 1.0 + 0.9 * 5.0))  # 0.44
    assert (target, pace) == (n[2, 2], "fast")
    assert agent.memory[vehicle][:2] == [now, best]


def test_exploration_seulement_vers_des_sorties_existantes():
    traffic, vehicle, n = alone_at_fork()
    node = n[1, 1]
    exits = traffic.get_exits(node)
    agent = QAgent(learning=True, epsilon=1.0, seed=3)
    seen = {agent.choose(traffic, vehicle, node, exits) for _ in range(200)}
    assert len(seen) == 2 * len(PACES)  # 2 sorties x 3 allures, jamais « descendre »


def test_conduite_apprise_ne_change_pas_la_table():
    traffic, vehicle, n = alone_at_fork()
    agent = QAgent()
    agent.q = {(NO_EXIT, FREE, FREE, 0, 0): [1.0] * len(ACTIONS)}
    before = {state: values.copy() for state, values in agent.q.items()}
    for _ in range(5):
        agent.choose(traffic, vehicle, n[1, 1], traffic.get_exits(n[1, 1]))
    assert agent.q == before and agent.memory == {}


def test_sauvegarde_puis_lecture_meme_table(tmp_path):
    agent = QAgent()
    agent.q = {(NO_EXIT, FREE, DANGER, 1, 0): [i / 4 for i in range(9)],
               (FREE, BUSY, NO_EXIT, 0, 1): [-1.5] * 9}
    path = tmp_path / "q_table.json"
    agent.save(path)
    loaded = QAgent.load(path)
    assert loaded.q == agent.q
    assert loaded.learning is False


def test_trafic_previent_la_conduite():
    class Spy(RulePolicy):
        def __init__(self):
            self.collided, self.arrived = [], []

        def on_collision(self, traffic, vehicle):
            self.collided.append(vehicle.number)

        def on_arrival(self, traffic, vehicle):
            self.arrived.append(vehicle.number)

    network, n = line_network()
    spy = Spy()
    traffic = Traffic(network, count=2, seed=0, policy=spy)
    place(traffic.vehicles[0], n[1, 0], n[2, 0], 0.5, speed=0.1)
    place(traffic.vehicles[1], n[1, 0], n[2, 0], 0.3, speed=1.5)
    for _ in range(40):  # 2 s : le rapide heurte le lent, le dépasse et arrive au END
        traffic.update(0.05)
    assert spy.collided == [0, 1]
    assert spy.arrived == [1]


def test_entrainement_reproductible():
    agent_a, curve_a = train(20)
    agent_b, curve_b = train(20)
    assert agent_a.q and agent_a.q == agent_b.q
    assert curve_a == curve_b


def test_seeds_d_entrainement_jamais_celles_de_l_evaluation():
    episodes = make_episodes(50, random.Random(1))
    assert all(seed >= FIRST_NETWORK_SEED for seed, *_ in episodes)


def test_moyenne_glissante():
    assert moving_average([2, 4, 6, 8], window=2) == [2, 3, 5, 7]


def test_table_livree_se_charge():
    agent = QAgent.load(TABLE_FILE)
    assert len(agent.q) > 200
    assert all(len(values) == len(ACTIONS) for values in agent.q.values())


@pytest.fixture(scope="module")
def results():
    """Comparaison des trois conduites sur les réseaux de test (calculée une fois)."""
    return compare()


def test_evaluation_reproductible(results):
    assert evaluate(RulePolicy()) == results["règle actuelle"]


def test_appris_moins_de_collisions_que_le_hasard(results):
    assert results["appris"]["collisions"] < results["hasard"]["collisions"]


@pytest.mark.parametrize("driving, kind", [("random", RandomPolicy), ("rule", RulePolicy),
                                           ("learned", QAgent)])
def test_conduite_par_son_nom(driving, kind):
    policy, used = make_policy(driving)
    assert isinstance(policy, kind) and used == driving


def test_table_absente_retour_a_la_regle(tmp_path):
    policy, used = make_policy("learned", tmp_path / "absente.json")
    assert isinstance(policy, RulePolicy) and used == "rule"


@pytest.mark.parametrize("content", [
    "",  # fichier vide
    "pas du json",
    "[1, 2, 3]",  # pas un objet
    '{"0,1,1": [0, 0, 0, 0, 0, 0, 0, 0, 0]}',  # état trop court
    '{"x,1,1,0,0": [0, 0, 0, 0, 0, 0, 0, 0, 0]}',  # état pas en nombres
    '{"0,1,1,0,0": [1, 2]}',  # pas 9 valeurs
    '{"0,1,1,0,0": ["a", 0, 0, 0, 0, 0, 0, 0, 0]}',  # valeur pas un nombre
])
def test_table_abimee_retour_a_la_regle(tmp_path, content):
    path = tmp_path / "q_table.json"
    path.write_text(content, encoding="utf-8")
    policy, used = make_policy("learned", path)
    assert isinstance(policy, RulePolicy) and used == "rule"


def test_appris_moins_de_collisions_que_la_regle(results):
    # Protège la table livrée : un réentraînement moins bon que la règle fait échouer ce test.
    assert results["appris"]["collisions"] < results["règle actuelle"]["collisions"]


@pytest.mark.parametrize("columns, rows", SIZES)
@pytest.mark.parametrize("seed", range(5))
def test_circulation_coherente_avec_les_trois_conduites(columns, rows, seed):
    network = build(columns, rows, seed=seed, intersections=3)
    assert check_collisions(network, seed) == []
