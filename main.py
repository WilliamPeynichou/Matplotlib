"""Point d'entrée : crée le réseau, le génère et l'affiche."""

import random

from display import show
from generator import generate_network
from network import RoadNetwork

COLUMNS = 15
ROWS = 9
SEED = None  # mettre un nombre (ex. 4821) pour rejouer exactement un réseau
MAX_SEED = 99999


def create_seed() -> int:
    """Renvoie la seed fixée, sinon une seed au hasard."""
    if SEED is not None:
        return SEED
    return random.randint(0, MAX_SEED)


def main() -> None:
    """Lance RoadNetwork."""
    network = RoadNetwork(COLUMNS, ROWS)
    seed = create_seed()
    generate_network(network, seed)
    print(f"Seed : {seed}")

    def on_randomize() -> int:
        """Régénère le réseau avec une nouvelle seed et la renvoie."""
        new_seed = random.randint(0, MAX_SEED)
        network.reset()
        generate_network(network, new_seed)
        print(f"Seed : {new_seed}")
        return new_seed

    show(network, seed, on_randomize)


if __name__ == "__main__":
    main()
