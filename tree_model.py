"""Apprentissage SUPERVISÉ : un arbre de décision qui prédit « cette sortie = collision ? ».

Lancer : .venv/bin/python tree_model.py
Produit : data/decisions.csv   (les exemples collectés)
          tree_model.pkl       (le modèle entraîné)
          docs/images/arbre.png et docs/arbre.txt (l'arbre, lisible)

Les 3 étapes, expliquées pas à pas dans docs/ml_alice.md :
1. COLLECTER : on fait rouler des voitures au hasard et on note chaque décision
   - X (features) = ce que voyait la voiture + ce qu'elle a choisi (7 nombres)
   - y (label)    = 1 si elle a eu une collision juste après, sinon 0
2. ENTRAÎNER : l'arbre cherche les questions (« tout droit == DANGER ? ») qui séparent
   le mieux les décisions dangereuses des autres. On garde 20 % des exemples de côté
   pour tester le modèle sur des cas qu'il n'a jamais vus.
3. UTILISER : TreePolicy demande à l'arbre le risque de chaque action possible
   et prend la moins risquée. On la donne à UNE seule voiture (Alice) pour comparer.
"""

import csv
import pickle
import random
import sys
from pathlib import Path

from circuit import Circuit
from learning import ACTIONS, NO_EXIT, get_state
from policies import PACES, Policy, RandomPolicy, RulePolicy
from traffic import Traffic

ROOT = Path(__file__).parent
DATA_FILE = ROOT / "data" / "decisions.csv"
MODEL_FILE = ROOT / "tree_model.pkl"
TREE_IMAGE = ROOT / "docs" / "images" / "arbre.png"
TREE_TEXT = ROOT / "docs" / "arbre.txt"

# Colonnes du tableau d'exemples. Les 5 premières = get_state() de learning.py.
FEATURES = ["descendre", "tout_droit", "monter", "rapide", "derriere", "direction", "allure"]
PACE_NAMES = list(PACES)  # ["slow", "normal", "fast"] -> allure 0, 1, 2

# Circuit utilisé pour collecter / évaluer (le même que main.py).
FRAME_COLUMNS, FRAME_ROWS = 10, 5
ROADS, INTERSECTIONS = 3, 6
VEHICLES = 10
EPISODE_TIME = 60.0  # secondes simulées par épisode
DT = 0.1
COLLECT_EPISODES = 150
FIRST_SEED = 10_000  # seeds 0..9999 réservées à la comparaison (données jamais vues)

MAX_DEPTH = 4  # profondeur de l'arbre : petit = lisible et moins de surapprentissage
TEST_SHARE = 0.2  # 20 % des exemples servent seulement à tester
SLOW_PENALTY = 0.03  # petit malus pour les allures lentes (sinon « lent partout » gagne)


# ---------------------------------------------------------------- 1. COLLECTER

class RecorderPolicy(Policy):
    """Conduit au hasard (pour voir de tout) et note chaque décision + son résultat."""

    def __init__(self):
        self.driver = RandomPolicy()
        self.rows = []  # exemples terminés : [7 features..., label]
        self.pending = {}  # véhicule -> exemple en cours (label pas encore connu)

    def choose(self, traffic, vehicle, node, exits):
        """Choisit au hasard, puis ouvre un nouvel exemple (label = 0 pour l'instant)."""
        self.close(vehicle)  # la décision précédente est finie sans collision -> on la range
        target, pace = self.driver.choose(traffic, vehicle, node, exits)
        state = get_state(traffic, vehicle, node, exits)
        direction = target.y - node.y + 1  # 0 descendre, 1 tout droit, 2 monter
        self.pending[vehicle] = [*state, direction, PACE_NAMES.index(pace), 0]
        return target, pace

    def on_collision(self, traffic, vehicle):
        """Collision pendant ce segment : le label de la décision en cours devient 1."""
        if vehicle in self.pending:
            self.pending[vehicle][-1] = 1

    def on_arrival(self, traffic, vehicle):
        """Fin du cadre : la dernière décision est terminée."""
        self.close(vehicle)

    def close(self, vehicle):
        """Range l'exemple en cours du véhicule dans self.rows."""
        if vehicle in self.pending:
            self.rows.append(self.pending.pop(vehicle))


def run_circuit(seed: int, policy: Policy, special: dict | None = None) -> Traffic:
    """Génère le circuit `seed` et fait rouler VEHICLES voitures pendant EPISODE_TIME."""
    circuit = Circuit(FRAME_COLUMNS, FRAME_ROWS)
    circuit.generate(seed, ROADS, INTERSECTIONS)
    traffic = Traffic(circuit, VEHICLES, seed, policy=policy, special=special)
    for _ in range(round(EPISODE_TIME / DT)):
        traffic.update(DT)
    return traffic


def collect(episodes: int = COLLECT_EPISODES) -> list[list[int]]:
    """Fait rouler des voitures au hasard sur `episodes` circuits. Renvoie les exemples."""
    recorder = RecorderPolicy()
    for index in range(episodes):
        run_circuit(FIRST_SEED + index, recorder)
        recorder.pending = {}  # trajets coupés par la fin de l'épisode : on les jette
    return recorder.rows


def save_rows(rows: list[list[int]], path: Path = DATA_FILE) -> None:
    """Écrit les exemples en CSV (ouvrable dans Excel pour les regarder)."""
    path.parent.mkdir(exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([*FEATURES, "collision"])
        writer.writerows(rows)


# ---------------------------------------------------------------- 2. ENTRAÎNER

def train(rows: list[list[int]], seed: int = 0):
    """Entraîne l'arbre. Renvoie (modèle, rapport). Le rapport compare à un modèle « bête »."""
    from sklearn.metrics import accuracy_score, recall_score
    from sklearn.model_selection import train_test_split
    from sklearn.tree import DecisionTreeClassifier

    x = [row[:-1] for row in rows]  # les features
    y = [row[-1] for row in rows]  # les labels
    # stratify=y : garde la même proportion de collisions dans les deux parties.
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=TEST_SHARE, random_state=seed, stratify=y)
    # class_weight="balanced" : les collisions sont rares ; sans ça, l'arbre répondrait
    # « jamais de collision » et aurait l'air très bon (voir docs/ml_alice.md, piège n°1).
    model = DecisionTreeClassifier(max_depth=MAX_DEPTH, class_weight="balanced",
                                   random_state=seed)
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    report = {
        "exemples": len(rows),
        "part_collisions": sum(y) / len(y),
        "precision_bete": 1 - sum(y_test) / len(y_test),  # répondre toujours 0
        "precision_arbre": accuracy_score(y_test, predictions),
        "collisions_detectees": recall_score(y_test, predictions),  # rappel
        "precision_entrainement": accuracy_score(y_train, model.predict(x_train)),
    }
    return model, report


def save_model(model, path: Path = MODEL_FILE) -> None:
    """Sauve le modèle (pickle = format Python pour enregistrer un objet)."""
    with open(path, "wb") as file:
        pickle.dump(model, file)


def load_model(path: Path = MODEL_FILE):
    """Relit le modèle. OSError si le fichier manque."""
    with open(path, "rb") as file:
        return pickle.load(file)


def draw_tree(model, image: Path = TREE_IMAGE, text: Path = TREE_TEXT) -> None:
    """Dessine l'arbre (PNG) et l'écrit en texte : on peut le lire question par question."""
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure
    from sklearn.tree import export_text, plot_tree

    figure = Figure(figsize=(22, 9))
    FigureCanvasAgg(figure)  # dessin en mémoire, sans fenêtre
    plot_tree(model, feature_names=FEATURES, class_names=["ok", "collision"], filled=True,
              rounded=True, fontsize=7, ax=figure.subplots(), impurity=False)
    figure.savefig(image, dpi=90, bbox_inches="tight")
    text.write_text(export_text(model, feature_names=FEATURES), encoding="utf-8")


# ---------------------------------------------------------------- 3. UTILISER

class TreePolicy(Policy):
    """Conduite guidée par l'arbre : pour chaque action possible, l'arbre donne le risque
    de collision ; on prend l'action au plus petit (risque + malus de lenteur)."""

    def __init__(self, model):
        self.model = model
        self.last_risks = {}  # véhicule -> {action: risque}, pour l'affichage / le debug

    def choose(self, traffic, vehicle, node, exits):
        state = get_state(traffic, vehicle, node, exits)
        actions = [(direction, pace) for direction, pace in ACTIONS
                   if state[direction] != NO_EXIT]  # seulement les sorties qui existent
        rows = [[*state, direction, PACE_NAMES.index(pace)] for direction, pace in actions]
        risks = self.get_risks(rows)
        self.last_risks[vehicle] = dict(zip(actions, risks, strict=True))
        scores = [risk + SLOW_PENALTY * (1 / PACES[pace] - 1)
                  for risk, (_, pace) in zip(risks, actions, strict=True)]
        direction, pace = actions[scores.index(min(scores))]
        target = next(e for e in exits if e.y - node.y + 1 == direction)
        return target, pace

    def get_risks(self, rows: list[list[int]]) -> list[float]:
        """Probabilité de collision (0 à 1) donnée par l'arbre pour chaque ligne."""
        probabilities = self.model.predict_proba(rows)
        column = list(self.model.classes_).index(1) if 1 in self.model.classes_ else None
        return [0.0 if column is None else float(p[column]) for p in probabilities]


def make_tree_policy(path: Path = MODEL_FILE) -> Policy:
    """TreePolicy si le modèle existe, sinon la règle (jamais de crash)."""
    try:
        return TreePolicy(load_model(path))
    except (OSError, pickle.UnpicklingError, ImportError):
        return RulePolicy()


def main() -> None:
    """Collecte, entraîne, affiche le rapport, sauve modèle + dessin."""
    episodes = int(sys.argv[1]) if len(sys.argv) > 1 else COLLECT_EPISODES
    random.seed(0)
    print(f"1. Collecte sur {episodes} circuits (conduite au hasard)…")
    rows = collect(episodes)
    save_rows(rows)
    print(f"   {len(rows)} décisions -> {DATA_FILE.relative_to(ROOT)}")
    print("2. Entraînement de l'arbre…")
    model, report = train(rows)
    save_model(model)
    draw_tree(model)
    print(f"   collisions dans les données : {report['part_collisions']:.1%}")
    print(f"   précision modèle « bête » (toujours 0) : {report['precision_bete']:.1%}")
    print(f"   précision de l'arbre (test)            : {report['precision_arbre']:.1%}")
    print(f"   collisions détectées (rappel, test)    : {report['collisions_detectees']:.1%}")
    print(f"   précision sur l'entraînement           : {report['precision_entrainement']:.1%}")
    print(f"3. Modèle -> {MODEL_FILE.name}, arbre -> {TREE_IMAGE.relative_to(ROOT)}")
    print("   Comparer Alice : .venv/bin/python alice.py")


if __name__ == "__main__":
    main()
