# Plan de présentation

Le cours demande de présenter : **problème, architecture, algorithme, features, difficultés et résultat**, puis une démo et des questions.
Le PDF ne donne pas la durée : la demander au prof. Base ci-dessous : **~10 min + questions**. Le cours demande une présentation « technique courte » et un support « synthétique » : si le temps est plus court, fusionner les slides 2-3 et 4-5.

Règle : chaque membre présente **la partie qu'il a codée** (A = données, B = génération, C = affichage).

## Slides

| # | Slide | Qui | Durée | Contenu | Visuel |
|---|---|---|---|---|---|
| 1 | Titre | A | 20 s | nom du projet, noms du groupe | capture d'un réseau généré |
| 2 | Le problème | A | 1 min | générer un réseau routier sur une grille. Réseau = graphe : nodes + segments | schéma 3 nodes reliés |
| 3 | Les 5 types de node | A | 40 s | UNUSED, START, END, CONNECTION, INTERSECTION + couleur | légende colorée |
| 4 | Architecture | A | 1 min 30 | 5 fichiers. Phrase : « briques / plateau / règles / écran / ON ». Une seule règle : generator ne dessine pas, display ne tire pas au hasard | schéma des imports |
| 5 | Les classes | A | 1 min | Node, Segment, RoadNetwork. `create_segment()` met à jour les types tout seul | mini-diagramme des classes |
| 6 | Algorithme | B | 2 min | 4 étapes : grille → chemin principal → branches → types automatiques. Même fonction `find_path` pour tout | 4 captures, une par étape |
| 7 | Seed | B | 40 s | même seed = même réseau → bug reproductible | 2 captures identiques |
| 8 | Affichage et animation | C | 1 min | couleurs par type, bouton Randomize, segments animés | capture + GIF |
| 8b | Comment on sait que ça marche | A | 1 min | `./run_checks.sh` en direct : ruff OK, 68 tests pytest, check.py OK. Exemple : test « toutes les routes vont au END » | capture du terminal vert |
| 9 | Difficultés | B + C | 1 min | 1 ou 2 vrais bugs : symptôme → cause → correction. Ex. : branches en cul-de-sac (→ viser le END), grille 1 colonne qui plantait (→ test + message clair), animation à 98 % CPU (→ blitting) | capture du bug |
| 10 | Démo live | C | 2 min | voir script ci-dessous | — |
| 11 | Bilan | tous | 30 s | ce qui marche, ce qu'on ajouterait avec plus de temps | — |

## Script de démo (2 min)
1. `python main.py` : la fenêtre s'ouvre, l'animation se joue.
2. Montrer START, END, une intersection.
3. Cliquer 3 fois sur Randomize : réseaux différents.
4. Relancer avec la seed de secours : même réseau qu'annoncé.
5. Montrer un bonus s'il existe (plus court chemin surligné).

Plan B si l'ordinateur plante : vidéo de la démo enregistrée à l'avance.

## Questions probables (chacun doit savoir répondre)
- Pourquoi une classe `Segment` et pas juste des coordonnées ?
- Comment un node devient INTERSECTION ?
- Comment évitez-vous de sortir de la grille ?
- À quoi sert la seed ?
- Pourquoi une liste plate pour les nodes ? Que fait `x * rows + y` ?
- Que se passe-t-il quand une branche touche un node déjà utilisé ?
- Pourquoi séparer `generator` et `display` ?
- Comment êtes-vous sûrs qu'il n'y a pas de cul-de-sac ? (règle `|y - end.y| <= end.x - x` + test)
- Pourquoi le blitting ? (redessin complet = 78 ms, trop lent pour 20 images/s)
- Comment marche l'animation ?
- Ouvre `create_segment()` et explique-la ligne par ligne.

Les réponses sont dans le tableau « Choix et justifications » de [architecture.md](architecture.md).

## Checklist avant l'oral
- [ ] Slides exportées (livrable ; PDF conseillé, le cours dit juste « exporté »)
- [ ] Archive ZIP testée sur un autre PC
- [ ] Seed de secours notée
- [ ] Vidéo de secours
- [ ] Répétition chronométrée faite au moins une fois
- [ ] Chacun a répondu aux questions ci-dessus sans regarder
