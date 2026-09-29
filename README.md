# Annuaire des astronautes — Session 21 : serveur de production

API REST sur Postgres ou SQLite, au choix, avec authentification JWT, rôles,
migrations Alembic et tests pytest, dans deux conteneurs Docker. L'API y est
désormais servie par Gunicorn, et non plus par le serveur de développement.

> Projet fil rouge de la formation « Flask, puis FastAPI ».
> Un commit par session : `git log --oneline` retrace la progression du code.

## Ce que cette session apporte

- **Gunicorn remplace `flask run` dans l'image.** Le `CMD` du `Dockerfile`
  lance `gunicorn --config gunicorn.conf.py "annuaire:creer_app()"` : un
  processus maître et plusieurs workers, chacun avec sa propre application,
  son propre moteur et son propre pool de connexions.
- **`gunicorn.conf.py`** : écoute sur `0.0.0.0:5000` dans le conteneur
  (l'exposition reste limitée à `127.0.0.1` par Compose), workers `sync`,
  délai de 30 s avant de tuer un worker bloqué, arrêt en douceur, recyclage
  d'un worker toutes les 1000 requêtes environ, journal d'accès de Gunicorn
  coupé (celui de l'application est plus riche), erreurs sur la sortie
  standard.
- **Un nombre de workers fixé, `GUNICORN_WORKERS=4`**, transmis par
  `docker-compose.yaml`. Le défaut de Gunicorn (`2 × cœurs + 1`) compte les
  cœurs de l'hôte : 33 workers sur 16 cœurs, soit jusqu'à 495 connexions pour
  les 100 qu'accepte Postgres. 4 workers × 15 connexions laissent la marge des
  tests et d'Alembic.
- **Rotation des journaux par Docker** (`x-journal` : 5 fichiers de 10 Mo par
  conteneur, pour `api` et `base`). Sans limite, Docker garde toute la sortie
  jusqu'à remplir le disque ; et un `FICHIER_LOG` tournant n'est pas sûr sous
  Gunicorn, chaque worker faisant tourner le même fichier de son côté.
- **Dépendances épinglées** dans `requirements.txt`, sur les versions
  vérifiées dans l'image : une reconstruction ne change plus de version sans
  qu'on l'ait décidé.
- **`DEPLOIEMENT.md` complété** : dimensionnement des workers (connexions,
  mémoire argon2, délai), même clé JWT dans tous les workers, arrêt en douceur
  (`docker compose stop -t 30`), une section « Surveiller » et la liste de
  vérification mise à jour.
- **`annuaire.http`** : la requête de santé passe en tête du fichier.

## Lancer

### Installer

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.exemple .env
```

Dans `.env`, renseigner au minimum :

```bash
CLE_SECRETE_JWT=...        # python -c "import secrets; print(secrets.token_urlsafe(32))"
FLASK_APP="annuaire:creer_app"
ENVIRONNEMENT=developpement
```

### Choisir la base

Le code ne connaît aucune base : elle est choisie par deux URL seulement, l'une
pour l'application, l'autre pour les tests.

| | Postgres (docker-compose) | SQLite |
|---|---|---|
| Préparer | `docker compose up -d base` (la base `annuaire_tests` est créée automatiquement à la création du volume) | rien |
| `URL_BASE_DE_DONNEES` (l'application) | `postgresql+psycopg://annuaire:<mdp>@127.0.0.1:5432/annuaire` | `sqlite:///astronautes.db` |
| `URL_BASE_TESTS` (les tests) | `postgresql+psycopg://annuaire:<mdp>@127.0.0.1:5432/annuaire_tests` | `sqlite://` (en mémoire, le plus rapide) |

- Pour Postgres, `<mdp>` est la valeur de `MOT_DE_PASSE_BASE`, également dans
  `.env` : c'est le mot de passe que `docker-compose.yaml` donne à la base.
- **Les tests vident toutes les tables.** `URL_BASE_TESTS` doit donc désigner
  une base à part, dont le nom se termine par `_tests` (`annuaire_tests`,
  `annuaire_tests.db`), ou une base SQLite en mémoire. Sinon, pytest refuse de
  démarrer.
- Une variable exportée dans le shell l'emporte sur `.env`. On peut donc
  changer de base le temps d'une commande, sans modifier le fichier :
  `URL_BASE_TESTS=sqlite:// pytest -q`.

### Lancer l'application

```bash
alembic upgrade head                        # créer / migrer la base
flask peupler                               # 3 missions, 5 astronautes
flask run --debug                           # http://127.0.0.1:5000
```

Les mêmes commandes servent pour les deux bases : seule l'URL change.

### Lancer les tests

```bash
pytest -q                                   # 108 tests, sur URL_BASE_TESTS
```

Chaque test recrée ses tables : pas besoin de lancer `alembic` sur la base de
test.

Pour lancer la même suite dans l'image de l'API, sur Postgres : voir
[Docker, cas par cas](#docker-cas-par-cas), « Lancer les tests dans Docker ».

## Docker, cas par cas

Trois services dans `docker-compose.yaml` :

| Service | Rôle | Lancé par |
|---|---|---|
| `base` | Postgres 16, publié sur `127.0.0.1:5432` ; données dans le volume `annuaire_donnees_postgres` | `docker compose up` |
| `api` | l'application, en production, servie par Gunicorn (4 workers), publiée sur `127.0.0.1:5000` | `docker compose up` |
| `tests` | la suite pytest, dans la même image que l'API | `docker compose run --rm tests` seulement (profil `tests`) |

Compose lit `CLE_SECRETE_JWT`, `MOT_DE_PASSE_BASE` et, s'il est renseigné,
`GUNICORN_WORKERS` dans le `.env` du projet.
En production, un fichier à part : voir `DEPLOIEMENT.md` §1.1.

Deux façons de lancer une commande dans un conteneur :
- `docker compose run --rm <service> <commande>` crée un conteneur neuf pour
  cette seule commande, puis le supprime. `api` n'a pas besoin d'être démarré.
- `docker compose exec <service> <commande>` entre dans le conteneur qui tourne
  déjà.

### Développer en local, avec seulement Postgres dans Docker

L'application et pytest tournent depuis `.venv`, la base dans Docker :

```bash
docker compose up -d base                   # puis URL_BASE_DE_DONNEES et URL_BASE_TESTS sur 127.0.0.1:5432
docker compose ps                           # base : « healthy »
```

### Premier lancement complet

```bash
docker compose build                        # images api et tests
docker compose up -d base
docker compose run --rm api alembic upgrade head
docker compose up -d api                    # http://127.0.0.1:5000
docker compose ps                           # api et base : « healthy »
```

### Données de démonstration (développement uniquement)

```bash
docker compose run --rm api flask peupler   # 3 missions, 5 astronautes ; refusé si la base contient déjà des missions
```

### Créer l'admin

On s'inscrit d'abord auprès de l'API, puis on change le rôle. La commande
échoue si l'adresse n'est pas encore inscrite.

```bash
curl -X POST http://127.0.0.1:5000/api/inscription \
     -H "Content-Type: application/json" \
     -d '{"email": "admin@x.fr", "mot_de_passe": "<mot de passe>"}'
docker compose run --rm api flask promouvoir admin@x.fr admin
```

### Lancer les tests dans Docker

Même Python et mêmes dépendances que l'API, sur la base `annuaire_tests` du
service `base`.

```bash
docker compose build tests                  # après toute modification du code
docker compose run --rm tests               # toute la suite
docker compose run --rm tests pytest -q -p no:cacheprovider tests/test_sante.py   # un seul fichier
```

`annuaire_tests` est créée par `docker/initdb/creer_base_tests.sh` à la
création du volume. Sur un volume plus ancien que ce script, la créer une
fois : `docker compose exec base createdb -U annuaire annuaire_tests`.

### Après une modification du code

Sans reconstruction, les conteneurs gardent l'ancien code.

```bash
docker compose build
docker compose run --rm tests               # la suite, dans la nouvelle image
docker compose run --rm api alembic upgrade head   # si une migration a été ajoutée
docker compose up -d api                    # recrée le conteneur avec la nouvelle image
```

### Nouvelle migration

La générer depuis `.venv`, pas dans le conteneur : le fichier doit arriver dans
`migrations/versions/` du dépôt, et le conteneur n'écrit pas sur le poste.

```bash
docker compose up -d base
alembic revision --autogenerate -m "message"     # avec URL_BASE_DE_DONNEES sur 127.0.0.1:5432
docker compose build && docker compose run --rm api alembic upgrade head
```

### Commandes flask et alembic dans le conteneur

```bash
docker compose run --rm api alembic current      # révision appliquée, (head) attendu
docker compose run --rm api alembic history      # liste des révisions
docker compose run --rm api flask routes         # routes enregistrées
```

### Surveiller

```bash
docker compose ps                           # état et santé des services
docker compose logs api                     # démarrage de Gunicorn (texte), puis journal JSON de l'API
docker compose logs -f api                  # le même, en continu (Ctrl+C pour sortir)
docker compose logs api | grep -c "Booting worker"   # 4 au démarrage ; plus, s'il a fallu en remplacer
docker compose logs api | grep "WORKER TIMEOUT"      # workers tués après 30 s sans réponse
curl http://127.0.0.1:5000/api/sante        # 200 si la base répond, 503 sinon
docker compose exec base psql -U annuaire annuaire   # console Postgres (\dt, \q)
```

`api` passe « unhealthy » une trentaine de secondes après une panne de la base,
et redevient « healthy » quand elle revient, sans redémarrage. Docker ne garde
que 5 fichiers de 10 Mo de journal par conteneur : `logs` ne remonte pas
indéfiniment.

### Sauvegarder et restaurer la base

```bash
docker compose exec -T base pg_dump -U annuaire annuaire > sauvegarde-$(date +%F).sql
docker compose exec -T base psql -U annuaire annuaire < sauvegarde-AAAA-MM-JJ.sql   # sur une base vide
```

### Arrêter et redémarrer

| Commande | Effet | Données |
|---|---|---|
| `docker compose stop` | arrête les conteneurs, sans les supprimer (`-t 30` laisse aux requêtes en cours le temps de Gunicorn) | conservées |
| `docker compose start` | relance les conteneurs arrêtés | conservées |
| `docker compose restart api` | redémarre la seule API | conservées |
| `docker compose down` | arrête et **supprime** conteneurs et réseau | **conservées** (volume intact) |
| `docker compose down -v` | idem, **et supprime le volume** | **perdues** : comptes, admin, données, `annuaire_tests` |

Après `stop` ou `down`, `docker compose up -d` repart avec toutes les données.

### Repartir d'une base vide

Irréversible sans sauvegarde : tout le contenu de Postgres est supprimé.

```bash
docker compose down -v
docker compose up -d base                   # nouveau volume ; annuaire_tests recréée automatiquement
docker compose run --rm api alembic upgrade head
docker compose up -d api                    # puis recréer l'admin (ci-dessus)
```

C'est aussi le seul moyen de changer `MOT_DE_PASSE_BASE` : Postgres ne le lit
qu'à la création du volume (détails dans `DEPLOIEMENT.md` §6).

### Libérer de la place

```bash
docker compose down --rmi local             # supprime aussi les images construites (api, tests), pas le volume
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
└── routes/            un blueprint par ressource, plus sante.py (debogage.py seulement si DEBUG)
tests/                 conftest.py + un fichier par domaine
migrations/            révisions Alembic (une migration initiale unique)
Dockerfile             image de l'API, lancée par Gunicorn
gunicorn.conf.py       workers, délais, recyclage et journal de Gunicorn
docker-compose.yaml    services base (Postgres), api, et tests (profil tests) ; rotation des journaux
docker/initdb/         scripts lancés par Postgres à la création du volume (annuaire_tests)
.dockerignore          ce qui n'entre pas dans l'image, dont .env
DEPLOIEMENT.md         mise en production avec Docker, liste de vérification
CLAUDE.md              règles du projet pour Claude Code
.claude/skills/        skill validate-projet-annuaire
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
- **Les tests ne touchent pas la base de l'application.** Chacun reçoit une
  application neuve sur la base de `URL_BASE_TESTS`, aux tables recréées, sans
  `monkeypatch`. Aucune fixture n'ouvre de contexte applicatif : chaque requête
  du test a sa propre session, comme en production.
- **Un worker, une application.** Gunicorn appelle `creer_app()` dans chaque
  worker : tout ce qui est tiré au hasard au démarrage différerait d'un
  worker à l'autre. C'est pourquoi la clé JWT vient toujours de
  l'environnement en production, et pourquoi le pool se dimensionne par
  worker.
- **Les listes sont triées par identifiant** (`order_by`) : sans cela, aucune
  base ne garantit d'ordre.
- Repartir de zéro : `alembic downgrade base && alembic upgrade head && flask peupler`.
- Migrations : `alembic current` (état), `alembic history` (liste),
  `alembic downgrade -1` (revenir d'un cran),
  `alembic revision --autogenerate -m "message"` (après modification de
  `annuaire/modeles.py`).
