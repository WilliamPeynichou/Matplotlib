# Première expérience laboratoire

Commande : `.venv/bin/python ml_lab.py --circuits 10 --tests 5`.
Entraînement supervisé : seeds 10000–10009 ; validation : 5000–5001 ; conduite : 0–4, 60 secondes, 10 voitures, cadres 10×5, routes 3, intersections visées 6.

| Conduite | Collisions/min moyenne | Écart-type | Tours moyens |
|---|---:|---:|---:|
| Hasard | 9,0 | 3,74 | 1,0 |
| Règle | 3,0 | 3,67 | 1,4 |
| Arbre | 2,8 | 2,59 | 2,0 |
| Forêt | 2,8 | 1,92 | 1,8 |
| RL ancien modèle | 1,4 | 1,14 | 1,6 |

## Lecture honnête

Petit essai de fonctionnement, **pas preuve statistique**. La forêt ne réduit pas davantage les collisions que l'arbre ici. L'ancien RL obtient moins de collisions mais a été entraîné avant la correction d'anticipation : il faudra le réentraîner avant une comparaison actualisée. Les variations entre circuits sont importantes.

Fichiers détaillés : `data/lab/comparaison.csv` et `data/lab/rapport.json` (gitignorés). Modèle forêt : `forest_model.pkl`. Ce modèle se branche avec `TreePolicy` car les deux classifieurs proposent `predict_proba`. La fenêtre reste en mode Alice live ; ce laboratoire n'ajoute pas de bouton Forêt.

## Prochaine expérience

Augmenter budget d'entraînement et nombre de circuits de validation. Ne pas régler paramètres sur les résultats de conduite 0–4 ; garder un nouvel ensemble final indépendant pour la prochaine conclusion. Ajouter plusieurs entraînements RL et un journal des décisions avant envisager réseaux de neurones.
