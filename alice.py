"""L'expérience Alice : UNE seule voiture change de conduite, les 9 autres gardent la Règle.

Lancer : .venv/bin/python alice.py            (entraîne le RL d'Alice puis compare)
         .venv/bin/python alice.py 300        (moins d'épisodes d'entraînement RL)
Prérequis : tree_model.py lancé une fois (sinon l'arbre est remplacé par la règle).
Produit : q_alice.json (la table Q d'Alice) et docs/images/alice.png (la comparaison).

Pourquoi une seule voiture ? Si tout le monde change en même temps, on ne sait plus
si c'est la conduite qui est meilleure ou le trafic qui a changé. Ici le trafic autour
d'Alice est toujours le même (Règle) : seule sa conduite change.

Conduites comparées pour Alice :
- Hasard  : sortie et allure au hasard (le « plancher »)
- Règle   : la règle de divergence (comme les autres)
- Arbre   : apprentissage SUPERVISÉ (tree_model.py)
- RL      : apprentissage PAR RENFORCEMENT (Q-learning, entraîné ici, sur Alice seule)
"""

import random
import sys
from pathlib import Path

from learning import STATE_SIZE, QAgent, get_length_classes, get_state
from policies import RandomPolicy, RulePolicy
from traffic import FUEL
from tree_model import EPISODE_TIME, FIRST_SEED, make_tree_policy, run_circuit

ROOT = Path(__file__).parent
ALICE = 0  # numéro de la voiture étudiée (0 = Alice)
Q_ALICE_FILE = ROOT / "q_alice.json"
RESULT_IMAGE = ROOT / "docs" / "images" / "alice.png"
RL_EPISODES = 3000
FUEL_COST = 0.15  # récompense perdue par unité de carburant (le « prix du litre »)
MIN_EPSILON = 0.05
TEST_SEEDS = range(30)  # circuits de test, jamais vus à l'entraînement (seeds < FIRST_SEED)


class AliceAgent(QAgent):
    """Le Q-learning d'Alice. Différence avec QAgent : Alice roule aux vraies distances
    (un tronçon long prend plus de temps), donc elle doit VOIR la longueur de chaque sortie.
    État = 5 infos habituelles + 3 longueurs (descendre, tout droit, monter) = 8 nombres."""

    state_size = STATE_SIZE + 3

    def get_state(self, traffic, vehicle, node, exits):
        """État habituel + classe de longueur de chaque sortie."""
        return (*get_state(traffic, vehicle, node, exits),
                *get_length_classes(traffic, node, exits))

    def choose(self, traffic, vehicle, node, exits):
        """Comme QAgent, puis on facture le carburant du tronçon choisi :
        récompense -= FUEL_COST x consommation(allure) x longueur. Rapide = 2x plus cher."""
        target, pace = super().choose(traffic, vehicle, node, exits)
        if self.learning and vehicle in self.memory:
            length = traffic.network.get_length(node, target)
            self.memory[vehicle][3] -= FUEL_COST * FUEL[pace] * length
        return target, pace


def train_alice(episodes: int = RL_EPISODES, seed: int = 1) -> QAgent:
    """Q-learning sur Alice seule. Au début elle explore (epsilon = 1 : tout au hasard),
    puis elle utilise de plus en plus ce qu'elle a appris (epsilon -> 0.05)."""
    agent = AliceAgent(learning=True, seed=seed)
    rng = random.Random(seed)
    for index in range(episodes):
        agent.epsilon = max(MIN_EPSILON, 1 - index / (0.8 * episodes))
        run_circuit(FIRST_SEED + rng.randrange(100_000), RulePolicy(), special={ALICE: agent})
        agent.forget()
        if (index + 1) % max(1, episodes // 5) == 0:
            print(f"   épisode {index + 1}/{episodes}  ·  epsilon {agent.epsilon:.2f}  ·  "
                  f"états connus {len(agent.q)}")
    agent.learning = False  # fini d'apprendre : maintenant elle applique
    agent.epsilon = 0.0
    return agent


def make_alice_policies(q_path: Path = Q_ALICE_FILE) -> dict:
    """Les 4 conduites possibles pour Alice (nom -> fabrique). La table RL est relue."""
    def rl():
        try:
            return AliceAgent.load(q_path)
        except (OSError, ValueError):
            return RulePolicy()
    return {"Hasard": RandomPolicy, "Règle": RulePolicy, "Arbre": make_tree_policy, "RL": rl}


def measure(make_policy, seeds=TEST_SEEDS) -> dict:
    """Moyennes sur les circuits de test : collisions/min d'Alice, ses tours, et les
    collisions/min des autres (pour voir si Alice les gêne)."""
    alice_collisions = alice_laps = others = fuel = 0.0
    paces = {"slow": 0, "normal": 0, "fast": 0}
    for seed in seeds:
        traffic = run_circuit(seed, RulePolicy(), special={ALICE: make_policy()})
        alice = traffic.vehicles[ALICE]
        alice_collisions += alice.collisions
        alice_laps += alice.laps
        fuel += alice.fuel / max(alice.distance, 1e-9)  # carburant par unité de distance
        for pace, count in alice.pace_counts.items():
            paces[pace] += count
        rest = traffic.vehicles[:ALICE] + traffic.vehicles[ALICE + 1:]
        others += sum(v.collisions for v in rest) / len(rest)
    minutes = len(seeds) * EPISODE_TIME / 60
    choices = sum(paces.values()) or 1
    return {"alice": alice_collisions / minutes, "tours": alice_laps / len(seeds),
            "autres": others / minutes, "carburant": fuel / len(seeds),
            "allures": {pace: count / choices for pace, count in paces.items()}}


def draw(results: dict, path: Path = RESULT_IMAGE) -> None:
    """Deux barres par conduite : collisions/min d'Alice et tours par épisode."""
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    figure = Figure(figsize=(14, 4))
    FigureCanvasAgg(figure)
    left, right, fuel = figure.subplots(1, 3)
    names = list(results)
    colors = ["#b5b4ae", "#8a8984", "#2e9e6a", "#2a78d6"]
    left.bar(names, [results[n]["alice"] for n in names], color=colors)
    left.set_title("Collisions d'Alice par minute (plus bas = mieux)")
    right.bar(names, [results[n]["tours"] for n in names], color=colors)
    right.set_title("Tours d'Alice par épisode de 60 s (plus haut = mieux)")
    fuel.bar(names, [results[n]["carburant"] for n in names], color=colors)
    fuel.set_title("Carburant d'Alice par unité de distance (plus bas = mieux)")
    figure.tight_layout()
    figure.savefig(path, dpi=90)


def main() -> None:
    episodes = int(sys.argv[1]) if len(sys.argv) > 1 else RL_EPISODES
    print(f"1. Entraînement RL d'Alice ({episodes} épisodes, les autres roulent à la Règle)…")
    train_alice(episodes).save(Q_ALICE_FILE)
    print(f"   table -> {Q_ALICE_FILE.name}")
    print(f"2. Comparaison sur {len(TEST_SEEDS)} circuits jamais vus…")
    results = {name: measure(make) for name, make in make_alice_policies().items()}
    print(f"   {'Conduite':<8} {'Alice coll/min':>15} {'Alice tours':>12} {'autres coll/min':>16}"
          f" {'carburant/dist':>15}   allures d'Alice (lent / normal / rapide)")
    for name, r in results.items():
        slow, normal, fast = (r["allures"][p] for p in ("slow", "normal", "fast"))
        print(f"   {name:<8} {r['alice']:>15.2f} {r['tours']:>12.2f} {r['autres']:>16.2f}"
              f" {r['carburant']:>15.2f}   {slow:>5.0%} / {normal:>4.0%} / {fast:>4.0%}")
    draw(results)
    print(f"3. Graphique -> {RESULT_IMAGE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
