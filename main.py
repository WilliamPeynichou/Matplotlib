"""Point d'entrée : crée le réseau, le génère et l'affiche."""

import random

from display import show
from generator import generate_network
from learning import DRIVINGS
from network import RoadNetwork

COLUMNS = 15
ROWS = 9
SEED = None  # mettre un nombre (ex. 4821) pour rejouer exactement un réseau
MAX_SEED = 99999
ROADS = 4  # chemin principal + branches
INTERSECTIONS = 4  # nombre visé (le plus proche possible)
VEHICLES = 6
DRIVING = "rule"  # conduite au démarrage : "random", "rule" ou "learned" (lancer train.py avant)


def create_seed() -> int:
    """Renvoie la seed fixée, sinon une seed au hasard."""
    if SEED is not None:
        return SEED
    return random.randint(0, MAX_SEED)


def main() -> None:
    """Lance RoadNetwork."""
    try:
        network = RoadNetwork(COLUMNS, ROWS)
    except ValueError as error:
        print(f"Erreur : {error}. Corrige COLUMNS / ROWS dans main.py.")
        return
    driving = DRIVING
    if driving not in DRIVINGS:
        print(f"Conduite inconnue {driving!r} : choisir parmi {', '.join(DRIVINGS)}. "
              "Conduite Règle utilisée.")
        driving = "rule"
    settings = {"roads": ROADS, "intersections": INTERSECTIONS, "vehicles": VEHICLES,
                "driving": driving}

    def generate(seed: int, roads: int, intersections: int) -> int:
        """Génère le réseau et renvoie le nombre d'intersections obtenu."""
        count = generate_network(network, seed, roads, intersections)
        print(f"Seed : {seed}  routes : {roads}  intersections : {count}/{intersections}")
        return count

    def new_seed() -> int:
        """Tire une nouvelle seed pour le bouton Generate (Randomize coché)."""
        return random.randint(0, MAX_SEED)

    show(network, create_seed(), settings, generate, new_seed, MAX_SEED)


if __name__ == "__main__":
    main()
