# Annuaire des astronautes — Session 18 : journal applicatif

API REST sur SQLite, avec authentification JWT, rôles, migrations Alembic et
tests pytest. Les logs ne sont plus ceux du serveur de développement.

> Projet fil rouge de la formation « Flask, puis FastAPI ».
> Un commit par session : `git log --oneline` retrace la progression du code.

## Ce que cette session apporte

- **Un journal structuré en JSON** (`annuaire/journal.py`). Un log destiné à
  une machine se cherche et s'agrège ; une phrase libre ne se cherche qu'à
  l'œil, et seulement si on sait déjà quoi chercher.
- **Un identifiant par requête**, posé sur `g` et injecté dans chaque
  enregistrement par `FiltreRequeteId` : c'est ce qui permet de recoller les
  lignes d'une même requête au milieu de celles de tous les autres clients.
- **Le niveau de log dépend de l'environnement** : `DEBUG` en développement,
  `WARNING` en test pour que la sortie de `pytest` reste lisible.
- **Ce qu'on ne journalise jamais** : un mot de passe, un jeton complet, une
  empreinte. Un journal se lit, se copie et s'expédie à un agrégateur — tout ce
  qu'on y écrit est publié.
- Le mode debug **désactivé en production**, et ce que ça change concrètement :
  plus de trace Python dans la réponse, donc plus de chemin de fichiers ni de
  console interactive offerts au premier venu.
- Les séquences ANSI de werkzeug sont nettoyées avant sérialisation, sans quoi
  `json.dumps` les échappe en `\u001b[31m` et rend la ligne illisible.

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
pytest -q                                   # 97 tests
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
├── journal.py         journal JSON, niveau par environnement, id de requête
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
- **Le journal est configuré par la fabrique.** `configurer_journal(app)` est
  appelé dans `creer_app` : une application de test a donc son propre niveau
  de log, sans variable globale à remettre en place après coup.
- **Les tests ne touchent pas `astronautes.db`.** Chacun reçoit une application
  neuve sur une base SQLite en mémoire (`ConfigTest`), sans `monkeypatch`.
- Repartir de zéro : `rm astronautes.db && alembic upgrade head && flask peupler`.
- Migrations : `alembic current` (état), `alembic history` (liste),
  `alembic downgrade -1` (revenir d'un cran),
  `alembic revision --autogenerate -m "message"` (après modification de
  `annuaire/modeles.py`).
