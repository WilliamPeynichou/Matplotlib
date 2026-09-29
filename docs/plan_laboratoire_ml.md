# Plan : laboratoire ML simple

## Livré dans cette évolution

1. **Anticipation physique** : calculer temps d'arrivée avec longueur réelle. Conserver les états existants pour ne pas agrandir inutilement la table Q.
2. **Supervisé** : comparer arbre et Random Forest (ensemble de petits arbres). Même features et même règle de score : isoler effet du modèle.
3. **Données** : collecte par circuit ; groupes entraînement et validation disjoints. Identifiant du circuit jamais fourni au modèle.
4. **Comparaison** : Hasard, Règle, Arbre, Forêt et RL sur mêmes conditions initiales. Export CSV par seed et résumé moyenne/écart-type. RL chargé sans apprentissage ; signaler modèle absent, ne pas le remplacer silencieusement.
5. **QA** : tests temps d'arrivée, groupes disjoints, forêt et exports. Rapport JSON avec configuration et métriques positives (précision, rappel, F1).

Commande prévue : `.venv/bin/python ml_lab.py --circuits 30 --tests 10`.
Les seeds >= 10000 servent à entraîner les modèles supervisés ; 5000–5999 à valider leurs prédictions ; 0–999 à mesurer conduite. Ne pas régler les paramètres sur ce dernier ensemble.

## Étapes futures (non livrées)

- Journal décisions + mode apprendre/évaluer dans fenêtre.
- Plusieurs entraînements RL et validation périodique figée : courbe actuelle mélange epsilon et apprentissage.
- Features vitesses relatives : les ajouter seulement après établir référence mesurée.
- Régression temps de trajet : comparer d'abord à distance/vitesse ; ML seulement si interactions rendent formule insuffisante.
- PPO/SAC : seulement après physique accélération/freinage et actions continues. Pas besoin maintenant.

## Comprendre et expérimenter

Arbre/Forêt prédisent collision entre décisions ; Q-learning apprend valeur future d'une action. Un meilleur F1 ne garantit pas meilleure conduite. Lire collisions avec mobilité et carburant, jamais seules.
Changer un seul facteur, écrire hypothèse, noter seeds et configuration, comparer moyennes et variation. Les probabilités d'un modèle à classes pondérées ne sont pas nécessairement calibrées.

## Limites

Forêt plus coûteuse et moins lisible qu'arbre. La table RL existante a été entraînée avec ancienne anticipation : ses résultats après correction doivent être présentés comme ceux d'un ancien modèle, pas comme réentraînement. Un audit et des tests ne prouvent pas convergence ni conduite optimale. Les autres voitures suivent même politique mais leurs trajectoires peuvent changer en réaction à Alice.
