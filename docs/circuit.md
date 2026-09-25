# Feature Circuit : 4 cadres en boucle + voitures nominatives

## Idée
```
            Haut
     Cadre 0 ╱ ╲ Cadre 1
      Gauche     Droite
     Cadre 3 ╲ ╱ Cadre 2
            Bas
```
- 4 grilles (cadres). Chacune = un `RoadNetwork` normal : mêmes règles, mêmes tests.
- END du cadre i = START du cadre i+1 (même point à l'écran, appelé jonction).
- END du cadre 3 → START du cadre 0 = **un tour**.

## Fichiers
| Fichier | Changement |
|---|---|
| `circuit.py` (nouveau) | classe `Circuit` : 4 cadres, `generate`, `get_next_start`, `to_screen` |
| `generator.py` | `fixed_end=True` : END au milieu de la dernière colonne (jonction fixe) |
| `models.py` | `Node.frame` : numéro du cadre (None = réseau simple) |
| `network.py` | `get_next_start` : réseau simple = retour au START |
| `traffic.py` | prénoms uniques, tours, meilleur tour, collisions par voiture, classement |
| `display.py` | cadres pliés sur l'arc, prénoms à côté des voitures, classement en haut à gauche |
| `main.py` | `CIRCUIT = True/False`, `FRAME_COLUMNS`, `FRAME_ROWS` |

## Coordonnées (la « précision » de chaque cadre)
Chaque cadre garde son repère local `(x, y)`. Seul `to_screen(cadre, x, y)` le met à l'écran :
- `x` → avance sur un quart d'ellipse, de la jonction de départ à celle d'arrivée ;
- `y` → écart à l'arc (vers l'extérieur ou l'intérieur), réduit près des jonctions (`sin`) pour que les cadres se rejoignent.

Donc : le générateur et le trafic ne savent pas que c'est un circuit. Seul l'affichage plie.

## Voitures nominatives
- `make_name(n)` : Alice, Bruno, Chloé… puis « Alice 2 » au-delà de 20 → toujours unique.
- Chaque voiture : `name`, `laps`, `best_lap`, `collisions`. `Traffic.get_ranking()` = classement.

## ML
Rien à changer : l'état (descendre / tout droit / monter) reste local au cadre. « Arrivée » = fin d'un cadre (+1).

## Tests (`test_circuit.py`)
Règles de chaque cadre, START/END fixes, jonctions au même point, boucle fermée, même seed = même circuit, cadre trop petit = message clair, prénoms uniques, tours comptés, passage par les 4 cadres.
