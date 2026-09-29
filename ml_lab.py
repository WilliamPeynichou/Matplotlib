"""Laboratoire reproductible : arbre, forêt et Q-learning sur circuits séparés."""

import argparse
import csv
import json
from pathlib import Path
from statistics import mean, stdev

from alice import ALICE, Q_ALICE_FILE, AliceAgent
from policies import RandomPolicy, RulePolicy
from tree_model import (
    DT,
    EPISODE_TIME,
    FEATURES,
    FRAME_COLUMNS,
    FRAME_ROWS,
    INTERSECTIONS,
    ROADS,
    VEHICLES,
    RecorderPolicy,
    TreePolicy,
    run_circuit,
    save_model,
)

ROOT = Path(__file__).parent
OUTPUT = ROOT / "data" / "lab"
FOREST_FILE = ROOT / "forest_model.pkl"


def collect_groups(seeds):
    """Un groupe par circuit ; identifiant conservé séparément des features."""
    rows, groups = [], []
    for seed in seeds:
        recorder = RecorderPolicy()
        run_circuit(seed, recorder)
        rows.extend(recorder.rows)
        groups.extend([seed] * len(recorder.rows))
    return rows, groups


def fit_models(train_rows, validation_rows):
    """Même données pour arbre et forêt ; validation provenant d'autres circuits."""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
    from sklearn.tree import DecisionTreeClassifier

    if not train_rows or not validation_rows:
        raise ValueError("Données vides : augmenter le nombre de circuits.")
    x, y = [r[:-1] for r in train_rows], [r[-1] for r in train_rows]
    vx, vy = [r[:-1] for r in validation_rows], [r[-1] for r in validation_rows]
    if set(y) != {0, 1}:
        raise ValueError("Entraînement nécessite exemples avec et sans collision.")
    models = {
        "Arbre": DecisionTreeClassifier(max_depth=4, class_weight="balanced", random_state=0),
        "Forêt": RandomForestClassifier(n_estimators=40, max_depth=6, min_samples_leaf=10,
                                        class_weight="balanced", random_state=0, n_jobs=1),
    }
    reports = {}
    for name, model in models.items():
        model.fit(x, y)
        prediction = model.predict(vx)
        reports[name] = {
            "accuracy": accuracy_score(vy, prediction),
            "precision_collision": precision_score(vy, prediction, zero_division=0),
            "rappel_collision": recall_score(vy, prediction, zero_division=0),
            "f1_collision": f1_score(vy, prediction, zero_division=0),
        }
    return models, reports


def compare(policies, seeds):
    """Une ligne par conduite et circuit, conditions initiales communes."""
    rows = []
    for seed in seeds:
        for name, make in policies.items():
            agent = make()
            if getattr(agent, "learning", False):
                raise ValueError("Comparaison exige une politique figée.")
            traffic = run_circuit(seed, RulePolicy(), special={ALICE: agent})
            car = traffic.vehicles[ALICE]
            rows.append({
                "seed": seed, "conduite": name,
                "collisions_min": car.collisions / (EPISODE_TIME / 60),
                "tours": car.laps,
                "carburant_distance": car.fuel / max(car.distance, 1e-9),
            })
    return rows


def summarize(rows):
    """Moyenne et écart-type entre circuits, pas intervalle de confiance."""
    result = {}
    for name in sorted({r["conduite"] for r in rows}):
        result[name] = {}
        for metric in ("collisions_min", "tours", "carburant_distance"):
            values = [r[metric] for r in rows if r["conduite"] == name]
            result[name][metric] = {"moyenne": mean(values),
                                    "ecart_type": stdev(values) if len(values) > 1 else 0.0}
    return result


def main():
    """Entraîner supervisé, valider, comparer conduite et exporter résultats."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--circuits", type=int, default=30)
    parser.add_argument("--tests", type=int, default=10)
    args = parser.parse_args()
    if not 2 <= args.circuits <= 1000 or not 1 <= args.tests <= 1000:
        parser.error("circuits entre 2 et 1000, tests entre 1 et 1000")
    train_seeds = list(range(10_000, 10_000 + args.circuits))
    validation_seeds = list(range(5000, 5000 + max(2, args.circuits // 5)))
    test_seeds = list(range(args.tests))
    print("Collecte entraînement et validation (circuits disjoints)…", flush=True)
    train, groups = collect_groups(train_seeds)
    validation, validation_groups = collect_groups(validation_seeds)
    assert not set(groups) & set(validation_groups)
    models, predictions = fit_models(train, validation)
    save_model(models["Forêt"], FOREST_FILE)
    policies = {"Hasard": RandomPolicy, "Règle": RulePolicy}
    policies.update({name: lambda model=model: TreePolicy(model) for name, model in models.items()})
    missing = []
    try:
        AliceAgent.load(Q_ALICE_FILE)
        policies["RL ancien modèle"] = lambda: AliceAgent.load(Q_ALICE_FILE)
    except (OSError, ValueError):
        missing.append("RL : table absente ou invalide, comparaison omise")
    print("Comparaison conduite sur nouveaux circuits…", flush=True)
    rows = compare(policies, test_seeds)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (OUTPUT / "comparaison.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report = {"train_seeds": train_seeds, "validation_seeds": validation_seeds,
              "test_seeds": test_seeds, "features": FEATURES,
              "configuration": {"columns": FRAME_COLUMNS, "rows": FRAME_ROWS,
                                "roads": ROADS, "intersections": INTERSECTIONS,
                                "vehicles": VEHICLES, "seconds": EPISODE_TIME, "dt": DT},
              "predictions_validation": predictions, "conduite": summarize(rows),
              "avertissements": missing + ["RL ancien modèle non réentraîné après correction."]}
    (OUTPUT / "rapport.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(json.dumps(report["conduite"], indent=2, ensure_ascii=False))
    print(f"Résultats : {OUTPUT}")


if __name__ == "__main__":
    main()
