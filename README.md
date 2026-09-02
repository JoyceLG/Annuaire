# Annuaire des astronautes — Session 13 : les relations

Les missions deviennent une table à part entière. Un astronaute pointe vers sa
mission par une clé étrangère.

> Projet fil rouge de la formation « Flask, puis FastAPI ».
> Un commit par session : `git log --oneline` retrace la progression du code.

## Ce que cette session apporte

- La relation un-à-plusieurs : `ForeignKey`, `relationship`, `back_populates`.
  La cohérence est garantie par la base, plus par la bonne volonté du code.
- **Le problème N+1.** Lister 50 astronautes et lire `astronaute.mission.nom`
  déclenche 51 requêtes SQL au lieu d'une. `selectinload` charge tout le lot
  d'un coup.
- Un test qui **compte les requêtes SQL** : c'est la seule façon d'empêcher le
  N+1 de revenir sans que personne ne s'en aperçoive. Une régression de
  performance ne fait échouer aucun test fonctionnel.
- La migration en cinq temps sur une table déjà peuplée : créer la table
  cible, la remplir depuis les valeurs existantes, ajouter la colonne de clé
  étrangère, la renseigner, puis seulement la contraindre.

## Lancer

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install "flask>=3.1" "sqlalchemy>=2.0" alembic pytest

alembic upgrade head
python peupler.py                  # 3 missions, 5 astronautes
flask --app app run --debug        # http://127.0.0.1:5000
pytest -q                          # 55 tests
```

## Les routes

| Méthode | Chemin                                | |
|---------|----------------------------------------|---|
| `GET`   | `/api/astronautes`                     | liste, filtrable |
| `GET`   | `/api/astronautes/<id>`                | une fiche |
| `POST`  | `/api/astronautes`                     | création |
| `PUT` / `PATCH` / `DELETE` | `/api/astronautes/<id>` | |
| `GET`   | `/api/missions`                        | liste |
| `GET`   | `/api/missions/<id>`                   | une mission |
| `GET`   | `/api/missions/<id>/astronautes`       | l'équipage |

Repartir de zéro : `rm astronautes.db && alembic upgrade head && python peupler.py`.
