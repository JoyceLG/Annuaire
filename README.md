# Annuaire des astronautes — Session 17 : permissions et failles courantes

API REST sur SQLite, avec authentification JWT, rôles, migrations Alembic et
tests pytest. Le module plat devient un paquet `annuaire/`.

> Projet fil rouge de la formation « Flask, puis FastAPI ».
> Un commit par session : `git log --oneline` retrace la progression du code.

## Ce que cette session apporte

- **RBAC explicite** : `PERMISSIONS: dict[str, set[str]]` dit noir sur blanc ce
  que chaque rôle a le droit de faire, et le décorateur `permission_requise`
  est le seul endroit qui consulte cette table.
- **Fail-closed.** Le hook `refuser_par_defaut` refuse toute vue qui ne s'est
  pas déclarée — oublier un décorateur ferme la route au lieu de l'ouvrir.
  `test_toutes_les_vues_sont_declarees` échoue si une vue oublie de le faire.
- **Élévation horizontale** : un utilisateur légitime qui atteint la ressource
  d'un autre. La possession se vérifie, elle ne se suppose pas.
- **Élévation par le corps de requête** : un champ `role` glissé dans un
  `PATCH` de profil. Aucune route n'expose le rôle ; le premier admin se crée
  en ligne de commande.
- **Autoriser d'abord, charger ensuite, valider seulement après.** Vérifier la
  permission *après* avoir chargé la ressource laisse distinguer un compte
  existant d'un compte absent par le code HTTP (403 contre 404) : c'est une
  fuite d'information.
- Réorganisation en paquet `annuaire/`, avec une **app factory** et des classes
  de configuration : tout paramètre sensible est lu via `current_app.config`
  au moment de l'appel, plus à l'import du module.

## Lancer

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export CLE_SECRETE_JWT=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
export FLASK_APP="annuaire:creer_app"      # évite de répéter --app à chaque commande

alembic upgrade head                        # créer / migrer la base
flask peupler                               # 3 missions, 5 astronautes
flask run --debug                           # http://127.0.0.1:5000
pytest -q                                   # 93 tests
```

## Organisation des fichiers

```
annuaire/              le paquet applicatif
├── __init__.py        creer_app() : la fabrique d'application
├── config.py          Config / ConfigTest : URL de base, clé JWT, coût argon2
├── bdd.py             moteur SQLAlchemy et session liée à la requête
├── modeles.py         Mission, Astronaute, Utilisateur
├── schemas.py         validation des corps de requête (Pydantic)
├── donnees/           accès à la base, un module par agrégat, sans Flask
├── erreurs.py         les exceptions métier
├── gestionnaires.py   exception métier → code HTTP
├── permissions.py     rôles et table des permissions
├── securite.py        hachage, jetons JWT, décorateurs d'accès
├── cli.py             flask promouvoir, flask peupler
└── routes/            un blueprint par ressource
tests/                 conftest.py + un fichier par domaine
migrations/            révisions Alembic
annuaire.http          requêtes prêtes à jouer (extension REST Client)
pytest.ini             met la racine sur sys.path pour que `pytest` trouve `annuaire`
```

## Rôles et permissions

| rôle    | permissions                                          |
|---------|------------------------------------------------------|
| lecteur | lire                                                  |
| editeur | lire, creer, modifier                                 |
| admin   | lire, creer, modifier, supprimer, administrer         |

Toute inscription crée un **lecteur**. Aucune route n'expose le changement de
rôle : le premier admin se crée en ligne de commande.

```bash
flask promouvoir camille@example.com admin
```

## Points de repère

- **Une seule source pour l'URL de la base.** `annuaire/config.py` la définit
  (variable d'environnement `URL_BASE_DONNEES`, `sqlite:///astronautes.db` par
  défaut) ; `migrations/env.py` la lit au même endroit. Application et
  migrations ne peuvent plus travailler sur deux bases différentes.
- **Rien n'est lu à l'import.** La clé JWT, le coût du hachage et l'URL sont
  lus à la création de l'application. `creer_app` refuse de démarrer si
  `CLE_SECRETE_JWT` est vide.
- **Les tests ne touchent pas `astronautes.db`.** Chacun reçoit une application
  neuve sur une base SQLite en mémoire (`ConfigTest`), sans `monkeypatch`.
- Repartir de zéro : `rm astronautes.db && alembic upgrade head && flask peupler`.
- Migrations : `alembic current` (état), `alembic history` (liste),
  `alembic downgrade -1` (revenir d'un cran),
  `alembic revision --autogenerate -m "message"` (après modification de
  `annuaire/modeles.py`).
