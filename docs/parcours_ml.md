# Audit du ML actuel et parcours pour apprendre

## 1. Objectif

Transformer RoadNetwork en laboratoire pédagogique : comprendre les décisions d'Alice, mesurer leurs effets et améliorer la conduite par des expériences reproductibles. Ce document est un **audit par lecture du code**, pas une nouvelle campagne de mesures. Les améliorations ci-dessous restent à réaliser.

Lire d'abord `ml_alice.md` pour le fonctionnement, puis `litterature_ml.md` pour les références scientifiques.

## 2. Ce qui existe vraiment

- `learning.py` : Q-learning en table. Une action = direction et allure, jusqu'à 9 choix. Les actions sans sortie sont exclues.
- `alice.py`, `AliceAgent` : état de 8 nombres, coût du carburant ajouté à la récompense.
- `LiveAlice` : table vide au départ, mises à jour pendant la conduite. Epsilon diminue selon les tours terminés, jusqu'à 0,05. Une diminution d'epsilon n'est pas une preuve de convergence.
- `train_alice` : 3000 épisodes par défaut, circuits d'entraînement tirés avec seeds >= 10 000. L'agent cesse d'apprendre après l'entraînement.
- `measure` : comparaison sur 30 seeds de test (0–29), autres voitures à la Règle. Résultats agrégés : collisions/min, tours, carburant/distance et allures.
- `tree_model.py` : arbre supervisé de profondeur 4, entraîné à prédire une collision entre deux décisions. Le risque estimé est combiné avec des pénalités manuelles pour choisir une action.
- `traffic.py` : physique et compteurs ; toutes les voitures du circuit utilisent longueurs et consommation. Les contacts sont comptés, pas bloquants.

**Deux problèmes différents :** arbre = prédire un événement ; RL = apprendre à choisir selon une récompense cumulée.

## 3. Points forts

1. Petite table inspectable : apprentissage explicable sans réseau de neurones.
2. Conduites interchangeables et références Hasard/Règle.
3. Entraînement RL et comparaison utilisent des plages de seeds distinctes.
4. Même physique pour tous ; seule Alice apprend dans son expérience.
5. Tests automatisés et simulateur utilisable sans fenêtre.
6. Plusieurs objectifs visibles : collisions, temps, carburant.

## 4. Limites constatées dans le code

### A. Estimation du danger incohérente avec les distances — priorité haute

Dans `learning.py:get_exit_state`, temps d'arrivée d'Alice = `1 / base_speed` et celui d'un autre véhicule = `(1 - progress) / speed`. Sur le circuit, la progression utilise pourtant la longueur réelle.

**Conséquence :** l'état peut classer une fusion comme dangereuse ou libre sur une estimation erronée.

**Correction proposée :** temps restant = longueur × progression restante / vitesse. Pour Alice, calculer la longueur de la sortie à allure normale. Adapter proprement la signature et conserver les tests du réseau simple. Ajouter un test où deux tronçons de longueurs différentes arrivent au même instant.

### B. Courbe d'entraînement ne suffit pas à prouver l'apprentissage

`train_alice` mesure les collisions pendant que la table ET epsilon changent. `draw_curve` compare ces circuits d'entraînement variables à un niveau Règle obtenu sur d'autres circuits.

**Conséquence :** courbe descriptive utile, mais pas comparaison contrôlée.

**Correction proposée :** à intervalles réguliers, copier la table et évaluer avec `learning=False`, `epsilon=0` sur un ensemble de validation fixe. Comparer aux mêmes circuits avec Règle, Hasard et table vide. Ne jamais mettre à jour la table pendant cette évaluation.

### C. Arbre : séparation aléatoire par ligne

`tree_model.py:train` utilise `train_test_split` sur les décisions. Des décisions d'un même circuit peuvent figurer dans les deux parties.

**Risque :** dépendances entre observations, performance possiblement trop optimiste. Ce risque n'est pas une fuite démontrée quantitativement dans cet audit.

**Correction proposée :** conserver `circuit_id` lors de la collecte et séparer les groupes de circuits. Cet identifiant sert au découpage, **pas comme feature** du modèle. Ajouter validation et test final distincts.

### D. Résultats agrégés sans incertitude

`measure` renvoie des moyennes, pas les résultats de chaque seed. Une seed d'entraînement ne couvre pas la variabilité de l'apprentissage.

**Correction proposée :** exporter une ligne par circuit, puis moyenne, écart-type et différences appariées entre conduites. Réentraîner avec plusieurs seeds d'agent. Présenter le nombre d'essais avec chaque résultat.

### E. Même environnement initial, pas même trafic exact

Une décision différente d'Alice influence les interactions et l'historique des passages. Les autres gardent leur conduite, mais leurs trajectoires ne restent pas nécessairement identiques.

**À dire :** mêmes conditions initiales et mêmes politiques de référence, pas « trafic exactement identique ».

### F. Compteurs de distance et carburant facturés au départ

`Traffic` ajoute longueur et consommation au moment du choix du segment, avant qu'il soit complètement parcouru.

**Limite :** fin d'épisode au milieu d'un segment = compteurs incluant le segment engagé. Ce sont des coûts engagés, pas exactement une distance déjà parcourue.

**Proposition :** documenter cette convention ou accumuler selon la progression ; si on change la récompense, tester sa cohérence avec ces compteurs.

### G. État incomplet et fins de cadre

L'état résume le trafic sans toutes les positions ni les vitesses relatives. Deux situations distinctes peuvent avoir le même état. De plus, `on_arrival` termine la transition RL à chaque END de cadre avec futur nul, même si la voiture poursuit le circuit.

**Conséquence :** modèle pédagogique simplifié ; pas de garantie qu'il capture tout le futur d'un tour. Ne pas affirmer qu'il trouve une conduite optimale.

**Proposition :** garder cette version comme référence, puis comparer une seule évolution à la fois : vitesse relative, ou transition continue entre cadres.

### H. Modes et sauvegardes

`LiveAlice` recalcule epsilon dans `choose`. Mettre uniquement `epsilon=0` ne suffit donc pas à créer un mode évaluation durable si on conserve l'apprentissage. Le chargement du JSON restaure la table, pas tout l'état d'un entraînement (progression d'exploration, RNG, historique).

**Proposition :** mode explicite apprendre/évaluer et sauvegarde des métadonnées. Tester qu'évaluer ne change ni table ni progression d'apprentissage. Signaler tout remplacement automatique d'un modèle manquant par la Règle dans les rapports.

## 5. Parcours pédagogique en six étapes

### Étape 1 — Comprendre une décision

**Notions :** état, action, récompense, politique.

**Exercice :** choisir une intersection ; écrire ce qu'Alice voit, ses actions possibles et les conséquences attendues. Lire `get_state`, `AliceAgent.choose`, `QAgent.learn`.

**Calcul à la main :** Q=2, récompense=-10, meilleur Q suivant=3, alpha=0,1, gamma=0,9 : nouvelle Q = 2 + 0,1 × (-10 + 0,9 × 3 - 2) = **1,07**. Le coût temps/carburant est volontairement omis dans cet exercice.

**Terminé quand :** tu peux expliquer pourquoi une collision diminue la note sans lire le code.

### Étape 2 — Rendre les décisions observables

**Notions :** exploration/exploitation, récompense décomposée.

**Feature L1 :** journal limité aux dernières décisions : état, choix, hasard ou meilleur score, epsilon, Q avant/après, collision, temps et carburant. Un choix aléatoire peut aussi tomber sur la meilleure action : journaliser la branche de sélection, pas déduire le hasard de l'action.

**Terminé quand :** tu expliques trois décisions réelles à partir du journal. Pas de nouvelle bibliothèque nécessaire.

### Étape 3 — Séparer apprendre et évaluer

**Notions :** validation, test final, référence.

**Features L2/L3 :** mode évaluation figé, correction des temps d'arrivée, runner commun configurable. Garder géométrie, nombre de voitures, durée et pas de simulation explicites : actuellement fenêtre et expérience hors fenêtre n'utilisent pas les mêmes réglages.

**Exercice :** comparer table vide, table entraînée, Hasard et Règle sur les mêmes conditions initiales.

**Terminé quand :** même expérience reproduit les résultats et le mode évaluation ne modifie pas la table.

### Étape 4 — Mesurer les variations

**Notions :** moyenne, écart-type, comparaison appariée, répétition.

**Feature L4 :** CSV par seed et courbes de validation périodique. Mesurer collisions/min, collisions/tour (seulement si tours terminés), temps/tour, carburant/distance et tours effectués. Une voiture lente peut avoir moins de collisions/min : ne pas lire cette métrique seule.

**Terminé quand :** tu sais expliquer pourquoi un beau tour ou une courbe lissée ne suffit pas.

### Étape 5 — Améliorer par expériences

**Notions :** hyperparamètre, ablation, compromis.

Changer **un seul facteur** : epsilon, alpha, poids carburant, ou retrait de l'information « derrière ». Même budget de simulation et mêmes circuits de validation. Éviter d'ajuster sur le test final ; le consulter seulement après choix de la configuration.

**Terminé quand :** trois fiches d'expérience avec hypothèse, résultat mesuré et conclusion, y compris une expérience qui échoue.

### Étape 6 — Revenir au supervisé

**Notions :** features/labels, classes rares, généralisation, précision/rappel.

**Feature L5 :** séparation par circuit, matrice de confusion, précision positive, rappel et F1. Avec les poids équilibrés de l'arbre, ses probabilités ne sont pas automatiquement calibrées au trafic réel. Ne pas annoncer « 70 % de risque » comme fréquence garantie.

**Terminé quand :** tu expliques pourquoi accuracy élevée peut masquer un modèle inutile et pourquoi bonne prédiction ne garantit pas bonne conduite.

## 6. Ordre des features et critères QA

1. **L1 — Journal** : borné en mémoire, aucune modification du comportement ; test d'une mise à jour connue.
2. **L2 — Modes** : évaluation sans mise à jour, reprise d'apprentissage contrôlée, reset explicite.
3. **L3 — Physique observée + runner** : temps d'arrivée corrects, configuration enregistrée, seed reproductible.
4. **L4 — Expériences** : résultats par seed, courbes de validation, plusieurs entraînements ; division par zéro impossible.
5. **L5 — Arbre** : aucun circuit partagé entre train/validation/test ; identifiant exclu des features.
6. **L6 — Sauvegarde pédagogique** : table, configuration, nombre de décisions et progression ; chargement vérifié.

À chaque feature : petite modification, test, `./run_checks.sh`, mise à jour des docs. Pas de réseau de neurones ni de grosse réorganisation pour le moment.

## 7. Modèle de fiche d'expérience

```markdown
# Expérience : [nom]
Hypothèse :
Référence :
Unique changement :
Configuration : géométrie, trafic, durée, dt, récompenses
Seeds entraînement / validation / test :
Budget : épisodes et décisions
Résultats par seed : fichier CSV
Résumé : moyenne, variation, collisions + mobilité + carburant
Conclusion : confirmé / infirmé / inconclusif
Limites et prochaine expérience :
```

## 8. Première session conseillée — environ une heure

- 15 min : lire une décision et calculer une mise à jour Q à la main.
- 20 min : suivre quelques décisions d'Alice et identifier les informations manquantes.
- 15 min : écrire une hypothèse testable et définir comment la mesurer.
- 10 min : expliquer différence entre courbe d'entraînement et évaluation figée.

**Réussite :** comprendre une décision et savoir comment vérifier une amélioration. Pas avoir le modèle le plus compliqué.
