# Présenter RoadNetwork en 10 minutes — version simple

> Objectif : expliquer ce que fait le projet, montrer une démo, puis prouver qu'Alice apprend. Ce texte est un **script à dire**, pas une liste de tous les fichiers.

## L'idée en une phrase

« On génère un circuit routier avec plusieurs chemins. Des voitures y roulent. Une voiture, Alice, essaie d'apprendre à choisir son chemin et sa vitesse pour éviter les collisions. »

## 0:00–1:00 — Le problème

« Le projet part d'une grille de points. On relie certains points pour créer des routes, puis on fait rouler des voitures dessus. Le défi : produire des routes cohérentes, faire circuler les voitures et vérifier si une conduite qui apprend fait mieux qu'une règle fixe. »

**Mots simples :** un **node** est un point ; un **segment** est une route entre deux points ; une **intersection** est un point avec plusieurs routes.

## 1:00–2:30 — Comment les routes sont créées

« Le générateur part du START, avance de colonne en colonne et construit un chemin jusqu'au END. Il ajoute ensuite des branches qui rejoignent une route existante. Il évite les impasses et les croisements en X. Avec une *seed*, le même nombre produit toujours le même circuit : pratique pour rejouer un bug. »

« Notre circuit contient **quatre grilles**. Le END d'une grille rejoint le START de la suivante ; la quatrième revient à la première. Les voitures peuvent donc faire des tours. »

**À montrer :** une intersection et la boucle de quatre cadres.

## 2:30–3:30 — Architecture sans jargon

- `models.py` : points et segments, les briques.
- `network.py` + `generator.py` : la grille et la création des routes.
- `circuit.py` : relie quatre grilles en boucle.
- `traffic.py` + `policies.py` : déplacement, collisions et conduite des voitures.
- `learning.py` + `alice.py` : apprentissage d'Alice.
- `display.py` + `main.py` : fenêtre et démarrage.

« Chaque fichier a un rôle. Le générateur ne dessine pas ; l'affichage ne décide pas comment Alice conduit. Ça permet de tester séparément. »

## 3:30–5:00 — Comment roulent les voitures

« Chaque voiture a son prénom, sa vitesse de base, son parcours, ses tours et ses collisions. À chaque point, une *conduite* choisit la prochaine sortie et une allure : lente, normale ou rapide. »

« La conduite **Règle**, utilisée par les autres voitures, essaie de prendre une autre sortie si quelqu'un est passé à cette intersection dans les deux dernières secondes. Alice seule peut utiliser une conduite qui apprend. »

« Toutes les voitures respectent la même physique : un tronçon plus long prend plus de temps ; rouler vite consomme plus de carburant. Une collision est comptée quand des voitures entrent en contact : elles ne s'arrêtent pas, pour que la simulation et l'apprentissage continuent. »

## 5:00–6:45 — Comment Alice apprend, très simplement

« Alice fait du **Q-learning** : elle garde un tableau de notes. La clé est une situation observée ; pour chaque choix possible, elle note si ce choix a été utile. Un choix combine une direction et une allure. Elle observe les sorties, les voitures proches et la longueur des routes. »

« Une collision lui coûte **−10** ; atteindre la fin d'un cadre rapporte **+1** ; le temps et le carburant ont aussi un coût. Après un choix, elle corrige la note selon ce qui s'est passé. Au début, elle essaie beaucoup de choix au hasard. À chaque tour, cette part de hasard baisse ; elle utilise de plus en plus ses notes. »

**Exemple oral :** « Tout droit + rapide provoque une collision ? Sa note baisse. La prochaine fois qu'elle reconnaît une situation semblable, elle peut choisir autrement. »

**Nuance importante :** elle apprend à **chaque décision**, pas seulement en fin de tour. Le nombre de tours sert à réduire progressivement le hasard. Les autres voitures ne modifient aucune table.

## 6:45–8:30 — Démo en direct

1. Lancer `.venv/bin/python main.py` avant l'oral, puis montrer le circuit et les prénoms. Par défaut, `ALICE = "live"` et `SPEEDUP = 10`.
2. Montrer les informations d'Alice : tours, collisions par tour, pourcentage de hasard (`epsilon`), nombre de situations apprises. **Au départ : table vide.**
3. Cliquer **Randomize** : nouveau circuit, statistiques à zéro, apprentissage d'Alice à zéro.
4. Après quelques tours, cliquer **Garder apprent.** : nouveau circuit, statistiques à zéro, mais table de connaissances conservée. Vérifier que le nombre d'états appris reste non nul. Le hasard repart selon les tours du nouveau circuit.
5. Expliquer les curseurs routes, intersections et véhicules. Éviter de promettre une baisse à chaque tour : les collisions fluctuent.

**Plan B si la fenêtre ne marche pas :** montrer `docs/images/alice_apprentissage.png` et `docs/images/alice.png`.

## 8:30–9:30 — Résultat et limites

« Dans l'expérience **hors fenêtre** (3000 épisodes d'entraînement, puis 30 circuits de test jamais vus), Alice avec Q-learning a environ **1,53 collision/min**, contre **3,23** avec la Règle. C'est une comparaison sur plusieurs circuits, pas la promesse que chaque tour en direct sera meilleur. »

« En direct, la mesure est plus bruitée : un circuit peut être facile ou difficile. La moyenne sur plusieurs tours est plus fiable qu'un seul tour. Le modèle est volontairement simple : une table lisible, pas un réseau de neurones. »

## 9:30–10:00 — Conclusion

« On a séparé trois problèmes : fabriquer le circuit, simuler la circulation, puis laisser Alice apprendre. Même physique pour toutes les voitures ; seule Alice change de conduite. On peut le vérifier avec des tests automatisés et des mesures sur des circuits jamais vus. »

## Questions probables — réponses courtes

- **Pourquoi quatre grilles ?** Pour former une boucle et mesurer des tours ; chaque grille reste un réseau simple.
- **Pourquoi une seed ?** Pour reproduire exactement un circuit.
- **Qu'est-ce qu'Alice apprend ?** La valeur de chaque couple direction + allure selon la situation.
- **Apprend-elle uniquement à la fin du tour ?** Non : mise à jour à chaque décision ; les tours règlent la part de hasard.
- **Pourquoi les autres voitures n'apprennent pas ?** Pour isoler l'effet d'Alice en gardant une référence stable.
- **Pourquoi deux boutons ?** `Randomize` efface apprentissage et statistiques ; `Garder apprent.` conserve seulement la table Q, pas les compteurs.
- **Pourquoi collisions pas toujours décroissantes ?** Hasard, trafic et circuits différents : comparer des moyennes, pas des tours isolés.
- **Comment vérifier ?** `./run_checks.sh` lance contrôles de style, tests et vérifications de simulation.

## À retenir si tu bloques

**Grille → routes → circuit → voitures → décisions → récompenses → Alice apprend → comparaison.**
