# Features

Numérotées dans l'ordre des **rounds** : dans un round, les 3 devs codent 3 features **en même temps**, chacun dans **un fichier différent**.
Qui fait quoi : [planning.md](planning.md). Signatures : [contrat](architecture.md#contrat).

## Vue d'ensemble

| Round | # | Feature | Fichier |
|---|---|---|---|
| 0 | 1 | Environnement + contrat | requirements.txt, stubs |
| 1 | 2 | Données | models.py |
| 1 | 3 | Grille | network.py |
| 1 | 4 | Dessin | display.py |
| 2 | 5 | Chemin principal | generator.py |
| 2 | 6 | Randomize | display.py |
| 2 | 7 | Vérifications | check.py |
| 3 | 8 | Branches + intersections | generator.py |
| 3 | 9 | Animation (1 pt) | display.py |
| 3 | 10 | Seed | main.py |
| 4 | 11 | Visu enrichie + routes courbes (bonus) | display.py |
| 4 | 12 | Plus court chemin (bonus) | network.py |
| 4 | 13 | Documentation (bonus) | README.md + docstrings |

Chaque feature ci-dessous : **But** · **À faire** · **Terminé quand** · **Pièges** · **À expliquer à l'oral**.

---

## Round 0

### F1 – Environnement + contrat (tous)
**But** : les 3 ont le même environnement, et le squelette du projet existe pour pouvoir coder en parallèle.

**À faire**
1. Chacun : installer Python 3.14, créer le `.venv`, `pip install -r requirements.txt`, choisir l'interpréteur `.venv` dans VS Code.
2. Un dev crée le repo Git avec `.gitignore`, `requirements.txt` (`matplotlib==3.11.2`), `docs/`.
3. Un dev pousse les **stubs** : les 5 fichiers avec toutes les classes et fonctions du contrat, corps vide (`pass`) et docstring.
4. Les 2 autres clonent et lancent le test Matplotlib du cours (grille 5 × 3 + segment vert).

**Terminé quand** : les 3 ouvrent la fenêtre de test, les stubs sont sur `main`, `python main.py` ne plante pas (même s'il n'affiche rien).

**Pièges** : `python` vs `python3`, `requirements.txt.txt` sous Windows, scripts PowerShell bloqués (voir cours 1.3).

**À l'oral** : pourquoi un `.venv` (projet isolé et reproductible).

---

## Round 1 – Les briques

### F2 – Données (`models.py`)
**But** : définir les briques du graphe.

**À faire**
1. `NodeType(Enum)` avec UNUSED, START, END, CONNECTION, INTERSECTION.
2. `Node(x, y)` : attributs `x`, `y`, `type = NodeType.UNUSED`, `segments = []`.
3. `Node.update_type()` :
   - START et END ne changent jamais ;
   - 0 segment → UNUSED ;
   - 1 ou 2 segments → CONNECTION ;
   - 3 ou plus → INTERSECTION.
4. `Segment(start, end)` : attributs `start`, `end`.

**Terminé quand** : dans un petit test, un node avec 3 segments devient INTERSECTION, un START reste START.

**Pièges** : `segments = []` en valeur par défaut dans la signature (liste partagée entre tous les nodes) → le créer **dans** `__init__`.

**À l'oral** : pourquoi une Enum, pourquoi le node connaît ses segments.

### F3 – Grille (`network.py`)
**But** : le plateau de jeu : toutes les cases, et le seul moyen de relier deux cases.

**À faire**
1. `RoadNetwork(columns, rows)` : stocke la taille, `nodes = []`, `segments = []`, puis crée la grille.
2. `create_node(x, y)` : crée un Node et l'ajoute à `nodes`. Boucle colonne par colonne → l'index vaut `x * rows + y`.
3. `is_inside(x, y)` : `0 <= x < columns and 0 <= y < rows`.
4. `get_node(x, y)` : `None` si hors grille, sinon `nodes[x * rows + y]`.
5. `create_segment(a, b)` :
   - refuse si le segment existe déjà (dans un sens ou l'autre) → `None` ;
   - crée le Segment, l'ajoute à `segments` et aux `segments` des deux nodes ;
   - appelle `update_type()` sur les deux.
6. `reset()` : vide les segments, remet tous les nodes en UNUSED.

**Terminé quand** : grille 4 × 3 = 12 nodes, `get_node(3, 2)` renvoie le bon, relier 2 fois les mêmes nodes ne crée qu'un segment.

**Pièges** : confondre `x * rows + y` et `y * columns + x` ; oublier de mettre à jour les deux nodes.

**À l'oral** : la formule d'index (cours 1.7), pourquoi tout passe par `create_segment()`.

### F4 – Dessin (`display.py`)
**But** : voir le réseau à l'écran.

**À faire**
1. Constante `COLORS = {NodeType.UNUSED: "#D0D4DA", NodeType.START: ..., ...}` en haut du fichier.
2. `draw_node(ax, node)` : `ax.plot(node.x, node.y, marker="o", color=COLORS[node.type])`. Nodes UNUSED plus petits.
3. `draw_network(ax, network)` : d'abord tous les segments (`ax.plot([x1, x2], [y1, y2])`), puis tous les nodes (dessus).
4. `show(...)` version simple : `fig, ax = plt.subplots()`, `draw_network`, `ax.set_aspect("equal")`, axes cachés, `plt.show()`.

**Terminé quand** : avec un réseau fait à la main (3 nodes, 2 segments), on voit la grille, les segments et les bonnes couleurs.

**Pièges** : dessiner les nodes avant les segments (les traits passent par-dessus).

**À l'oral** : Figure vs Axes (cours 1.11), pourquoi display ne connaît pas le hasard.

---

## Round 2 – Le socle

### F5 – Chemin principal (`generator.py`)
**But** : générer la route principale START → END.

**À faire**
1. `find_path(network, rng, start)` :
   - part de `start`, avance d'une colonne à chaque tour ;
   - `dy = rng.choice([-1, 0, 1])`, on force à rester dans la grille (si `y + dy` sort, on prend `dy = 0`) ;
   - relie le node courant au suivant avec `create_segment()` ;
   - renvoie la liste des nodes traversés.
2. `generate_network(network, seed)` :
   - `rng = random.Random(seed)` ;
   - START = `get_node(0, rows // 2)` ;
   - `path = find_path(...)` ;
   - dernier node du chemin → END.

**Terminé quand** : sur 20 générations, START toujours au milieu de la 1ʳᵉ colonne, END toujours dans la dernière, jamais hors grille.

**Pièges** : utiliser `random.choice` global au lieu de `rng` (la seed ne marchera plus) ; marquer START **après** le chemin (sinon `update_type` l'écrase → d'où la règle « START/END ne changent jamais »).

**À l'oral** : « déplacements contraints », pourquoi `rng` est passé en paramètre.

### F6 – Randomize (`display.py`)
**But** : régénérer le réseau sans relancer le programme.

**À faire**
1. Dans `show()`, ajouter un bouton : `Button(fig.add_axes([...]), "Randomize")`.
2. Au clic : appeler `on_randomize()` (fourni par `main`, qui fait `reset()` + `generate_network()` et renvoie la nouvelle seed).
3. `ax.clear()`, redessiner avec `draw_network`, `fig.canvas.draw_idle()`.

**Terminé quand** : 20 clics d'affilée, nouveau réseau à chaque fois, aucun ancien trait qui reste.

**Pièges** : garder une référence au bouton (sinon Python le supprime et il ne répond plus) ; oublier `ax.clear()`.

**À l'oral** : le principe du callback (on donne une fonction au bouton, il l'appelle au clic).

### F7 – Vérifications (`check.py`)
**But** : trouver les bugs automatiquement au lieu de cliquer 100 fois.

**À faire**
1. Boucle sur 100 seeds : créer un réseau, `generate_network(network, seed)`.
2. Vérifier :
   - exactement 1 START et 1 END ;
   - tous les nodes des segments sont dans la grille ;
   - aucun segment en double ;
   - chaque node a le bon type selon son nombre de segments.
3. Afficher la seed de chaque réseau en erreur, puis « OK » à la fin.

**Terminé quand** : `python check.py` affiche OK, et affiche la seed si on casse volontairement une règle.

**Pièges** : ne pas importer `display` (pas de fenêtre dans un test).

**À l'oral** : comment on a trouvé nos bugs (seed affichée → bug reproduit).

---

## Round 3 – Les évolutions

### F8 – Branches + intersections (`generator.py`)
**But** : passer d'une route unique à un vrai réseau.

**À faire**
1. Après le chemin principal, choisir 2 à 4 nodes au hasard sur ce chemin (pas START, pas END).
2. Depuis chacun, relancer `find_path()` (même fonction) : la branche vise le END et s'arrête en retombant sur la route. Aucun cul-de-sac.
3. Si la branche arrive sur un node déjà utilisé : on crée le segment puis on s'arrête (fusion).
4. Une branche ne devient jamais END : elle se termine en CONNECTION.
5. Les intersections apparaissent seules grâce à `create_segment()` + `update_type()`.

**Terminé quand** : réseaux avec plusieurs chemins et des intersections visibles, `check.py` toujours OK.

**Pièges** : branche qui finit en cul-de-sac (ne garder que les cases d'où le END reste atteignable) ; branche qui écrase END.

**À l'oral** : réutiliser `find_path` = une seule règle à expliquer.

### F9 – Animation (`display.py`) – 1 point
**But** : voir le réseau se construire.

**À faire**
1. `FuncAnimation(fig, update, frames=len(network.segments), interval=50)`.
2. `update(i)` : dessine le segment `network.segments[i]` puis ses 2 nodes.
3. Relancer l'animation après chaque Randomize.
4. Garder l'objet animation dans une variable (sinon il s'arrête tout de suite).

**Terminé quand** : au lancement et après chaque Randomize, les segments apparaissent dans l'ordre de génération.

**Pièges** : animation supprimée faute de référence ; ancienne animation qui continue après un Randomize (l'arrêter avec `event_source.stop()`).

**À l'oral** : pourquoi l'ordre de la liste `segments` suffit (zéro code en plus dans le générateur).

### F10 – Seed (`main.py`)
**But** : pouvoir rejouer exactement un réseau.

**À faire**
1. `main()` : seed = nombre au hasard (`random.randint(0, 99999)`), ou valeur fixée en haut de `main.py` (`SEED = None` par défaut).
2. La passer à `generate_network()` et à `show()` pour l'afficher dans le titre (« Seed : 4821 »).
3. `on_randomize()` tire une nouvelle seed, régénère et la renvoie.
4. Afficher aussi la seed dans le terminal.

**Terminé quand** : en mettant `SEED = 4821`, deux lancements donnent exactement le même réseau.

**Pièges** : un seul `random` global utilisé ailleurs (le résultat change quand même) → tout doit passer par `rng`.

**À l'oral** : la seed de secours pour la démo, et le bug retrouvé grâce à elle.

---

## Round 4 – Bonus (seulement si 1 → 10 est stable)

### F11 – Visu enrichie + routes courbes (`display.py`)
**But** : rendu plus lisible, proche de l'exemple du cours.
**À faire** : route principale plus épaisse que les branches ; légende des 5 types ; fond sombre ; segments arrondis (courbes au lieu de lignes droites) ; surligner le chemin renvoyé par F12.
**Terminé quand** : un inconnu comprend l'image sans explication.
**Pièges** : ne rien changer dans `generator.py` : tout le rendu reste dans `display.py`.

### F12 – Plus court chemin (`network.py`)
**But** : algorithme avancé simple (bonus +0,5).
**À faire** : `get_shortest_path()` en BFS : file d'attente depuis START, un `set` des nodes visités (cours 1.8), un dict `parent` ; à END, remonter les parents → liste de nodes.
**Terminé quand** : le chemin renvoyé va de START à END et n'est jamais plus long que le chemin principal.
**Pièges** : oublier le `set` visités → boucle infinie sur les réseaux avec fusion.

### F13 – Documentation (`README.md` + docstrings)
**But** : bonus « documentation impeccable » (+0,5).
**À faire** : README (installation, lancement, contrôles, captures, features, qui a fait quoi) ; vérifier qu'il y a une docstring sur chaque classe et fonction ; mettre à jour `docs/` si le code a changé.
**Terminé quand** : quelqu'un d'extérieur installe et lance le projet en suivant seulement le README.

---

## Round 5 – Réglages et circulation

### F14 – Choisir routes et intersections (`generator.py`, `display.py`)
**But** : régler le réseau avec les curseurs au lieu de changer le code.

**À faire** : curseur routes 1–10, intersections visées 0–15. À chaque changement, refaire des essais avec la même seed et garder celui avec le plus de routes, puis l'écart le plus petit à la cible. Montrer le nombre réel ; signaler si la cible est impossible avec ce nombre de routes.

**Terminé quand** : déplacer les curseurs met à jour le réseau sans fermer la fenêtre. Le titre affiche le résultat réel.

### F15 – Véhicules et règle des 2 secondes (`traffic.py`, `display.py`)
**But** : faire avancer des points sur le réseau et les faire diverger aux intersections.

**À faire** : curseur 0–20 véhicules ; départs espacés au START ; déplacement continu en suivant les routes courbes. À une intersection, éviter les sorties prises par d'autres véhicules au même node dans les deux dernières secondes. Si toutes les sorties ont été prises, choisir une sortie différente de celle du dernier véhicule. Au bout du réseau, repartir du START. Afficher les véhicules en route et les divergences imposées.

**Limite explicite** : sur une sortie unique, divergence impossible ; le véhicule la prend.

**Terminé quand** : les véhicules bougent, le curseur change leur nombre et le test vérifie la règle.

### F16 – Tester trafic et génération (`check.py`)
Générer plusieurs réseaux et seeds ; vérifier START/END, grille, doublons, croisements, types, chemin BFS. Simuler des véhicules à pas fixe et contrôler les décisions dans la fenêtre de 2 secondes. Terminé quand `python check.py` affiche `OK`.

---

## Vérifications à chaque fin de round
- `python check.py` → OK (dès le round 2).
- 20 clics Randomize sans erreur.
- Grille petite (3 × 3) et grande (30 × 20).
