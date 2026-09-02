# Annuaire des astronautes — Session 12 : les migrations

Le schéma de la base a maintenant un historique, versionné à côté du code.
Ajouter une colonne ne demande plus de détruire la base.

> Projet fil rouge de la formation « Flask, puis FastAPI ».
> Un commit par session : `git log --oneline` retrace la progression du code.

## Ce que cette session apporte

- Alembic : chaque changement de schéma devient un fichier de révision, avec un
  `upgrade()` et un `downgrade()`, appliqué dans l'ordre sur n'importe quelle
  base.
- **`create_all()` et Alembic ne cohabitent pas.** Laisser les deux en place
  produit une base dont Alembic ignore l'état réel, et un « duplicate column »
  à la première migration.
- Les **migrations de données** : une nouvelle colonne `NOT NULL` sur une table
  déjà peuplée ne se fait pas en une étape. Ajouter, remplir avec un `UPDATE`
  en SQL brut, puis contraindre.
- `server_default` : la valeur que la **base** donne aux lignes existantes, à
  distinguer du `default` que Python applique aux nouvelles.
- Une migration de données testée sur une base vide n'a jamais rien migré : il
  faut la vérifier sur des lignes réelles.

## Lancer

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install "flask>=3.1" "sqlalchemy>=2.0" alembic pytest

alembic upgrade head               # crée / met à jour la base
python peupler.py                  # 5 astronautes Apollo
flask --app app run --debug        # http://127.0.0.1:5000
pytest -q                          # 24 tests
```

## Alembic au quotidien

```bash
alembic current                                  # où en est la base
alembic history                                  # les révisions connues
alembic downgrade -1                             # revenir d'un cran
alembic revision --autogenerate -m "message"     # après modification de modeles.py
```

## Attention aux deux URL

L'URL de la base est écrite à **deux** endroits : `sqlalchemy.url` dans
`alembic.ini` (migrations) et `create_engine(...)` dans `bdd.py` (application).
Comme elle est relative, toutes les commandes doivent être lancées depuis la
racine du dépôt — sinon chacune travaille sur une base différente.

Repartir de zéro : `rm astronautes.db && alembic upgrade head && python peupler.py`.
Les tests, eux, créent une base temporaire : `pytest` ne touche jamais
`astronautes.db`.
