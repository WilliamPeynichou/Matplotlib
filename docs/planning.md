# Planning – 3 devs en parallèle

Principe : le projet avance par **rounds**. Dans chaque round, **A, B et C codent en même temps**, chacun une feature, chacun dans **son fichier**. On merge ensemble en fin de round, puis round suivant.

Les rôles **tournent** : chaque dev passe par models / network / generator / display → tout le monde sait tout expliquer à l'oral.

## Le plan

| Round | Quand | Dev A | Dev B | Dev C |
|---|---|---|---|---|
| 0 | S1 | **F1** env + stubs | **F1** env | **F1** env |
| 1 | S2, 1ʳᵉ moitié | **F2** données `models.py` | **F3** grille `network.py` | **F4** dessin `display.py` |
| 2 | S2, 2ᵉ moitié | **F6** Randomize `display.py` | **F5** chemin `generator.py` | **F7** vérifs `check.py` |
| 3 | S3, 1ʳᵉ moitié | **F8** branches `generator.py` | **F9** animation `display.py` | **F10** seed `main.py` |
| 4 | S3, 2ᵉ moitié | **F12** plus court chemin `network.py` | **F13** documentation `README.md` | **F11** visu enrichie `display.py` |
| 5 | S4 | slides 1-5 + test ZIP | slides 6, 7, 9 + captures | slides 8, 10, 11 + vidéo |

Récap par dev (tout le monde touche à tout) :
- **A** : models, display, generator, network
- **B** : network, generator, display, doc
- **C** : display, check, main, display

## Comment on bosse en même temps sans se bloquer

1. **Le contrat d'abord** (round 0) : les signatures des classes et fonctions sont écrites dans [architecture.md](architecture.md#contrat). A pousse des *stubs* (fonctions vides + docstring). À partir de là, personne n'attend personne.
2. **Un fichier par dev et par round** : jamais deux devs dans le même fichier en même temps.
3. **Coder contre le contrat** : si la feature d'un autre n'est pas finie, on utilise son stub ou de fausses données faites à la main pour tester.
4. **Une branche par feature** : `feature/F5-chemin`.
5. **Fin de round (20 min, ensemble)** :
   - chacun relit la feature d'un autre (A → B → C → A) ;
   - merge dans `main` dans l'ordre du numéro de feature ;
   - `python main.py` + `python check.py` ;
   - chacun explique sa feature aux deux autres en 2 min.
6. **Changer le contrat** : seulement en fin de round, à 3, et on met à jour `architecture.md`.

## Déroulé type d'un round (~1h30)

| Temps | Quoi |
|---|---|
| 5 min | stand-up : qui fait quoi, doutes sur le contrat |
| 1h05 | chacun code sa feature en parallèle |
| 20 min | fin de round : relecture, merge, test, explication |

## Jalons
- Fin round 2 : chemin START → END + Randomize → **tag `v0.1`**
- Fin round 3 : features 1 → 10 stables → **tag `v1.0`**, plus de nouveau code après, seulement des corrections
- Round 4 = bonus, abandonnable sans risque

## Si quelqu'un est en retard
- Sa feature passe au round suivant, les deux autres continuent.
- Ne jamais merger une feature cassée : `main` reste lançable.
- Le socle construit avec le prof en S2 prime : si ses noms diffèrent, on met à jour le contrat en fin de round.

## Soutenance
Voir [presentation.md](presentation.md).
