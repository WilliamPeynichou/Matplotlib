"""La circulation : des véhicules qui parcourent les routes (feature 15).

Chaque véhicule a sa propre vitesse (ML-1) : les rapides rattrapent les lents.

Collisions (ML-2) : les véhicules se traversent, mais chaque nouveau contact est compté.

Conduite (ML-3) : à chaque node, une politique (policies.py) choisit la sortie et l'allure.
Par défaut, c'est la règle de divergence.
"""

import random
from itertools import combinations

from models import Node, NodeType
from network import RoadNetwork
from policies import PACES, RulePolicy

SPEED = 1.5  # vitesse moyenne, en segments par seconde
MIN_SPEED_FACTOR = 0.7  # le plus lent roule à 0.7 x SPEED
MAX_SPEED_FACTOR = 1.3  # le plus rapide à 1.3 x SPEED
SPAWN_DELAY = 0.7  # secondes entre deux départs
MIN_GAP = 0.15  # en segments : plus près que ça, deux véhicules se heurtent
# Carburant (Alice) : consommation par unité de longueur selon l'allure. Rouler vite coûte.
FUEL = {"slow": 0.5, "normal": 1.0, "fast": 2.0}
NAMES = ["Alice", "Bruno", "Chloé", "David", "Emma", "Farid", "Gaïa", "Hugo", "Inès", "Jules",
         "Karim", "Léa", "Malik", "Nina", "Oscar", "Paul", "Rose", "Sami", "Théo", "Zoé"]


def make_name(number: int) -> str:
    """Prénom unique : Alice, Bruno… puis Alice 2, Bruno 2… si plus de 20 véhicules."""
    name = NAMES[number % len(NAMES)]
    return name if number < len(NAMES) else f"{name} {number // len(NAMES) + 1}"


class Vehicle:
    """Un point qui avance de node en node, toujours vers la droite."""

    def __init__(self, number: int, start: Node, departure: float, base_speed: float = SPEED):
        self.number = number
        self.name = make_name(number)  # nominatif et unique
        self.laps = 0  # tours terminés (retour à la ligne de départ)
        self.best_lap = None  # meilleur temps de tour (secondes)
        self.lap_start = departure
        self.collisions = 0
        self.lap_collisions = []  # collisions de chaque tour terminé (voir si Alice progresse)
        self.collisions_at_lap_start = 0
        # False (tout le monde) : chaque tronçon dure pareil. True (Alice) : plus un tronçon
        # est long, plus il prend de temps (vitesse de base / longueur).
        self.distance_aware = False
        self.pace = "normal"  # allure choisie sur le tronçon en cours (observabilité)
        self.length = 1.0  # longueur du tronçon en cours
        self.pace_counts = {pace: 0 for pace in PACES}  # combien de fois chaque allure
        self.distance = 0.0  # distance parcourue (vraies longueurs si distance_aware)
        self.fuel = 0.0  # carburant consommé (seulement si distance_aware)
        self.current = start  # dernier node atteint
        self.target = None  # node vers lequel il roule (None = à l'arrêt)
        self.progress = 0.0  # 0 = sur current, 1 = sur target
        self.departure = departure  # instant de départ (secondes)
        self.base_speed = base_speed  # vitesse propre du véhicule
        self.speed = base_speed  # vitesse sur le segment en cours = base_speed x allure
        self.trip_start = departure  # instant où il a quitté le START pour ce trajet


def make_pair(a: Vehicle, b: Vehicle) -> tuple[Vehicle, Vehicle]:
    """Paire rangée par numéro : (a, b) et (b, a) donnent la même paire."""
    return (a, b) if a.number < b.number else (b, a)


class Traffic:
    """Fait rouler `count` véhicules sur le réseau selon une conduite (règle par défaut)."""

    def __init__(self, network: RoadNetwork, count: int, seed: int, policy=None,
                 special=None):
        self.network = network
        self.policy = policy if policy is not None else RulePolicy()
        # Conduites propres à certaines voitures : {numéro: conduite}. Ex. {0: arbre} = Alice
        # conduit avec l'arbre, les autres avec self.policy (sert à comparer une seule voiture).
        self.special = special or {}
        self.rng = random.Random(seed)
        self.time = 0.0
        self.start = network.get_start()
        self.vehicles = []
        # Hasard séparé : tirer les vitesses ne change pas les choix de sortie d'une seed.
        speed_rng = random.Random(f"{seed}-speeds")
        if self.start is not None:
            self.vehicles = [
                Vehicle(i, self.start, i * SPAWN_DELAY,
                        SPEED * speed_rng.uniform(MIN_SPEED_FACTOR, MAX_SPEED_FACTOR))
                for i in range(count)
            ]
        self.lengths = {}  # (node, node) -> longueur, calculée une fois
        # Circuit : TOUTES les voitures suivent les mêmes règles (vraies distances + carburant).
        # Seule Alice apprend ; les autres gardent leur conduite fixe.
        if hasattr(network, "frames"):  # uniquement sur le circuit
            for vehicle in self.vehicles:
                vehicle.distance_aware = True
        self.passages = {}  # node -> [(instant, sortie choisie)], mémoire de la règle
        self.decisions = []  # historique de la règle, utilisé par check.py
        self.forced_divergences = 0
        self.collisions = 0
        self.collision_events = []  # [(instant, véhicule, véhicule, (node, node, progress))]
        self.contacts = set()  # paires en contact à l'image précédente
        self.previous = {}  # véhicule -> ((node, node), progress) à l'image précédente
        self.trip_times = []  # durée (s) de chaque trajet START -> END terminé

    def update(self, dt: float) -> None:
        """Avance la simulation de dt secondes, puis compte les nouvelles collisions."""
        self.time += dt
        for vehicle in self.vehicles:
            if self.time < vehicle.departure:
                continue
            if vehicle.target is None:
                self.leave(vehicle)
                continue
            vehicle.progress += vehicle.speed * dt / vehicle.length
            if vehicle.progress >= 1:
                vehicle.current = vehicle.target
                vehicle.progress = 0.0
                self.leave(vehicle)
        self.detect_collisions()

    def detect_collisions(self) -> None:
        """Une collision = un nouveau contact (un contact qui dure ne compte qu'une fois)."""
        rolling = [vehicle for vehicle in self.get_moving() if vehicle.target is not None]
        contacts = self.find_contacts(rolling)
        for a, b in sorted(contacts - self.contacts, key=lambda p: (p[0].number, p[1].number)):
            self.collisions += 1
            a.collisions += 1
            b.collisions += 1
            self.collision_events.append((self.time, a, b, (a.current, a.target, a.progress)))
            self.policy_of(a).on_collision(self, a)
            self.policy_of(b).on_collision(self, b)
        self.contacts = contacts
        self.previous = {v: ((v.current, v.target), v.progress) for v in rolling}

    def find_contacts(self, rolling: list[Vehicle]) -> set[tuple[Vehicle, Vehicle]]:
        """Paires trop proches : sur le même segment, ou autour du même node (fusion, sortie).
        On range les véhicules par segment et par node pour ne comparer que des voisins."""
        by_segment = {}
        near_node = {}  # node -> [(véhicule, distance au node)], seulement si distance < MIN_GAP
        for vehicle in rolling:
            by_segment.setdefault((vehicle.current, vehicle.target), []).append(vehicle)
            for node, distance in ((vehicle.current, vehicle.progress),
                                   (vehicle.target, 1 - vehicle.progress)):
                if distance < MIN_GAP:
                    near_node.setdefault(node, []).append((vehicle, distance))
        contacts = set()
        for group in by_segment.values():
            for a, b in combinations(group, 2):
                if abs(a.progress - b.progress) < MIN_GAP or self.has_overtaken(a, b):
                    contacts.add(make_pair(a, b))
        for node, group in near_node.items():
            if node.type in (NodeType.START, NodeType.END):
                continue  # départ et retour des véhicules
            for (a, distance_a), (b, distance_b) in combinations(group, 2):
                if distance_a + distance_b < MIN_GAP:
                    contacts.add(make_pair(a, b))
        return contacts

    def has_overtaken(self, a: Vehicle, b: Vehicle) -> bool:
        """Vrai si a et b ont échangé leur ordre sur ce segment depuis l'image précédente :
        un dépassement est impossible sur une voie, même s'il a eu lieu entre deux images."""
        segment = (a.current, a.target)
        before_a, before_b = self.previous.get(a), self.previous.get(b)
        if before_a is None or before_b is None:
            return False
        if before_a[0] != segment or before_b[0] != segment:
            return False
        return (before_a[1] - before_b[1]) * (a.progress - b.progress) < 0

    def leave(self, vehicle: Vehicle) -> None:
        """La conduite choisit la route et l'allure ; en bout de route, retour au START."""
        if vehicle.current.type is NodeType.START:
            vehicle.trip_start = self.time
        exits = self.get_exits(vehicle.current)
        if not exits:
            self.trip_times.append(self.time - vehicle.trip_start)
            self.policy_of(vehicle).on_arrival(self, vehicle)
            # Réseau simple : retour au START. Circuit : START du cadre suivant.
            vehicle.current = self.network.get_next_start(vehicle.current)
            vehicle.target = None
            if vehicle.current is self.start:
                self.finish_lap(vehicle)
            return
        policy = self.policy_of(vehicle)
        vehicle.target, pace = policy.choose(self, vehicle, vehicle.current, exits)
        vehicle.speed = vehicle.base_speed * PACES[pace]
        vehicle.pace = pace
        vehicle.length = self.get_length(vehicle) if vehicle.distance_aware else 1.0
        vehicle.pace_counts[pace] += 1
        vehicle.distance += vehicle.length
        if vehicle.distance_aware:
            vehicle.fuel += FUEL[pace] * vehicle.length

    def get_length(self, vehicle: Vehicle) -> float:
        """Longueur du tronçon en cours du véhicule (mise en cache)."""
        key = (vehicle.current, vehicle.target)
        if key not in self.lengths:
            self.lengths[key] = self.network.get_length(*key)
        return self.lengths[key]

    def policy_of(self, vehicle: Vehicle):
        """Conduite de ce véhicule : la sienne s'il en a une, sinon celle de tout le monde."""
        return self.special.get(vehicle.number, self.policy)

    def finish_lap(self, vehicle: Vehicle) -> None:
        """Un tour de plus, et peut-être un meilleur temps."""
        lap = self.time - vehicle.lap_start
        vehicle.laps += 1
        if vehicle.best_lap is None or lap < vehicle.best_lap:
            vehicle.best_lap = lap
        vehicle.lap_start = self.time
        vehicle.lap_collisions.append(vehicle.collisions - vehicle.collisions_at_lap_start)
        vehicle.collisions_at_lap_start = vehicle.collisions

    def get_ranking(self) -> list[Vehicle]:
        """Classement : plus de tours d'abord, puis meilleur tour le plus court."""
        return sorted(self.get_moving(), key=lambda v: (-v.laps, v.best_lap or float("inf"),
                                                         v.number))

    def get_exits(self, node: Node) -> list[Node]:
        """Nodes voisins situés dans la colonne de droite."""
        exits = []
        for segment in node.segments:
            neighbor = segment.end if segment.start is node else segment.start
            if neighbor.x == node.x + 1:
                exits.append(neighbor)
        return exits

    def get_moving(self) -> list[Vehicle]:
        """Véhicules déjà partis."""
        return [vehicle for vehicle in self.vehicles if self.time >= vehicle.departure]
