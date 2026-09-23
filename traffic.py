"""La circulation : des véhicules qui parcourent les routes (feature 15).

Règle de divergence : à un node qui a plusieurs sorties, si un autre véhicule y est
passé il y a moins de DIVERGE_WINDOW secondes, on prend une sortie différente de la sienne.
"""

import random

from models import Node
from network import RoadNetwork

SPEED = 1.5  # segments par seconde
SPAWN_DELAY = 0.7  # secondes entre deux départs
DIVERGE_WINDOW = 2.0  # secondes


class Vehicle:
    """Un point qui avance de node en node, toujours vers la droite."""

    def __init__(self, number: int, start: Node, departure: float):
        self.number = number
        self.current = start  # dernier node atteint
        self.target = None  # node vers lequel il roule (None = à l'arrêt)
        self.progress = 0.0  # 0 = sur current, 1 = sur target
        self.departure = departure  # instant de départ (secondes)


class Traffic:
    """Fait rouler `count` véhicules sur le réseau et applique la règle de divergence."""

    def __init__(self, network: RoadNetwork, count: int, seed: int):
        self.network = network
        self.rng = random.Random(seed)
        self.time = 0.0
        self.start = network.get_start()
        self.vehicles = []
        if self.start is not None:
            self.vehicles = [Vehicle(i, self.start, i * SPAWN_DELAY) for i in range(count)]
        self.passages = {}  # node -> [(instant, sortie choisie)]
        self.decisions = []  # historique, utilisé par check.py
        self.forced_divergences = 0

    def update(self, dt: float) -> None:
        """Avance la simulation de dt secondes."""
        self.time += dt
        for vehicle in self.vehicles:
            if self.time < vehicle.departure:
                continue
            if vehicle.target is None:
                self.leave(vehicle)
                continue
            vehicle.progress += SPEED * dt
            if vehicle.progress >= 1:
                vehicle.current = vehicle.target
                vehicle.progress = 0.0
                self.leave(vehicle)

    def leave(self, vehicle: Vehicle) -> None:
        """Choisit la prochaine route ; en bout de route, le véhicule repart du START."""
        exits = self.get_exits(vehicle.current)
        if not exits:
            vehicle.current = self.start
            vehicle.target = None
            return
        vehicle.target = self.choose_exit(vehicle.current, exits)

    def get_exits(self, node: Node) -> list[Node]:
        """Nodes voisins situés dans la colonne de droite."""
        exits = []
        for segment in node.segments:
            neighbor = segment.end if segment.start is node else segment.start
            if neighbor.x == node.x + 1:
                exits.append(neighbor)
        return exits

    def choose_exit(self, node: Node, exits: list[Node]) -> Node:
        """Choisit une sortie en évitant celles prises récemment par d'autres véhicules."""
        if len(exits) == 1:
            return exits[0]
        recent = [exit_node for moment, exit_node in self.passages.get(node, [])
                  if self.time - moment <= DIVERGE_WINDOW]
        free = [exit_node for exit_node in exits if exit_node not in recent]
        if free:
            choice = self.rng.choice(free)
            if recent:
                self.forced_divergences += 1
        elif recent:
            # Toutes les sorties ont été prises dans les 2 s : choisir autre chose
            # que la dernière sortie, quitte à réutiliser une sortie plus ancienne.
            last_exit = self.passages[node][-1][1]
            alternatives = [exit_node for exit_node in exits if exit_node is not last_exit]
            choice = self.rng.choice(alternatives)
            self.forced_divergences += 1
        else:
            choice = self.rng.choice(exits)
        self.decisions.append((node, self.time, choice, exits, recent.copy()))
        self.remember(node, choice)
        return choice

    def remember(self, node: Node, choice: Node) -> None:
        """Note le passage et oublie ceux de plus de DIVERGE_WINDOW secondes."""
        passages = [(moment, exit_node) for moment, exit_node in self.passages.get(node, [])
                    if self.time - moment <= DIVERGE_WINDOW]
        passages.append((self.time, choice))
        self.passages[node] = passages

    def get_moving(self) -> list[Vehicle]:
        """Véhicules déjà partis."""
        return [vehicle for vehicle in self.vehicles if self.time >= vehicle.departure]
