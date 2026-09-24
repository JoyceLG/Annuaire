# Annuaire des astronautes

Projet fil rouge d'une formation « Flask, puis FastAPI » : une API REST
d'annuaire (missions, astronautes, utilisateurs) qui grandit d'une session à
l'autre. Le programme des sessions est dans `../../programme-formation-fastapi-flask*.md`.

C'est un projet d'apprentissage : on explique ce qu'on change, on ne
réécrit pas le travail de l'autrice sans le lui avoir montré, et **on ne fait
aucune référence aux sessions suivantes** (ni dans le code, ni dans la doc, ni
dans les commits). Chaque session décrit le projet tel qu'il est, pas tel qu'il
sera.

## Commandes

L'environnement virtuel est dans le projet : `.venv` (non versionné). Pour le
recréer : `python3 -m venv .venv`, puis les deux `pip install` ci-dessous.

```bash
source .venv/bin/activate
pip install -r requirements.txt
pip install ruff                           # outil de relecture, hors requirements

docker compose up -d base                  # Postgres, publié sur 127.0.0.1:5432
                                           # (annuaire_tests créée à la création du volume)

pytest -q                                  # toute la suite, sur URL_BASE_TESTS
docker compose run --rm tests              # la même, dans l'image de l'API
alembic upgrade head                       # créer / migrer la base locale
flask peupler                              # jeu de démonstration Apollo
flask run --debug                          # http://127.0.0.1:5000
flask promouvoir <email> admin             # seul moyen de créer un admin
alembic revision --autogenerate -m "..."   # après modification de modeles.py
```

`.env` (non versionné) fournit `CLE_SECRETE_JWT`, `URL_BASE_DE_DONNEES`,
`FLASK_APP` et `ENVIRONNEMENT` en local, plus `MOT_DE_PASSE_BASE` (Postgres de
docker-compose) et `URL_BASE_TESTS` (base vidée par les tests, nom en
`_tests`) ; `.env.exemple` en est le modèle. Ces deux dernières ne sont pas des
réglages de l'application : elles ne vont ni dans `VARIABLES_ENVIRONNEMENT`
ni dans `DEPLOIEMENT.md`.

## Architecture

- `annuaire/__init__.py` : `creer_app(config, **surcharges)`, la fabrique. Tout
  l'état (moteur, hacheur, clé) vit dans `app.config` / `app.extensions`,
  jamais dans des globales de module.
- `annuaire/config.py` : une classe par environnement (`ConfigDeveloppement`,
  `ConfigTest`, `ConfigProduction`), choisie par `ENVIRONNEMENT`. Priorité :
  attribut de classe < variable d'environnement < surcharge de `creer_app`.
- `routes/` : un blueprint par ressource. Les vues appellent `donnees/`, qui
  ne connaît pas Flask (fonctions prenant une `Session` SQLAlchemy).
- `erreurs.py` + `gestionnaires.py` : une vue lève une exception métier,
  un gestionnaire la traduit en code HTTP et JSON `{"erreur": ...}`.
- `securite.py` / `permissions.py` : argon2, JWT, rôles lecteur / editeur / admin.
- `migrations/` : Alembic ; `migrations/env.py` lit l'URL dans `annuaire.config`.

## Règles du projet

- **Tout est en français** : identifiants, docstrings, commentaires, messages
  d'erreur, messages de commit. Les commentaires expliquent *pourquoi*, pas ce
  que fait la ligne.
- **Routes fermées par défaut** : toute vue porte `@publique`,
  `@authentification_requise` ou `@permission_requise("...")`, sinon
  `refuser_par_defaut` la refuse et `test_toutes_les_vues_sont_declarees` échoue.
- **Rien n'est lu à l'import** : les réglages se lisent dans
  `current_app.config` au moment de l'appel.
- **Nouvelle variable d'environnement** : l'ajouter à la fois dans
  `VARIABLES_ENVIRONNEMENT` (`config.py`), `.env.exemple` et `DEPLOIEMENT.md`.
- **Nouvelle dépendance importée** : l'ajouter à `requirements.txt`.
- **Modèle modifié** : générer la migration Alembic dans la même session.
- **Tests** : `creer_app(ConfigTest, URL_BASE=...)` sur la base de
  `URL_BASE_TESTS` (tables recréées à chaque test), fixtures de
  `tests/conftest.py`, pas de `monkeypatch` des globales de l'application.
  Chaque test est précédé d'un commentaire `# Vérifie que ...` ou d'une ligne
  décrivant le comportement attendu. Un test doit pouvoir échouer : pas
  d'`assert` toujours vrai.

## Indépendance de la base

Le code ne connaît aucune technologie de base : elle vient tout entière de
`URL_BASE_DE_DONNEES`. Changer de base, c'est changer l'URL, ajouter le pilote
à `requirements.txt` et faire passer les tests sur la nouvelle base.

- **Aucun SQL écrit à la main**, ni dans `annuaire/` ni dans les migrations :
  pas de `sa.text(...)`. Une migration de données s'écrit en Python :
  ```python
  astronautes = sa.table("astronautes", sa.column("id"), sa.column("mission"), sa.column("programme"))
  bind = op.get_bind()
  for id_, mission in bind.execute(sa.select(astronautes.c.id, astronautes.c.mission)).all():
      bind.execute(astronautes.update().where(astronautes.c.id == id_)
                   .values(programme=mission.split(" ")[0]))
  ```
- **Types génériques** de SQLAlchemy seulement (`String`, `Integer`,
  `DateTime`…), jamais `JSONB`, `ARRAY` ou autre type propre à une base.
- **`order_by` explicite** dès que l'ordre d'une liste compte : sans lui,
  aucune base ne garantit d'ordre.
- **`annuaire/bdd.py:options_moteur`** est le seul endroit qui connaît les
  différences entre bases (pool, SQLite en mémoire).
- Les tests tournent sur la base réellement utilisée, et doivent aussi passer
  sur `URL_BASE_TESTS=sqlite://` : c'est la preuve que rien ne dépend d'une base.

## Git

- Dépôt : `git@github.com:JoyceLG/Annuaire.git`, branche principale `main`.
- **Un commit par session**, titré `Session N — titre en minuscules`, daté du
  jour où la session est validée. L'historique se lit comme la progression de
  la formation : ne jamais réécrire un commit déjà sur `main`.
- Une session en cours vit sur une branche `sessionNN`, fusionnée dans `main`
  en avance rapide (`--ff-only`) puis supprimée, en local et sur GitHub.
- Le README décrit l'état de la session qui vient d'être commitée (format :
  voir le skill `validate-projet-annuaire`).
- Valider une session : `/validate-projet-annuaire`.
