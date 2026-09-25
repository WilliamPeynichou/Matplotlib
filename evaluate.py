"""Comparaison (ML-8) : hasard, règle actuelle et conduite apprise, sur les mêmes réseaux.

Lancer : .venv/bin/python evaluate.py   (~2 s ; lit q_table.json)
Affiche un tableau et écrit docs/images/comparaison.png.

Les 20 réseaux de test (seeds 0 à 19) ne servent jamais à l'entraînement (seeds >= 10 000) :
on mesure ce que l'agent a appris, pas ce qu'il a retenu par cœur.
"""

from pathlib import Path

from matplotlib.figure import Figure

from learning import TABLE_FILE, QAgent
from policies import Policy, RandomPolicy, RulePolicy
from train import EPISODE_TIME, GRID, LEARNED_COLOR, SURFACE, TEXT, TEXT_MUTED, french, simulate

TEST_SEEDS = range(20)
ROADS, INTERSECTIONS = 4, 4  # le réseau par défaut de la fenêtre
VEHICLES = 10  # trafic chargé : assez de monde pour que les collisions comptent
COMPARISON_FILE = Path(__file__).parent / "docs" / "images" / "comparaison.png"
OTHER_COLOR = "#b5b4ae"  # hasard et règle en gris : seule la conduite apprise est mise en avant


def evaluate(policy: Policy) -> dict:
    """Fait rouler `policy` sur chaque réseau de test et renvoie ses mesures moyennes."""
    minutes = EPISODE_TIME / 60
    collisions, trips = [], []
    for seed in TEST_SEEDS:
        traffic = simulate(policy, seed, ROADS, INTERSECTIONS, VEHICLES)
        collisions.append(traffic.collisions / minutes)
        trips.extend(traffic.trip_times)
    return {
        "collisions": sum(collisions) / len(collisions),  # par minute, tous véhicules
        "trip_time": sum(trips) / len(trips),  # secondes par trajet START -> END
        "arrivals": len(trips) / len(TEST_SEEDS) / minutes,  # trajets terminés par minute
        "per_network": collisions,  # collisions/min de chaque réseau de test
    }


def compare() -> dict[str, dict]:
    """Mesures des trois conduites, dans l'ordre du graphique."""
    return {"hasard": evaluate(RandomPolicy()),
            "règle actuelle": evaluate(RulePolicy()),
            "appris": evaluate(QAgent.load(TABLE_FILE))}


def print_table(results: dict[str, dict]) -> None:
    """Tableau dans le terminal, puis sur combien de réseaux l'appris bat la règle."""
    print(f"{'Conduite':<16}{'Collisions/min':>16}{'Trajet moyen (s)':>18}{'Arrivées/min':>14}")
    for name, result in results.items():
        print(f"{name:<16}{french(result['collisions']):>16}{french(result['trip_time']):>18}"
              f"{french(result['arrivals']):>14}")
    pairs = zip(results["appris"]["per_network"], results["règle actuelle"]["per_network"])
    wins = sum(1 for learned, rule in pairs if learned < rule)
    print(f"L'appris fait moins de collisions que la règle sur {wins}/{len(TEST_SEEDS)} réseaux.")


def draw_comparison(results: dict[str, dict], path: Path) -> None:
    """Deux panneaux côte à côte (une mesure chacun, jamais deux échelles sur un axe)."""
    fig = Figure(figsize=(9, 3.6), dpi=150, facecolor=SURFACE)
    names = list(results)
    colors = [LEARNED_COLOR if name == "appris" else OTHER_COLOR for name in names]
    panels = [("collisions", "Collisions par minute"),
              ("trip_time", "Durée d'un trajet START → END (s)")]
    for index, (key, title) in enumerate(panels):
        ax = fig.add_subplot(1, 2, index + 1)
        ax.set_facecolor(SURFACE)
        values = [results[name][key] for name in names]
        ax.barh(names, values, color=colors, height=0.55)
        for row, value in enumerate(values):
            ax.annotate(french(value), (value, row), xytext=(4, 0), textcoords="offset points",
                        va="center", fontsize=9, color=TEXT,
                        fontweight="bold" if names[row] == "appris" else "normal")
        ax.set_title(f"{title}\nmoins = mieux", loc="left", fontsize=10, color=TEXT)
        ax.set_xlim(0, max(values) * 1.2)
        ax.invert_yaxis()  # hasard en haut, appris en bas
        ax.grid(axis="x", color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        for side in ("top", "right", "bottom"):
            ax.spines[side].set_visible(False)
        ax.spines["left"].set_color(GRID)
        ax.tick_params(colors=TEXT_MUTED, labelsize=9, length=0)
        if index == 1:
            ax.set_yticklabels([])  # les noms sont déjà sur le panneau de gauche
    fig.suptitle("Conduite apprise, règle actuelle et hasard", x=0.02, y=0.97, ha="left",
                 fontsize=13, fontweight="bold", color=TEXT)
    fig.text(0.02, 0.87, f"Mêmes {len(TEST_SEEDS)} réseaux de test (jamais vus à "
             f"l'entraînement), {VEHICLES} véhicules, {round(EPISODE_TIME)} s chacun",
             fontsize=9, color=TEXT_MUTED)
    fig.subplots_adjust(left=0.13, right=0.97, top=0.68, bottom=0.08, wspace=0.12)
    fig.savefig(path, facecolor=SURFACE)


def main() -> None:
    """Compare, affiche le tableau et dessine le graphique."""
    results = compare()
    print_table(results)
    draw_comparison(results, COMPARISON_FILE)
    print(f"Graphique : {COMPARISON_FILE}")


if __name__ == "__main__":
    main()
