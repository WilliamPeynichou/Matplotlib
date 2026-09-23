# Qualité

## 8 règles de code
1. Noms en anglais, `snake_case` ; classes en `PascalCase` ; constantes en `MAJUSCULES`.
2. Fonctions qui commencent par un verbe : `create_`, `draw_`, `get_`, `generate_`.
3. Une fonction = une tâche, courte (< 25 lignes).
4. `NodeType.START`, jamais `"start"`.
5. Pas de nombre magique : couleurs et tailles en constantes en haut du fichier.
6. Relier deux nodes = toujours `create_segment()`.
7. Une docstring d'une ligne par classe et par fonction.
8. `main.py` : `main()` + `if __name__ == "__main__":`.

## Git
- `main` marche toujours.
- Une branche par feature : `feature/F5-chemin`.
- Dans un round, un seul dev par fichier.
- Un autre membre relit avant de merger.

## Avant chaque merge
- [ ] `python main.py` se lance
- [ ] 20 Randomize sans erreur
- [ ] Je sais expliquer mon code à voix haute en 1 minute

## Honnêteté
Pas de copier-coller non compris (malus −2). Chacun doit pouvoir expliquer tout le projet.
