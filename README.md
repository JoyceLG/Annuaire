# Annuaire des astronautes — Session 11 : une vraie base de données

Les données ne vivent plus dans une liste Python. SQLAlchemy 2.0 les range dans
un fichier SQLite qui survit au redémarrage.

> Projet fil rouge de la formation « Flask, puis FastAPI ».
> Un commit par session : `git log --oneline` retrace la progression du code.

## Ce que cette session apporte

- Le style déclaratif moderne : `DeclarativeBase`, `Mapped`, `mapped_column`.
- **Engine contre Session.** L'Engine est le pool de connexions, créé une fois
  pour toute la vie du processus ; la Session est l'espace de travail d'une
  requête, créé et refermé à chaque fois. Les confondre, c'est partager un
  cache d'objets entre deux clients.
- `teardown_appcontext` : Flask referme la session à la fin de la requête,
  y compris quand une exception est passée par là.
- **La session est passée en paramètre** aux fonctions de `donnees.py`, jamais
  importée depuis un global : c'est ce qui permettra aux tests de leur donner
  une base jetable.

## Lancer

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install "flask>=3.1" "sqlalchemy>=2.0" pytest

python peupler.py                  # crée les tables et insère 5 astronautes
flask --app app run --debug        # http://127.0.0.1:5000
pytest -q                          # 23 tests
```

Repartir de zéro : `rm astronautes.db && python peupler.py`.

## Organisation

```
app.py            assemblage
bdd.py            l'Engine et la fabrique de sessions
modeles.py        Astronaute, en table
session_web.py    la session liée à la requête Flask
peupler.py        crée les tables et insère les données de départ
routes.py         les vues
donnees.py        les requêtes SQLAlchemy, sans Flask
validation.py / erreurs.py / gestionnaires.py
test_app.py       la suite de tests
```

Le fichier `astronautes.db` n'est pas versionné : il se reconstruit.
