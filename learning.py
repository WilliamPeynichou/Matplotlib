"""L'apprentissage : les véhicules apprennent à ne pas se heurter (Q-learning).

1. Ce que « voit » un véhicule quand il doit choisir sa route (ML-5).
L'état est un petit tuple, pour que la table de Q-learning reste petite (4 x 4 x 4 x 2 x 2 = 256) :
    (descendre, tout droit, monter, rapide, derrière)
- une case par direction de sortie :
    NO_EXIT (0) pas de sortie,  FREE (1) libre,  BUSY (2) véhicule devant mais loin,
    DANGER (3) véhicule devant et proche, ou un autre véhicule arrive au même node en même temps ;
- rapide : 1 si le véhicule roule plus vite que la moyenne (SPEED), sinon 0 ;
- derrière : 1 si un véhicule arrive juste derrière lui (aller lentement serait risqué).

2. L'agent (ML-6) : une table q[état][action] = « ce que rapporte cette action ici ».
Une action = (direction, allure) : 3 x 3 = 9 actions. Après chaque segment, le véhicule
reçoit sa récompense (collision -10, arrivée +1, -0.1 par seconde de route) et corrige :
    q[état][action] += ALPHA * (récompense + GAMMA * meilleur q de l'état suivant - q[état][action])
Tous les véhicules partagent la même table : ce que l'un apprend sert aux autres.

3. Le choix de la conduite (ML-9) : make_policy("random" | "rule" | "learned"). Si la table
apprise manque ou est abîmée, on revient à la règle au lieu de planter.
"""

import json
import random
from pathlib import Path

from models import Node
from policies import PACES, Policy, RandomPolicy, RulePolicy
from traffic import SPEED, Traffic, Vehicle

NO_EXIT, FREE, BUSY, DANGER = 0, 1, 2, 3
STATE_SIZE = 5  # (descendre, tout droit, monter, rapide, derrière)
CLOSE_GAP = 0.4  # en segments : un véhicule devant à moins de ça est dangereux
MERGE_WINDOW = 0.3  # secondes : deux arrivées au même node plus proches que ça = danger
BEHIND_GAP = 0.3  # en segments : un véhicule derrière à moins de ça est dangereux

ACTIONS = [(direction, pace) for direction in range(3) for pace in PACES]  # (0, "slow")...
ALPHA = 0.1  # vitesse d'apprentissage : part de la nouvelle expérience dans q
GAMMA = 0.9  # poids du futur : 0 = seul le segment compte, 1 = tout le trajet compte
COLLISION_REWARD = -10.0
ARRIVAL_REWARD = 1.0
TIME_COST = 0.1  # par seconde de route : sinon rouler lentement serait gratuit
TABLE_FILE = Path(__file__).parent / "q_table.json"  # écrite par train.py
DRIVINGS = {"random": "Hasard", "rule": "Règle", "learned": "Appris"}  # nom -> étiquette


def get_state(traffic: Traffic, vehicle: Vehicle, node: Node,
              exits: list[Node]) -> tuple[int, int, int, int, int]:
    """État du véhicule arrêté sur `node`, au moment de choisir parmi `exits`."""
    others = [other for other in traffic.get_moving()
              if other is not vehicle and other.target is not None]
    directions = [NO_EXIT, NO_EXIT, NO_EXIT]  # descendre, tout droit, monter
    for target in exits:
        directions[target.y - node.y + 1] = get_exit_state(vehicle, node, target, others)
    fast = 1 if vehicle.base_speed > SPEED else 0
    behind = 1 if any(other.target is node and 1 - other.progress < BEHIND_GAP
                      for other in others) else 0
    return (*directions, fast, behind)


def get_exit_state(vehicle: Vehicle, node: Node, target: Node, others: list[Vehicle]) -> int:
    """FREE, BUSY ou DANGER pour la sortie node -> target, vue à allure normale."""
    my_arrival = 1 / vehicle.base_speed  # temps pour atteindre target à allure normale
    state = FREE
    for other in others:
        if other.target is not target:
            continue
        if other.current is node:  # sur la même route, devant nous
            if other.progress < CLOSE_GAP:
                return DANGER
        else:  # sur une autre route qui rejoint le même node
            other_arrival = (1 - other.progress) / other.speed
            if abs(other_arrival - my_arrival) < MERGE_WINDOW:
                return DANGER
        state = BUSY
    return state


class QAgent(Policy):
    """Conduite qui apprend par Q-learning, ou qui applique ce qu'elle a appris.

    learning=True : entraînement, choisit au hasard une fois sur `epsilon` pour explorer.
    learning=False (par défaut) : prend toujours la meilleure action connue, sans rien changer.
    """

    def __init__(self, learning: bool = False, epsilon: float = 0.0, seed: int = 0):
        self.q = {}  # état -> [valeur de chacune des 9 actions]
        self.learning = learning
        self.epsilon = epsilon
        self.rng = random.Random(seed)  # hasard séparé : ne change pas celui du trafic
        self.memory = {}  # véhicule -> [état, action, instant de la décision, récompense reçue]

    def choose(self, traffic: Traffic, vehicle: Vehicle, node: Node,
               exits: list[Node]) -> tuple[Node, str]:
        """Meilleure action connue parmi les directions qui existent (ou une au hasard)."""
        state = get_state(traffic, vehicle, node, exits)
        values = self.q.get(state, [0.0] * len(ACTIONS))
        allowed = [i for i, (direction, _) in enumerate(ACTIONS) if state[direction] != NO_EXIT]
        if self.learning and self.rng.random() < self.epsilon:
            action = self.rng.choice(allowed)
        else:
            action = max(allowed, key=lambda i: values[i])
        if self.learning:
            self.learn(traffic, vehicle, future=max(values[i] for i in allowed))
            self.memory[vehicle] = [state, action, traffic.time, 0.0]
        direction, pace = ACTIONS[action]
        target = next(exit_node for exit_node in exits if exit_node.y - node.y + 1 == direction)
        return target, pace

    def on_collision(self, traffic: Traffic, vehicle: Vehicle) -> None:
        """Punit la décision en cours du véhicule."""
        if vehicle in self.memory:
            self.memory[vehicle][3] += COLLISION_REWARD

    def on_arrival(self, traffic: Traffic, vehicle: Vehicle) -> None:
        """Récompense la dernière décision ; fin du trajet, donc pas de futur."""
        if vehicle in self.memory:
            self.memory[vehicle][3] += ARRIVAL_REWARD
            self.learn(traffic, vehicle, future=0.0)

    def learn(self, traffic: Traffic, vehicle: Vehicle, future: float) -> None:
        """Corrige q pour la décision précédente du véhicule. `future` = meilleur q suivant."""
        if vehicle not in self.memory:
            return  # première décision du véhicule : rien à corriger
        state, action, moment, reward = self.memory.pop(vehicle)
        reward -= TIME_COST * (traffic.time - moment)
        values = self.q.setdefault(state, [0.0] * len(ACTIONS))
        values[action] += ALPHA * (reward + GAMMA * future - values[action])

    def forget(self) -> None:
        """Oublie les trajets en cours (fin d'un épisode d'entraînement)."""
        self.memory = {}

    def save(self, path: str) -> None:
        """Écrit la table en JSON, une ligne par état, valeurs arrondies (lisible à l'oral).
        Clé "1,3,0,1,0" : JSON n'accepte pas les tuples."""
        lines = [f'  "{",".join(map(str, state))}": {json.dumps([round(v, 4) for v in values])}'
                 for state, values in sorted(self.q.items())]
        with open(path, "w", encoding="utf-8") as file:
            file.write("{\n" + ",\n".join(lines) + "\n}\n")

    @classmethod
    def load(cls, path: str) -> "QAgent":
        """Conduite apprise : lit la table, prend toujours la meilleure action, n'apprend plus.
        OSError si le fichier manque, ValueError s'il est abîmé."""
        with open(path, encoding="utf-8") as file:
            table = json.load(file)
        if not isinstance(table, dict):
            raise ValueError("table Q : un objet JSON est attendu")
        agent = cls()
        for key, values in table.items():
            state = tuple(int(x) for x in key.split(","))
            if (len(state) != STATE_SIZE or not isinstance(values, list)
                    or len(values) != len(ACTIONS)
                    or not all(isinstance(v, int | float) for v in values)):
                raise ValueError(f"table Q : ligne invalide {key!r}")
            agent.q[state] = [float(v) for v in values]
        return agent


def make_policy(driving: str, path: Path = TABLE_FILE) -> tuple[Policy, str]:
    """Conduite à partir de son nom ("random", "rule" ou "learned").
    Si la table apprise manque ou est abîmée : la règle, jamais de crash.
    Renvoie (conduite, nom de la conduite vraiment utilisée)."""
    if driving == "random":
        return RandomPolicy(), "random"
    if driving == "learned":
        try:
            return QAgent.load(path), "learned"
        except (OSError, ValueError):
            pass
    return RulePolicy(), "rule"
