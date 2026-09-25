"""Entraînement sans fenêtre (ML-7) : les véhicules apprennent à ne pas se heurter.

Lancer : .venv/bin/python train.py         (3000 épisodes, ~30 s)
         .venv/bin/python train.py 500     (plus court, moins bien entraîné)
Produit q_table.json (la conduite apprise) et docs/images/apprentissage.png (la courbe).

Un épisode = un réseau au hasard, 6 à 15 véhicules, 60 s simulées. Au début, les véhicules
choisissent surtout au hasard (exploration, epsilon = 1) ; à la fin, surtout ce qu'ils ont
appris (epsilon = 0.05). Même TRAINING_SEED = même table.
"""

import random
import sys
from pathlib import Path

from matplotlib.figure import Figure

from generator import generate_network
from learning import TABLE_FILE, QAgent
from network import RoadNetwork
from policies import Policy, RandomPolicy, RulePolicy
from traffic import Traffic

EPISODES = 3000
TRAINING_SEED = 1
FIRST_NETWORK_SEED = 10_000  # les seeds 0 à 9999 restent pour l'évaluation (ML-8)
COLUMNS, ROWS = 15, 9  # comme main.py
ROADS = (3, 6)  # bornes du tirage au hasard, incluses
INTERSECTIONS = (2, 6)
VEHICLES = (6, 15)
EPISODE_TIME = 60.0  # secondes simulées
DT = 0.1  # pas de simulation fixe (secondes)
MIN_EPSILON = 0.05
EXPLORATION_SHARE = 0.8  # epsilon descend de 1 à MIN_EPSILON sur 80 % des épisodes
REFERENCE_EPISODES = 200  # épisodes rejoués avec la règle et le hasard, pour comparer
AVERAGE_WINDOW = 100  # épisodes par point de la moyenne glissante
CURVE_FILE = Path(__file__).parent / "docs" / "images" / "apprentissage.png"

SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT_MUTED = "#52514e"
GRID = "#e4e3df"
LEARNED_COLOR = "#2a78d6"
REFERENCE_COLOR = "#8a8984"


def make_episodes(count: int, rng: random.Random) -> list[tuple[int, int, int, int]]:
    """Réglages de chaque épisode : (seed du réseau, routes, intersections, véhicules)."""
    return [(FIRST_NETWORK_SEED + i, rng.randint(*ROADS), rng.randint(*INTERSECTIONS),
             rng.randint(*VEHICLES)) for i in range(count)]


def simulate(policy: Policy, seed: int, roads: int, intersections: int,
             vehicles: int) -> Traffic:
    """Génère le réseau `seed` et y fait rouler les véhicules pendant EPISODE_TIME."""
    network = RoadNetwork(COLUMNS, ROWS)
    generate_network(network, seed, roads, intersections)
    traffic = Traffic(network, vehicles, seed, policy=policy)
    for _ in range(round(EPISODE_TIME / DT)):
        traffic.update(DT)
    return traffic


def run_episode(policy: Policy, episode: tuple[int, int, int, int]) -> float:
    """Simule un épisode et renvoie les collisions par véhicule et par minute."""
    traffic = simulate(policy, *episode)
    vehicles = episode[3]
    return traffic.collisions / vehicles / (EPISODE_TIME / 60)


def train(count: int = EPISODES, seed: int = TRAINING_SEED) -> tuple[QAgent, list[float]]:
    """Entraîne un agent. Renvoie l'agent et les collisions/véhicule/min de chaque épisode."""
    episodes = make_episodes(count, random.Random(seed))
    agent = QAgent(learning=True, seed=seed)
    curve = []
    for index, episode in enumerate(episodes):
        agent.epsilon = max(MIN_EPSILON, 1 - index / (EXPLORATION_SHARE * count))
        curve.append(run_episode(agent, episode))
        agent.forget()
        if (index + 1) % max(1, count // 10) == 0:
            recent = curve[-AVERAGE_WINDOW:]
            print(f"épisode {index + 1}/{count}  ·  epsilon {agent.epsilon:.2f}  ·  "
                  f"collisions/véhicule/min {sum(recent) / len(recent):.2f}")
    return agent, curve


def reference_level(policy: Policy, seed: int = TRAINING_SEED) -> float:
    """Collisions/véhicule/min moyennes d'une conduite fixe sur les premiers épisodes."""
    episodes = make_episodes(REFERENCE_EPISODES, random.Random(seed))
    return sum(run_episode(policy, episode) for episode in episodes) / len(episodes)


def moving_average(values: list[float], window: int) -> list[float]:
    """Moyenne des `window` dernières valeurs (moins au début de la liste)."""
    averages, total = [], 0.0
    for i, value in enumerate(values):
        total += value
        if i >= window:
            total -= values[i - window]
        averages.append(total / min(i + 1, window))
    return averages


def french(value: float) -> str:
    """Nombre à une décimale, avec une virgule : 1.8 -> "1,8"."""
    return f"{value:.1f}".replace(".", ",")


def draw_curve(curve: list[float], references: dict[str, float], path: Path) -> None:
    """Courbe d'apprentissage (moyenne glissante) et niveaux de la règle et du hasard."""
    fig = Figure(figsize=(8, 4.5), dpi=150, facecolor=SURFACE)
    ax = fig.add_subplot()
    ax.set_facecolor(SURFACE)
    # La moyenne ne commence qu'une fois la fenêtre pleine : avant, elle est trop bruitée.
    start = min(AVERAGE_WINDOW, len(curve))
    average = moving_average(curve, AVERAGE_WINDOW)[start - 1:]
    ax.plot(range(start, len(curve) + 1), average, color=LEARNED_COLOR, linewidth=2)
    ax.annotate(f"appris : {french(average[-1])}", (len(curve), average[-1]),
                xytext=(6, 0), textcoords="offset points", va="center",
                color=TEXT, fontsize=9, fontweight="bold")
    for name, level in references.items():
        ax.axhline(level, color=REFERENCE_COLOR, linewidth=1, linestyle=(0, (4, 3)))
        ax.annotate(f"{name} : {french(level)}", (len(curve), level), xytext=(6, 0),
                    textcoords="offset points", va="center", color=TEXT_MUTED, fontsize=9)
    ax.set_xlim(0, len(curve))
    ax.set_ylim(0, max(max(average), *references.values()) * 1.15)
    ax.set_xlabel("épisode d'entraînement", color=TEXT_MUTED)
    ax.set_ylabel("collisions par véhicule et par minute", color=TEXT_MUTED)
    fig.suptitle("Les véhicules apprennent à ne pas se heurter", x=0.08, ha="left",
                 color=TEXT, fontsize=13, fontweight="bold")
    ax.set_title(f"{len(curve)} épisodes de 60 s, réseaux au hasard · courbe : moyenne sur "
                 f"{AVERAGE_WINDOW} épisodes", loc="left", color=TEXT_MUTED, fontsize=9)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=TEXT_MUTED, labelsize=9)
    fig.subplots_adjust(left=0.08, right=0.8, top=0.86, bottom=0.12)
    fig.savefig(path, facecolor=SURFACE)


def main() -> None:
    """Entraîne, enregistre la table et dessine la courbe."""
    count = int(sys.argv[1]) if len(sys.argv) > 1 else EPISODES
    agent, curve = train(count)
    agent.save(TABLE_FILE)
    references = {"hasard": reference_level(RandomPolicy()),
                  "règle actuelle": reference_level(RulePolicy())}
    draw_curve(curve, references, CURVE_FILE)
    print(f"Table : {TABLE_FILE.name} ({len(agent.q)} états)  ·  courbe : {CURVE_FILE}")


if __name__ == "__main__":
    main()
