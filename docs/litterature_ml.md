# Fondements scientifiques et pistes d'evolution ML

Ce document relie les choix du projet a la litterature scientifique. Il ne cherche
pas a faire passer le simulateur pour un systeme de conduite autonome reel : il
s'agit d'un environnement pedagogique controle, utile pour comprendre comment on
formule, entraine et evalue un agent.

## Lecture rapide

Le projet suit une progression coherente avec l'histoire du machine learning :

1. une regle manuelle fournit une reference simple ;
2. un arbre de decision apprend a predire un risque a partir d'exemples ;
3. le Q-learning apprend une politique par interaction avec le simulateur ;
4. les collisions, le temps et le carburant forment plusieurs objectifs parfois
   incompatibles ;
5. l'evaluation sur de nouveaux circuits cherche a mesurer la generalisation.

La litterature soutient cette progression, mais elle montre aussi que la prochaine
priorite n'est pas necessairement un reseau de neurones. Il faut d'abord rendre la
separation des donnees, les metriques et l'incertitude experimentale plus solides.

## 1. Arbre de decision : apprendre a partir d'exemples

Dans `tree_model.py`, l'arbre recoit une description numerique de la situation et
estime le risque de collision pour chaque action possible. Cette logique appartient
a l'apprentissage supervise : les observations passees servent d'exemples etiquetes.

Quinlan presente ID3 comme une methode qui synthetise un arbre de decision a partir
d'exemples. Cette reference permet de situer l'arbre du projet dans la famille
historique des modeles a regles conditionnelles apprises, plutot que codees a la
main ([Quinlan, 1986](https://doi.org/10.1007/BF00116251)).

Dans le projet, l'arbre est pedagogiquement utile parce que ses decisions restent
inspectables. Il permet notamment de demander quelles variables ont ete utilisees
avant de passer a un modele plus difficile a expliquer.

## 2. Classes rares : une collision n'est pas un exemple ordinaire

Une collision est normalement beaucoup plus rare qu'une absence de collision. Dans
ce contexte, l'accuracy peut sembler bonne simplement parce que le modele predit
souvent la classe majoritaire.

Saito et Rehmsmeier montrent que les courbes ROC peuvent donner une impression
trompeuse sur des donnees desequilibrees, tandis que precision-rappel indique plus
directement la proportion de vrais positifs parmi les alertes produites
([Saito et Rehmsmeier, 2015](https://doi.org/10.1371/journal.pone.0118432)).

Application au projet : l'arbre devrait etre accompagne au minimum de la matrice de
confusion, de la precision, du rappel, du score F1 et de la courbe precision-rappel.
La classe positive doit etre definie explicitement comme `collision`.

## 3. Separer par circuit, pas seulement par ligne

Deux decisions prises sur le meme circuit ne sont pas entierement independantes :
elles partagent la geometrie, le trafic et une partie de leur histoire. Les placer
aleatoirement de part et d'autre de la frontiere train/test peut rendre le test trop
facile.

Roberts et ses collegues montrent que la validation croisee aleatoire sous-estime
l'erreur lorsque les observations possedent une structure temporelle, spatiale ou
hierarchique. Ils recommandent une separation par blocs adaptee a la dependance et a
la cible de generalisation
([Roberts et al., 2017, publication en ligne 2016](https://doi.org/10.1111/ecog.02881)).
Kapoor et Narayanan documentent plus largement le role des fuites de donnees dans la
crise de reproductibilite des travaux scientifiques bases sur le ML
([Kapoor et Narayanan, 2023](https://doi.org/10.1016/j.patter.2023.100804)).

Application au projet : ajouter un identifiant de circuit a chaque decision, puis
utiliser des groupes de circuits disjoints pour l'entrainement, la validation et le
test. Le test final doit rester intact jusqu'a la fin du choix des features et des
hyperparametres.

## 4. Q-learning : apprendre par essais et consequences

Le Q-learning de `learning.py` associe une valeur a chaque couple etat-action. La
mise a jour rapproche l'ancienne valeur de la recompense recue et de la meilleure
valeur future estimee. Watkins et Dayan constituent la reference fondatrice pour
l'analyse de cet algorithme tabulaire
([Watkins et Dayan, 1992](https://doi.org/10.1007/BF00992698)).

La synthese de Kaelbling, Littman et Moore definit le reinforcement learning comme
l'apprentissage par interactions d'essai-erreur avec un environnement dynamique.
Elle identifie deja les questions centrales presentes dans ce projet : compromis
exploration-exploitation, recompenses retardees, generalisation et etat cache
([Kaelbling et al., 1996](https://doi.org/10.1613/jair.301)).

Application au projet : la politique `epsilon-greedy` alterne exploration et
exploitation. La table Q est un bon choix tant que l'espace discret reste petit, car
chaque valeur apprise peut etre inspectee.

## 5. La recompense definit le comportement recherche

Le projet combine collision, arrivee, temps et carburant en une recompense scalaire.
Ces coefficients ne sont pas des constantes naturelles : ils expriment une
preference humaine.

Les travaux sur le reward shaping montrent qu'ajouter des recompenses auxiliaires
peut modifier l'apprentissage et, si la transformation est mal choisie, modifier la
politique optimale. Les transformations basees sur un potentiel ont ete proposees
pour conserver cette politique
([Ng, Harada et Russell, 1999](https://doi.org/10.5555/645528.657613)).
Des travaux plus recents insistent aussi sur le fait que plusieurs recompenses
compatibles avec le meme comportement final peuvent produire des vitesses
d'apprentissage tres differentes
([Sowerby, Zhou et Littman, 2022, prepublication](https://arxiv.org/abs/2205.15400)).

Application au projet : entrainer separement une Alice prudente, rapide, economique
et equilibree permettrait de montrer que changer la fonction objectif change la
politique apprise.

## 6. Plusieurs objectifs, donc plusieurs bonnes politiques possibles

Une politique peut reduire les collisions au prix d'un trajet plus long ou d'une
consommation plus elevee. Il n'existe alors pas necessairement un unique gagnant.

Roijers et ses collegues expliquent que la reduction de plusieurs objectifs a une
seule somme ponderee peut etre impossible, indesirable ou insuffisante selon le
probleme. La solution peut etre une politique unique, une enveloppe convexe ou un
front de Pareto
([Roijers et al., 2013](https://doi.org/10.1613/jair.3987)).

Application au projet : conserver separement les quatre mesures brutes, tracer les
compromis et ne calculer un score global qu'apres avoir declare les poids. Une piste
avancee consisterait a apprendre plusieurs politiques placees sur le front de Pareto.

## 7. Etat incomplet et memoire

Alice ne voit qu'un resume local du trafic. Deux situations reellement differentes
peuvent donc produire le meme etat discret. Le probleme se rapproche alors d'un
processus de decision partiellement observable.

Kaelbling, Littman et Cassandra expliquent que, lorsque l'etat reel n'est pas
directement observable, une decision peut devoir reposer sur une croyance construite
a partir de l'historique des observations et des actions
([Kaelbling, Littman et Cassandra, 1998](https://doi.org/10.1016/S0004-3702(98)00023-X)).

Application au projet : avant d'introduire un reseau recurrent, on peut simplement
ajouter les deux ou trois observations precedentes a l'etat et mesurer si cette
memoire reduit les collisions.

## 8. Evaluer un agent avec de l'incertitude

Une moyenne sur quelques seeds ne montre pas si l'avantage est stable. Henderson et
ses collegues soulignent que la variance propre aux algorithmes et aux environnements
rend les comparaisons RL difficiles sans metriques de significativite et protocole
standardise
([Henderson et al., 2017, prepublication](https://arxiv.org/abs/1709.06560)).
Agarwal et ses collegues montrent que des conclusions fondees uniquement sur des
estimations ponctuelles peuvent differer de celles obtenues avec une analyse
statistique plus complete. Ils recommandent des estimations par intervalle et des
agregats robustes
([Agarwal et al., 2021, prepublication](https://arxiv.org/abs/2108.13264)).

Application au projet : comparer les politiques sur les memes circuits, calculer la
difference par circuit, puis rapporter moyenne ou mediane avec intervalle de
confiance. La seed et la version de la table Q doivent etre conservees avec chaque
resultat.

## 9. Quand passer au DQN

Une table Q devient peu pratique lorsque le nombre d'etats explose. Le DQN remplace
la table par un reseau qui approxime la valeur des actions. Le travail de Mnih et ses
collegues a montre qu'un reseau convolutionnel entraine avec une variante du
Q-learning pouvait apprendre des politiques a partir d'entrees visuelles de grande
dimension sur des jeux Atari
([Mnih et al., 2013, prepublication](https://arxiv.org/abs/1312.5602)). Une synthese
pedagogique du deep RL et de ses principaux mecanismes est fournie par
[Francois-Lavet et al., 2018](https://doi.org/10.1561/2200000071).

Application au projet : un DQN est justifie apres avoir enrichi l'etat au point que
la table ne visite plus suffisamment les combinaisons possibles. Le simple fait qu'un
reseau soit plus moderne ne garantit pas une meilleure politique ni une meilleure
evaluation.

## 10. De l'agent unique au multi-agent

Avec plusieurs agents apprenants, chaque voiture modifie l'environnement des autres.
Le probleme devient non stationnaire et plus difficile a attribuer a une seule
decision. La revue de Gronauer et Diepold organise les principales familles de deep
RL multi-agent et leurs difficultes
([Gronauer et Diepold, 2021](https://doi.org/10.1007/s10462-021-09996-w)).

Application au projet : conserver d'abord Alice comme seul agent apprenant est une
bonne experience controlee. L'etape multi-agent doit venir apres la stabilisation du
protocole mono-agent.

## 11. Limite de l'analogie avec la conduite autonome

La litterature sur la conduite autonome confirme l'interet du deep RL pour des taches
de decision complexes, mais elle insiste aussi sur les enjeux de simulation, de test,
de robustesse et de deploiement reel
([Kiran et al., 2021](https://doi.org/10.1109/TITS.2021.3054625)).

Le projet actuel ne modele pas encore la dynamique continue, les capteurs, les regles
de priorite, les pietons ou le passage du simulateur au monde reel. Ses conclusions
doivent donc rester formulees comme des resultats internes au simulateur, pas comme
des preuves de securite routiere.

## Roadmap fondee sur ces sources

### Phase 1 - Evaluation fiable

- ajouter `circuit_id` et `episode_id` aux observations ;
- separer train, validation et test par circuit ;
- ajouter matrice de confusion, precision, rappel, F1 et PR-AUC ;
- comparer les politiques sur les memes seeds ;
- fournir intervalles de confiance et distributions, pas seulement les moyennes.

### Phase 2 - Comprendre le comportement

- realiser des ablations de features ;
- comparer plusieurs fonctions de recompense ;
- afficher separement securite, temps, debit et carburant ;
- tracer les compromis et identifier les politiques non dominees.

### Phase 3 - Enrichir le reinforcement learning

- comparer Q-learning, SARSA et Double Q-learning dans le meme protocole ;
- ajouter une courte memoire des observations ;
- mesurer la couverture de la table Q et les etats inconnus ;
- ne passer au DQN que lorsque l'explosion de l'espace d'etats est mesuree.

### Phase 4 - Augmenter le realisme

- introduire plusieurs agents apprenants de maniere controlee ;
- ajouter acceleration, freinage et priorites ;
- tester des changements de distribution : nouveaux graphes, densites et profils ;
- distinguer clairement performance dans le simulateur et validite externe.

## Parcours de lecture conseille

1. [Kaelbling et al. (1996)](https://doi.org/10.1613/jair.301) pour la vue d'ensemble du RL.
2. [Watkins et Dayan (1992)](https://doi.org/10.1007/BF00992698) pour le Q-learning tabulaire.
3. [Saito et Rehmsmeier (2015)](https://doi.org/10.1371/journal.pone.0118432) pour les metriques de collision rare.
4. [Roberts et al. (2017)](https://doi.org/10.1111/ecog.02881) pour la separation par groupes.
5. [Henderson et al. (2017)](https://arxiv.org/abs/1709.06560) et [Agarwal et al. (2021)](https://arxiv.org/abs/2108.13264) pour l'evaluation statistique du RL.
6. [Roijers et al. (2013)](https://doi.org/10.1613/jair.3987) pour les objectifs multiples.
7. [Mnih et al. (2013)](https://arxiv.org/abs/1312.5602) seulement au moment de passer au DQN.

## Methode de recherche et limites documentaires

Recherche effectuee sans restriction de date, avec priorite aux textes fondateurs et
aux syntheses directement applicables au projet. Les candidats ont ete recherches
dans OpenAlex et arXiv, dedupliques par DOI ou identifiant arXiv, puis lus au minimum
au niveau du resume ou de la page integrale disponible. Les references recentes de
2025-2026 qui partageaient seulement des mots-cles ont ete ecartees.

Plusieurs editeurs n'ont fourni que le resume dans l'acces automatise. Les affirmations
associees restent donc volontairement limitees a ce que ces resumes etablissent. Les
liens DOI pointent vers les versions publiees ; les liens arXiv sont marques comme
prepublications lorsqu'aucune version publiee n'a ete utilisee ici.

## Bibliographie verifiee

- Agarwal, R., Schwarzer, M., Castro, P. S. et al. (2021). *Deep
  Reinforcement Learning at the Edge of the Statistical Precipice*.
  [arXiv:2108.13264](https://arxiv.org/abs/2108.13264).
- Francois-Lavet, V., Henderson, P., Islam, R. et al. (2018). *An
  Introduction to Deep Reinforcement Learning*.
  [DOI](https://doi.org/10.1561/2200000071).
- Gronauer, S. et Diepold, K. (2021). *Multi-agent deep reinforcement
  learning: a survey*. [DOI](https://doi.org/10.1007/s10462-021-09996-w).
- Henderson, P., Islam, R., Bachman, P. et al. (2017). *Deep Reinforcement
  Learning that Matters*. [arXiv:1709.06560](https://arxiv.org/abs/1709.06560).
- Kaelbling, L. P., Littman, M. L. et Cassandra, A. R. (1998). *Planning and
  acting in partially observable stochastic domains*.
  [DOI](https://doi.org/10.1016/S0004-3702(98)00023-X).
- Kaelbling, L. P., Littman, M. L. et Moore, A. W. (1996). *Reinforcement
  Learning: A Survey*. [DOI](https://doi.org/10.1613/jair.301).
- Kapoor, S. et Narayanan, A. (2023). *Leakage and the reproducibility crisis
  in machine-learning-based science*.
  [DOI](https://doi.org/10.1016/j.patter.2023.100804).
- Kiran, B. R., Sobh, I., Talpaert, V. et al. (2021). *Deep Reinforcement
  Learning for Autonomous Driving: A Survey*.
  [DOI](https://doi.org/10.1109/TITS.2021.3054625).
- Mnih, V., Kavukcuoglu, K., Silver, D. et al. (2013). *Playing Atari with
  Deep Reinforcement Learning*.
  [arXiv:1312.5602](https://arxiv.org/abs/1312.5602).
- Ng, A. Y., Harada, D. et Russell, S. J. (1999). *Policy Invariance Under
  Reward Transformations: Theory and Application to Reward Shaping*.
  [DOI](https://doi.org/10.5555/645528.657613).
- Quinlan, J. R. (1986). *Induction of decision trees*.
  [DOI](https://doi.org/10.1007/BF00116251).
- Roberts, D. R., Bahn, V., Ciuti, S. et al. (2017). *Cross-validation
  strategies for data with temporal, spatial, hierarchical, or phylogenetic
  structure*. [DOI](https://doi.org/10.1111/ecog.02881).
- Roijers, D. M., Vamplew, P., Whiteson, S. et Dazeley, R. (2013). *A Survey
  of Multi-Objective Sequential Decision-Making*.
  [DOI](https://doi.org/10.1613/jair.3987).
- Saito, T. et Rehmsmeier, M. (2015). *The Precision-Recall Plot Is More
  Informative than the ROC Plot When Evaluating Binary Classifiers on
  Imbalanced Datasets*.
  [DOI](https://doi.org/10.1371/journal.pone.0118432).
- Sowerby, K., Zhou, Z. et Littman, M. L. (2022). *Designing Rewards for Fast
  Learning*. [arXiv:2205.15400](https://arxiv.org/abs/2205.15400).
- Watkins, C. J. C. H. et Dayan, P. (1992). *Q-learning*.
  [DOI](https://doi.org/10.1007/BF00992698).
