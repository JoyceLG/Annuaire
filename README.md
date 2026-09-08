# Annuaire des astronautes — Session 14 : valider avec un outil

`validation.py` disparaît. Pydantic v2 reprend tout le travail, et le fait
mieux.

> Projet fil rouge de la formation « Flask, puis FastAPI ».
> Un commit par session : `git log --oneline` retrace la progression du code.

## Ce que cette session apporte

- Un schéma par usage dans `schemas.py` : ce que l'API accepte est désormais
  **déclaré**, plus vérifié à la main.
- `strict=True` : pas de conversion implicite. Sans lui, la chaîne `"3"` passe
  pour un entier et un booléen se déduit d'un nombre — des règles silencieuses
  qu'on n'a jamais demandées.
- `extra="forbid"` : un champ inconnu est refusé, pas ignoré.
- `Literal[...]` pour les valeurs fermées (les rôles), et des types annotés
  réutilisables plutôt que la même contrainte recopiée dans chaque schéma.
- `exclude_unset=True` : c'est ce qui donne enfin à `PATCH` sa vraie
  sémantique — distinguer « champ absent » de « champ mis à null ».
- L'outil arrive **après** avoir souffert du problème : la validation manuelle
  des sessions 7 à 13 a montré ce qu'elle coûtait à maintenir.

## Lancer

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install "flask>=3.1" "sqlalchemy>=2.0" alembic "pydantic>=2" pytest

alembic upgrade head
python peupler.py
flask --app app run --debug        # http://127.0.0.1:5000
pytest -q                          # 64 tests
```
