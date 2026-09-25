"""Les conduites : qui choisit la sortie et l'allure d'un véhicule à chaque node (ML-3).

Une conduite (politique) répond à une question :
    choose(traffic, vehicle, node, exits) -> (sortie, allure)
- RulePolicy : la règle de divergence (feature 15), toujours à allure normale.
- RandomPolicy : sortie et allure au hasard (point de comparaison pour l'apprentissage).

Règle de divergence : à un node qui a plusieurs sorties, si un autre véhicule y est
passé il y a moins de DIVERGE_WINDOW secondes, on prend une sortie différente de la sienne.
"""

from typing import TYPE_CHECKING

from models import Node

if TYPE_CHECKING:  # seulement pour les annotations : traffic.py importe déjà ce fichier
    from traffic import Traffic, Vehicle

DIVERGE_WINDOW = 2.0  # secondes
PACES = {"slow": 0.5, "normal": 1.0, "fast": 1.5}  # allure -> multiplicateur de vitesse


class Policy:
    """Une conduite. Chaque conduite écrit choose() ; on_collision() et on_arrival()
    ne servent qu'aux conduites qui apprennent (learning.py)."""

    def choose(self, traffic: "Traffic", vehicle: "Vehicle", node: Node,
               exits: list[Node]) -> tuple[Node, str]:
        """Renvoie (sortie, allure) pour `vehicle` arrêté sur `node`."""
        raise NotImplementedError

    def on_collision(self, traffic: "Traffic", vehicle: "Vehicle") -> None:
        """Prévenu quand `vehicle` vient d'en heurter un autre."""

    def on_arrival(self, traffic: "Traffic", vehicle: "Vehicle") -> None:
        """Prévenu quand `vehicle` arrive au END."""


class RulePolicy(Policy):
    """La règle de divergence, à allure normale : la conduite par défaut."""

    def choose(self, traffic: "Traffic", vehicle: "Vehicle", node: Node,
               exits: list[Node]) -> tuple[Node, str]:
        """Sortie choisie par la règle de divergence, allure normale."""
        return self.choose_exit(traffic, node, exits), "normal"

    def choose_exit(self, traffic: "Traffic", node: Node, exits: list[Node]) -> Node:
        """Choisit une sortie en évitant celles prises récemment par d'autres véhicules."""
        if len(exits) == 1:
            return exits[0]
        recent = [exit_node for moment, exit_node in traffic.passages.get(node, [])
                  if traffic.time - moment <= DIVERGE_WINDOW]
        free = [exit_node for exit_node in exits if exit_node not in recent]
        if free:
            choice = traffic.rng.choice(free)
            if recent:
                traffic.forced_divergences += 1
        elif recent:
            # Toutes les sorties ont été prises dans les 2 s : choisir autre chose
            # que la dernière sortie, quitte à réutiliser une sortie plus ancienne.
            last_exit = traffic.passages[node][-1][1]
            alternatives = [exit_node for exit_node in exits if exit_node is not last_exit]
            choice = traffic.rng.choice(alternatives)
            traffic.forced_divergences += 1
        else:
            choice = traffic.rng.choice(exits)
        traffic.decisions.append((node, traffic.time, choice, exits, recent.copy()))
        self.remember(traffic, node, choice)
        return choice

    def remember(self, traffic: "Traffic", node: Node, choice: Node) -> None:
        """Note le passage et oublie ceux de plus de DIVERGE_WINDOW secondes."""
        passages = [(moment, exit_node) for moment, exit_node in traffic.passages.get(node, [])
                    if traffic.time - moment <= DIVERGE_WINDOW]
        passages.append((traffic.time, choice))
        traffic.passages[node] = passages


class RandomPolicy(Policy):
    """Sortie et allure au hasard : ce que ferait un conducteur qui n'a rien appris."""

    def choose(self, traffic: "Traffic", vehicle: "Vehicle", node: Node,
               exits: list[Node]) -> tuple[Node, str]:
        """Une sortie et une allure tirées au hasard."""
        return traffic.rng.choice(exits), traffic.rng.choice(list(PACES))
