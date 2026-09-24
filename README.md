# Annuaire des astronautes — Session 19 : configuration et secrets

API REST sur une base SQLite, avec authentification JWT, rôles, migrations
Alembic et tests pytest.

> Projet fil rouge de la formation « Flask, puis FastAPI ».
> Un commit par session : `git log --oneline` retrace la progression du code.

## Ce que cette session apporte

- **Une classe de configuration par environnement**, choisie par la variable
  `ENVIRONNEMENT`. Un nom inconnu est refusé au démarrage plutôt que replié en
  silence sur le développement.
- **Un ordre de priorité explicite** entre les trois sources : attribut de
  classe, variable d'environnement, surcharge passée à `creer_app`.
- **`.env.exemple` versionné, `.env` jamais.** Le fichier d'exemple documente
  toutes les variables reconnues ; le vrai contient des secrets et reste sur la
  machine. C'est `.env.exemple` qui dit à un nouvel arrivant ce qu'il doit
  renseigner.
- **`annuaire/contraintes.py`** : les longueurs et bornes partagées par
  `schemas.py` et `modeles.py`, pour que la validation et le schéma de base ne
  puissent plus diverger.
- **Les routes de débogage n'existent que si `DEBUG` est actif.** `/plante`
  offrirait sinon à n'importe qui le moyen de provoquer une 500 à volonté.
- **`.env` n'est pas lu en production.** Quand `ENVIRONNEMENT=production` est
  exporté, `charger_dotenv()` n'appelle pas `load_dotenv()` : les variables
  viennent de l'environnement réel, pas d'un fichier oublié sur la machine.
  La commande `flask` lisant `.env` d'elle-même, on exporte aussi
  `FLASK_SKIP_DOTENV=1`.
- **`DEPLOIEMENT.md`** : variables requises, génération de la clé, ordre des
  opérations (migrations, admin, démarrage) et liste de vérification avant une
  mise en production.

## Lancer

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.exemple .env               # puis renseigner CLE_SECRETE_JWT et l'URL
```

`load_dotenv()` lit `.env` au moment de créer l'application. À défaut, les mêmes
variables peuvent être exportées à la main :

```bash
export CLE_SECRETE_JWT=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
export URL_BASE_DE_DONNEES=sqlite:///astronautes.db
export FLASK_APP="annuaire:creer_app"       # évite de répéter --app à chaque commande
export ENVIRONNEMENT=developpement          # ou test, ou production
```

Puis, dans les deux cas :

```bash
alembic upgrade head                        # créer / migrer la base
flask peupler                               # 3 missions, 5 astronautes
flask run --debug                           # http://127.0.0.1:5000
pytest -q                                   # 105 tests
```

## Organisation des fichiers

```
annuaire/              le paquet applicatif
├── __init__.py        creer_app() : la fabrique d'application
├── config.py          une classe par environnement, choisie par ENVIRONNEMENT
├── contraintes.py     longueurs et bornes partagées par schemas.py et modeles.py
├── journal.py         journal JSON, niveau par environnement, id de requête
├── bdd.py             moteur SQLAlchemy et session liée à la requête
├── modeles.py         Mission, Astronaute, Utilisateur
├── schemas.py         validation des corps de requête (Pydantic)
├── donnees/           accès à la base, un module par agrégat, sans Flask
├── erreurs.py         les exceptions métier
├── gestionnaires.py   exception métier → code HTTP
├── permissions.py     rôles et table des permissions
├── securite.py        hachage, jetons JWT, décorateurs d'accès
├── cli.py             flask promouvoir, flask peupler
└── routes/            un blueprint par ressource (debogage.py seulement si DEBUG)
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

- **Un environnement, une classe.** `ENVIRONNEMENT` (`developpement`, `test`
  ou `production`) choisit la classe de `annuaire/config.py` ; un nom inconnu
  est refusé au démarrage. `creer_app` accepte aussi une classe ou un nom en
  argument, ce dont se servent les tests.
- **Trois sources, un ordre.** Attribut de classe, puis variable
  d'environnement, puis surcharge passée à `creer_app`. `.env.exemple` liste
  toutes les variables reconnues ; `.env` n'est pas versionné.
- **Une seule source pour l'URL de la base.** `annuaire/config.py` la définit
  (variable d'environnement `URL_BASE_DE_DONNEES`) ; `migrations/env.py` la lit
  au même endroit, environnement compris. Application et migrations ne peuvent
  plus travailler sur deux bases différentes.
- **Rien n'est lu à l'import.** La clé JWT, le coût du hachage et l'URL sont
  lus à la création de l'application. `creer_app` refuse de démarrer si
  `CLE_SECRETE_JWT` ou l'URL de base est vide, quel que soit l'environnement.
- **Les routes sont fermées par défaut.** Chaque vue porte soit `@publique`,
  soit un décorateur d'accès (`@authentification_requise`,
  `@permission_requise("creer")`). Le hook `refuser_par_defaut` refuse tout ce
  qui ne porte ni l'un ni l'autre, et `test_toutes_les_vues_sont_declarees`
  échoue si une vue oublie de se déclarer.
- **Les tests ne touchent pas `astronautes.db`.** Chacun reçoit une application
  neuve sur une base SQLite en mémoire (`ConfigTest`), sans `monkeypatch`.
- Repartir de zéro : `rm astronautes.db && alembic upgrade head && flask peupler`.
- Migrations : `alembic current` (état), `alembic history` (liste),
  `alembic downgrade -1` (revenir d'un cran),
  `alembic revision --autogenerate -m "message"` (après modification de
  `annuaire/modeles.py`).
