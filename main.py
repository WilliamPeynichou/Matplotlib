"""Point d'entrée : crée le réseau, le génère et l'affiche."""

import random

from display import show
from generator import generate_network
from network import RoadNetwork

COLUMNS = 15
ROWS = 9
SEED = None  # mettre un nombre (ex. 4821) pour rejouer exactement un réseau
MAX_SEED = 99999
ROADS = 4  # chemin principal + branches
INTERSECTIONS = 4  # nombre visé (le plus proche possible)
VEHICLES = 6


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
    settings = {"roads": ROADS, "intersections": INTERSECTIONS, "vehicles": VEHICLES}

    def generate(seed: int, roads: int, intersections: int) -> int:
        """Génère le réseau et renvoie le nombre d'intersections obtenu."""
        count = generate_network(network, seed, roads, intersections)
        print(f"Seed : {seed}  routes : {roads}  intersections : {count}/{intersections}")
        return count

    def new_seed() -> int:
        """Tire une nouvelle seed pour le bouton Randomize."""
        return random.randint(0, MAX_SEED)

    show(network, create_seed(), settings, generate, new_seed)


if __name__ == "__main__":
    main()
