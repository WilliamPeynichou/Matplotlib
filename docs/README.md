# Documentation – Projet RoadNetwork

Bootcamp Python B3 – Sup de Vinci 2026-2027. Groupe de 3.

Générer un réseau routier sur une grille (nodes + segments) et l'afficher avec Matplotlib. Principe : **simple à coder, simple à expliquer**.

| Document | Contenu |
|---|---|
| [architecture.md](architecture.md) | 5 fichiers, 4 classes, algo en 4 étapes, choix justifiés |
| [features.md](features.md) | F1–F16 : réseau, contrôles et circulation |
| [qualite.md](qualite.md) | 8 règles de code, Git, checklist |
| [planning.md](planning.md) | 3 devs en parallèle, rounds, rôles tournants |
| [evaluation.md](evaluation.md) | grille de notation → features |
| [presentation.md](presentation.md) | slides, script de démo, questions probables |

> Le socle de la séance 2 est construit avec le prof : ses noms priment, on adapte la doc ensuite.

## Ce qui vient du cours / ce qui est proposé

| Imposé par le cours (PDF) | Proposé par nous (modifiable) |
|---|---|
| Python 3.14, `.venv`, `matplotlib==3.11.2` | découpage en 5 fichiers |
| graphe nodes + segments, 5 types de node | noms `generate_path`, `show`, `get_node`, `is_inside` |
| `create_node()`, `create_segment()`, `draw_node()` | rôles A / B / C |
| START au milieu de la 1ʳᵉ colonne, chemin colonne par colonne | règles qualité (anglais, < 25 lignes, branches Git) |
| bouton Randomize, seed, branches, intersections | 11 slides, ~10 min |
| | rounds parallèles + contrat de signatures |
| livrables : ZIP + support exporté + oral | features bonus 11-13 (idées tirées du cours) |
| grille d'évaluation, bonus, malus | |

## À demander au prof
- Durée de la soutenance.
- Format attendu du support (PDF ?).
- Noms exacts du socle de la séance 2 → mettre à jour `architecture.md`.
