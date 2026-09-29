# Cours : architecture d'un petit laboratoire de Machine Learning

> Niveau débutant. Exemple : RoadNetwork et Alice. Objectif : comprendre **où placer chaque responsabilité**, pourquoi les séparer et comment les données circulent. Pas besoin de serveur, de base de données ou de réseau de neurones.

## 1. Architecture : qu'est-ce que c'est ?

L'architecture est l'organisation du programme : qui possède les données, qui décide, qui calcule et qui affiche.

Imagine un laboratoire :
- le **simulateur** est le terrain d'expérience ;
- la **politique** est le conducteur ;
- le **modèle** est ce que le conducteur a appris ;
- l'**évaluation** est l'examinateur ;
- l'**interface** est le tableau de bord.

Si l'examinateur entraîne le conducteur pendant son examen, on ne mesure plus une compétence figée. Si le tableau de bord change les règles physiques, la comparaison devient incohérente. L'architecture sert à éviter ces mélanges.

## 2. Les six responsabilités nécessaires

### A. Décrire le monde

**Fichiers :** `models.py`, `network.py`, `generator.py`, `circuit.py`.

Un point (`Node`), un tronçon (`Segment`), une grille (`RoadNetwork`) et quatre grilles reliées (`Circuit`). Le générateur crée les routes à partir d'une seed.

**Pourquoi séparé du ML ?** On doit pouvoir générer un circuit sans entraîner de modèle. On doit aussi pouvoir comparer plusieurs modèles sur un même type de circuit.

### B. Simuler ce qui se passe

**Fichier :** `traffic.py`.

`Traffic` possède les voitures et l'horloge. Il fait avancer les voitures, détecte les contacts et compte les tours. `Vehicle` garde position, vitesse et compteurs.

La physique doit être commune à toutes les conduites :

```text
vitesse = vitesse_de_base × multiplicateur_d'allure
progression supplémentaire = vitesse × dt / longueur
```

`dt` est le temps simulé entre deux mises à jour. Une longueur plus grande exige plus de temps à vitesse égale.

**Pourquoi ?** Si Alice bénéficie d'une physique différente, un meilleur résultat ne prouve pas que son modèle est meilleur.

### C. Choisir une action

**Fichiers :** `policies.py`, `learning.py`, `alice.py`, `tree_model.py`.

Toutes les conduites répondent à la même question :

```python
choose(traffic, vehicle, node, exits) -> (target, pace)
```

- `target` : prochaine destination ;
- `pace` : lent, normal ou rapide.

La règle manuelle, le hasard, l'arbre et le Q-learning respectent ce contrat. `Traffic` demande une action sans connaître l'algorithme utilisé.

**C'est un branchement interchangeable**, souvent appelé pattern Strategy. Pas besoin de retenir le nom : même prise, plusieurs conducteurs.

### D. Transformer le monde en informations utiles

**Fonctions :** `get_state`, `get_length_classes`, `get_features`.

Le modèle ne comprend pas directement un dessin Matplotlib. On lui fournit une description numérique : sorties libres ou dangereuses, présence derrière, classes de longueur, etc.

Cette transformation est la **construction des features**.

**Pourquoi un endroit commun ?** Une sortie ne doit pas signifier « dangereuse » à l'entraînement et « libre » en démo à cause de deux calculs différents. C'est un problème de cohérence entre entraînement et utilisation.

### E. Entraîner et évaluer

**Fichiers :** `alice.py`, `tree_model.py`, `ml_lab.py` ; aussi `train.py` et `evaluate.py` pour l'expérience historique.

L'entraînement modifie le modèle. L'évaluation mesure un modèle figé.

Deux métriques différentes :
- qualité de prédiction : précision positive, rappel, F1 ;
- qualité de conduite : collisions/min, tours, carburant/distance.

**Pourquoi deux niveaux ?** Un modèle peut prédire correctement le danger mais conduire mal si la règle qui transforme ses prédictions en actions est mauvaise.

### F. Afficher et conserver les résultats

**Fichiers :** `display.py`, JSON, CSV et modèles sauvegardés.

La fenêtre affiche et transmet les commandes utilisateur. Les exports permettent de retrouver les résultats sans regarder toute la simulation.

L'évaluation doit fonctionner **sans fenêtre** : sinon une expérience longue dépend de l'interface, du rythme d'affichage et de clics humains.

## 3. Schéma général : les responsabilités, pas les imports exacts

```text
main.py ───────────> fenêtre display.py
                         │ commandes / affichage
                         ▼
monde ──────────────> Traffic ──────demande──────> Policy
(grille, circuit)        │                         │
                        │                    features / modèle
                        │                         │
                        <──────── action ──────────┘
                        │
                   événements et compteurs
                        │
                collecte / apprentissage / évaluation
                        │
                    CSV, JSON, graphiques
```

Le **runner d'expérience** orchestre le même simulateur hors fenêtre. Il n'invente pas une deuxième physique.

## 4. Chemin d'une décision : exemple concret

1. Alice arrive à un node.
2. `Traffic` trouve les sorties possibles.
3. La politique observe la situation.
4. Elle choisit une destination et une allure.
5. `Traffic` applique ce choix et fait avancer Alice.
6. S'il y a contact, il appelle `on_collision`.
7. À la décision suivante, le Q-learning met à jour la note du choix précédent.
8. L'écran et les compteurs montrent le résultat.

**À retenir :** le modèle décide, le simulateur applique, l'évaluation mesure.

## 5. Architecture du supervisé : prédire une collision

```text
Simulation avec conduite au hasard
        ↓
RecorderPolicy observe situation + action
        ↓
Label : collision pendant ce segment, oui/non
        ↓
Séparation des circuits : train / validation
        ↓
Arbre ou Random Forest : fit(X, y)
        ↓
Prédictions sur validation : predict(X)
        ↓
TreePolicy : scores des actions → choix
        ↓
Simulation de conduite sur d'autres circuits
```

### Qu'est-ce qu'on stocke ?

- **X** : informations observées et action envisagée ;
- **y** : résultat observé, collision ou non ;
- **groupe** : circuit d'origine, pour séparer les données.

Le numéro du circuit **n'est pas une feature** : sinon le modèle pourrait apprendre un identifiant au lieu d'une situation.

### Modèle et politique : différence importante

Le classifieur renvoie un score de risque. La politique combine ce score avec pénalités de lenteur et carburant. Le classifieur ne choisit donc pas seul le prochain node.

Dans notre code, `TreePolicy` fonctionne aussi avec la forêt : les deux modèles ont `predict_proba`. Son nom vient du premier modèle utilisé, pas d'une restriction technique.

**Limite :** les scores d'un modèle entraîné avec classes pondérées ne sont pas automatiquement des probabilités calibrées au trafic réel.

## 6. Architecture du RL : apprendre en conduisant

Pas de tableau de bonnes réponses préparé à l'avance. Alice agit et reçoit une récompense.

```text
État s → action a → simulation → récompense r + nouvel état s'
  ↑                                             │
  └──────────── mise à jour de la table Q ───────┘
```

`QAgent` possède :
- `q` : notes apprises pour chaque état et action ;
- `memory` : décision encore en cours ;
- `epsilon` : part d'exploration ;
- `learning` : autorisation de modifier la table.

**Ne pas confondre table et mémoire :**
- conserver la table permet de réutiliser l'apprentissage ;
- conserver la décision d'un ancien véhicule sur un nouveau circuit serait une erreur.

C'est pourquoi le bouton **Garder apprent.** conserve la table mais efface les décisions en cours. Les nouvelles voitures ont des compteurs neufs.

Dans le code actuel, la fin de chaque cadre termine une transition RL avec futur nul. C'est une simplification : la voiture continue physiquement dans le cadre suivant. Une future expérience pourra comparer cette formulation à une transition continue.

## 7. Trois cycles de vie à ne pas mélanger

### Cycle de la simulation

Circuit, voitures, horloge, contacts, statistiques. Recommence quand on recrée la simulation.

### Cycle de l'apprentissage

Table Q ou classifieur, progression d'exploration, paramètres. Peut durer sur plusieurs simulations.

### Cycle d'une expérience

Configuration, seeds, données, modèle testé et résultats. Doit être identifiable pour comparer deux essais.

**Exemple :** nouveau circuit avec table conservée = nouvelle simulation, apprentissage continu. Ce n'est pas une remise à zéro complète.

## 8. Train, validation et test

- **Train** : apprendre les paramètres.
- **Validation** : choisir ou comparer des configurations pendant le développement.
- **Test final** : estimer résultat après avoir arrêté les choix.

Dans `ml_lab.py` : circuits d'entraînement à partir de 10000, validation à partir de 5000, comparaison de conduite à partir de 0. Les plages sont disjointes.

**Attention :** si on utilise souvent les circuits de comparaison pour ajuster le modèle, ils deviennent en pratique une validation. Pour annoncer un résultat final, réserver de nouveaux circuits non consultés.

Même seed et mêmes conditions initiales rendent comparaison reproductible. Cela ne garantit pas les mêmes trajectoires : les choix d'Alice peuvent influencer les autres voitures.

## 9. Le runner : chef d'orchestre

Le runner assemble :

```text
configuration + seeds + politique → simulation → résultats
```

Actuellement, `run_circuit` est dans `tree_model.py`, et `ml_lab.py` le réutilise. C'est simple, mais la fonction contient des réglages fixes définis dans ce module.

**Évolution conseillée, pas encore réalisée :** extraire un runner neutre avec configuration explicite, utilisé par collecte, RL et comparaison. Faire cela quand les expériences l'exigent ; pas besoin d'une grosse réorganisation aujourd'hui.

Un runner reproductible devrait enregistrer : géométrie, véhicules, durée, dt, seeds, paramètres du modèle, récompenses et version du code. Le rapport actuel enregistre une partie de ces informations, pas encore tout.

## 10. Ce que les fichiers sauvegardent

- `q_alice.json` : table Q ; pas tout l'état nécessaire pour reprendre exactement un entraînement.
- `forest_model.pkl` : classifieur entraîné.
- `data/lab/comparaison.csv` : une ligne par conduite et circuit.
- `data/lab/rapport.json` : configuration, seeds, métriques et avertissements.

**Sécurité :** ne jamais charger un fichier pickle provenant d'une source non fiable. Le chargement peut exécuter du code.

Pour une reprise complète du RL, il faudrait aussi versionner format des features, paramètres, progression et état du hasard. C'est une amélioration future.

## 11. Tester chaque frontière

- **Monde** : routes valides, pas d'impasses, boucle correcte.
- **Physique** : tronçon long prend plus de temps ; temps d'arrivée tient compte de la longueur.
- **Politique** : action toujours parmi sorties autorisées.
- **Apprentissage** : mise à jour Q vérifiable à la main.
- **Évaluation** : ne modifie pas le modèle.
- **Données** : aucun circuit partagé entre ensembles ; identifiant exclu des features.
- **Interface** : reset des compteurs, conservation explicite de la table.
- **Exports** : paramètres et résultats présents, divisions par zéro évitées.

Commande de contrôle : `./run_checks.sh`. Les tests vérifient des règles, pas que le modèle est optimal.

## 12. Ce qu'il ne faut pas ajouter maintenant

Pas besoin de microservices, API, base de données, GPU ou pipeline distribué. Le projet tient dans quelques modules Python et des fichiers locaux.

Un réseau de neurones ne corrige pas une mauvaise définition de l'état, un label erroné ou une évaluation biaisée. Commencer par données et mesures fiables.

## 13. Exercices pour vérifier ta compréhension

1. Alice choisit une sortie interdite : quelle frontière tester ? **Contrat de la politique.**
2. L'écran se ferme, mais expérience doit continuer : quelle séparation manque ? **Simulation hors interface.**
3. Nouveau circuit, ancienne table conservée : quoi effacer ? **Décisions en cours et statistiques de simulation ; pas table.**
4. Arbre a bon F1 mais beaucoup de collisions : que vérifier ? **Règle de choix des actions, distribution du trafic et métriques de conduite.**
5. Deux modèles donnent résultats différents : que garder identique ? **Conditions initiales, physique, durée, budget et protocole d'évaluation.**

## Résumé à retenir

**Monde → simulateur → observations → politique → action → conséquences → apprentissage ou évaluation → résultats.**

Bonne architecture ML = responsabilités séparées, mêmes contrats, données cohérentes et expériences reproductibles. Le modèle n'est qu'une partie du système.
