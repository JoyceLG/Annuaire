# Déploiement

Mise en production de l'annuaire avec Docker Compose : un conteneur `base`
(Postgres 16) et un conteneur `api` (l'application), décrits par
`docker-compose.yaml` et `Dockerfile`.

À dérouler dans l'ordre. La liste de vérification (§7) se coche avant de
considérer la mise en production comme terminée.

---

## 1. Variables

Il y a deux familles de variables, à ne pas confondre.

### 1.1 Lues par Docker Compose

`docker compose` remplace les `${…}` de `docker-compose.yaml` par les valeurs
d'un fichier d'environnement. Ces valeurs ne vont pas telles quelles dans les
conteneurs : Compose les recopie aux endroits où `docker-compose.yaml` les cite.

| Variable | Rôle | Utilisée par |
|---|---|---|
| `CLE_SECRETE_JWT` | Signe et vérifie les jetons de connexion. | `api` (variable du même nom) |
| `MOT_DE_PASSE_BASE` | Mot de passe du compte Postgres `annuaire`. | `base` (`POSTGRES_PASSWORD`) et `api` (dans `URL_BASE_DE_DONNEES`) |

**Attention au fichier lu.** Sans option, Compose lit le `.env` du dossier du
projet, celui du **développement**. La production doit avoir son propre
fichier, passé à **chaque** commande `docker compose` (§3.1) :

```bash
export COMPOSE_ENV_FILES=~/annuaire-production.env   # vaut pour tout le shell
# ou, commande par commande : docker compose --env-file ~/annuaire-production.env …
```

Une variable absente n'arrête pas Compose. Il affiche seulement
`The "…" variable is not set. Defaulting to a blank string.` et continue avec
une valeur vide. Ce message ne doit jamais apparaître en production.

### 1.2 Vues par l'application, dans le conteneur `api`

| Variable | Valeur dans le conteneur | Posée par |
|---|---|---|
| `ENVIRONNEMENT` | `production` | `docker-compose.yaml` |
| `CLE_SECRETE_JWT` | celle du fichier de production | `docker-compose.yaml`, depuis §1.1 |
| `URL_BASE_DE_DONNEES` | `postgresql+psycopg://annuaire:<MOT_DE_PASSE_BASE>@base:5432/annuaire` | `docker-compose.yaml`, depuis §1.1 |
| `FLASK_APP` | `annuaire:creer_app` | `Dockerfile` : toute commande `flask` du conteneur (`run`, `promouvoir`) trouve l'application |

- `ENVIRONNEMENT=production` : `DEBUG` coupé, route `/api/plante` absente,
  journal JSON au niveau `WARNING`. Sans cette variable, l'application
  démarrerait **en développement, sans aucun message**.
- `CLE_SECRETE_JWT` ou `URL_BASE_DE_DONNEES` vide : l'application et `alembic`
  refusent de démarrer (`Réglages manquants : …`).
- `.dockerignore` exclut `.env` de l'image : aucun fichier de développement ne
  peut compléter la configuration du conteneur.

### 1.3 Réglages facultatifs

Ils gardent leur valeur par défaut. Pour en changer un, il faut **l'ajouter
sous `environment:` du service `api`** dans `docker-compose.yaml`, sinon il
n'atteint pas le conteneur. La liste complète est dans `annuaire/config.py`
(`VARIABLES_ENVIRONNEMENT`).

| Variable | Défaut en production | Quand la changer |
|---|---|---|
| `DUREE_JETON_MINUTES` | `30` | Plus court = moins de risque si un jeton fuit. |
| `ALGORITHME_JWT` | `HS256` | Ne pas toucher sans raison. |
| `FAIRE_CONFIANCE_PROXY` | `false` | `true` **uniquement** derrière un reverse proxy qui réécrit `X-Forwarded-For`, sinon n'importe qui choisit l'IP inscrite au journal. |
| `ARGON2_TEMPS`, `ARGON2_MEMOIRE`, `ARGON2_PARALLELISME` | `3`, `65536` (64 Mio), `4` | Coût du hachage des mots de passe. Jamais en dessous des défauts. |
| `NIVEAU_LOG` | `WARNING` | `INFO` pour voir connexions et refus d'accès. |
| `NIVEAU_LOG_WERKZEUG` | `WARNING` | Une ligne par requête HTTP dès `INFO`. |
| `FORMAT_LOG` | `json` | `texte` pour lire à l'œil. |
| `FICHIER_LOG` | vide (sortie standard) | Laisser vide : `docker compose logs api` recueille la sortie standard. |
| `ECHO_SQL` | `false` | Jamais en production. |
| `POOL_TAILLE`, `POOL_DEBORDEMENT`, `POOL_RECYCLAGE_SECONDES`, `POOL_TIMEOUT_SECONDES` | `5`, `10`, `1800`, `30` | `POOL_TAILLE + POOL_DEBORDEMENT` doit rester sous le `max_connections` de Postgres (100 par défaut). |

---

## 2. Générer les secrets

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"   # CLE_SECRETE_JWT
python -c "import secrets; print(secrets.token_urlsafe(24))"   # MOT_DE_PASSE_BASE
```

- `token_urlsafe` ne produit que des lettres, des chiffres, `-` et `_`. C'est
  indispensable pour `MOT_DE_PASSE_BASE`, recopié dans une URL : un `@`, un `/`
  ou un `:` la casserait.
- Un jeu de secrets **par environnement** : jamais ceux du développement.
- Changer `CLE_SECRETE_JWT` **déconnecte tout le monde** : tous les jetons en
  circulation deviennent invalides. C'est aussi la procédure si elle a fuité.
- Changer `MOT_DE_PASSE_BASE` après coup ne change **pas** le mot de passe de la
  base : voir §6.

---

## 3. Premier déploiement

### 3.1 Avant de partir du poste

```bash
pytest -q                                  # sur la base de test Postgres
URL_BASE_TESTS=sqlite:// pytest -q         # et sur SQLite : rien ne dépend de la base
docker compose build && docker compose run --rm tests   # et dans l'image qui sera déployée
git status                                 # rien de non commité
git ls-files | grep -E '\.env$|\.db$'      # doit ne rien afficher
```

### 3.2 Le fichier d'environnement de production

Hors du dépôt, lisible par le seul compte qui déploie :

```bash
install -m 600 /dev/null ~/annuaire-production.env
# y écrire, avec les valeurs du §2 :
#   CLE_SECRETE_JWT=...
#   MOT_DE_PASSE_BASE=...
export COMPOSE_ENV_FILES=~/annuaire-production.env
docker compose config --quiet              # aucun avertissement « not set » attendu
```

### 3.3 Construire et démarrer la base

```bash
docker compose build                       # image de l'API, avec le code actuel
docker compose up -d base
docker compose ps                          # base : « healthy »
```

Au **tout premier** démarrage, Postgres crée le volume de données, le compte
`annuaire` avec `MOT_DE_PASSE_BASE` et la base `annuaire`.

### 3.4 Migrer

```bash
docker compose run --rm api alembic upgrade head
docker compose run --rm api alembic current     # doit afficher (head)
```

- `run --rm` lance un conteneur `api` jetable pour une seule commande, avec la
  même configuration que l'API. Il attend que `base` soit prêt.
- **Pas de `flask peupler`** : c'est le jeu de démonstration Apollo.

### 3.5 Démarrer l'API

```bash
docker compose up -d api                   # http://127.0.0.1:5000
docker compose ps                          # api et base : « healthy »
docker compose logs api                    # lignes JSON, aucune erreur au démarrage
```

L'API ne démarre qu'une fois `base` en bonne santé (`depends_on`,
`condition: service_healthy`). Chaque service a son propre test de santé :
`pg_isready` pour `base`, un appel à `/api/sante` pour `api`. Si la base tombe,
`api` passe « unhealthy » en une trentaine de secondes, puis redevient
« healthy » quand la base revient, sans redémarrage.

### 3.6 Créer l'admin

Aucune route ne crée d'admin : on s'inscrit comme tout le monde, puis on se
promeut en ligne de commande. `promouvoir` échoue (`Aucun utilisateur avec
l'adresse …`) si l'inscription n'a pas eu lieu.

```bash
curl -s -X POST http://127.0.0.1:5000/api/inscription \
     -H "Content-Type: application/json" \
     -d '{"email": "admin@exemple.fr", "mot_de_passe": "<mot de passe fort>"}'

docker compose run --rm api flask promouvoir admin@exemple.fr admin
```

Pas besoin de redémarrer : le rôle est relu en base à chaque requête.

### 3.7 Vérifier en vrai

```bash
# 1. Connexion et identité
JETON=$(curl -s -X POST http://127.0.0.1:5000/api/connexion \
        -H "Content-Type: application/json" \
        -d '{"email": "admin@exemple.fr", "mot_de_passe": "<mot de passe>"}' \
        | python -c "import sys, json; print(json.load(sys.stdin)['jeton'])")
curl -s http://127.0.0.1:5000/api/moi -H "Authorization: Bearer $JETON"   # "role": "admin"

# 2. La route de débogage n'existe pas
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:5000/api/plante  # 404 attendu

# 3. Sans jeton, c'est refusé
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:5000/api/moi     # 401 attendu
```

---

## 4. Mettre à jour (nouveau code)

```bash
export COMPOSE_ENV_FILES=~/annuaire-production.env
docker compose exec -T base pg_dump -U annuaire annuaire > sauvegarde-$(date +%F).sql
docker compose build                       # sans rebuild, le conteneur garde l'ancien code
docker compose run --rm tests              # la suite, dans la nouvelle image, avant de migrer
docker compose run --rm api alembic upgrade head
docker compose up -d api                   # recrée le conteneur avec la nouvelle image
```

La base n'est pas touchée par `build` ni par `up` : seules les migrations la
modifient.

Restaurer une sauvegarde, sur une base vide (après `down -v`, §6) :

```bash
docker compose up -d base
docker compose exec -T base psql -U annuaire annuaire < sauvegarde-AAAA-MM-JJ.sql
```

---

## 5. Arrêter et redémarrer

| Commande | Conteneurs | Réseau | Volume de données (`annuaire_donnees_postgres`) |
|---|---|---|---|
| `docker compose stop` | arrêtés, conservés | conservé | conservé |
| `docker compose start` | redémarrés tels quels | — | — |
| `docker compose down` | arrêtés **et supprimés** | supprimé | **conservé** |
| `docker compose down -v` | arrêtés et supprimés | supprimé | **supprimé** |

Après `stop` ou `down`, `docker compose up -d` retrouve toutes les données :
utilisateurs, admin, missions, table `alembic_version`.

---

## 6. `down` ou `down -v`

**`docker compose down`** est l'arrêt normal. Les conteneurs sont supprimés,
mais les données vivent dans le volume nommé `donnees_postgres`, qui survit. Au
prochain `up`, Postgres retrouve la base telle qu'elle était. Il n'y a rien à
refaire.

**`docker compose down -v`** supprime aussi les volumes déclarés dans
`docker-compose.yaml`, donc **toute la base** : comptes, admin, données,
historique des migrations, et la base `annuaire_tests`, qui vit dans le même
volume. C'est irréversible sans sauvegarde (§4).

Au `up` suivant, Postgres repart de zéro, comme au premier déploiement. Il faut
refaire les §3.3 à §3.7 : migrations, puis inscription et promotion de l'admin.
`annuaire_tests` est recréée automatiquement : `docker/initdb/creer_base_tests.sh`
s'exécute à chaque création du volume.

**Quand utiliser `down -v`** : seulement pour repartir d'une base vide
volontairement, ou pour changer `MOT_DE_PASSE_BASE`. Postgres n'applique
`POSTGRES_PASSWORD` qu'à la création du volume. Si on change la variable sur un
volume existant, la base garde l'ancien mot de passe, et l'API échoue avec
`password authentication failed`. Pour changer le mot de passe sans tout
perdre : sauvegarde, `down -v`, nouveau mot de passe, `up -d base`,
restauration (§4).

Avant tout `down -v`, vérifier ce qui sera supprimé :

```bash
docker volume ls | grep annuaire
```

---

## 7. Liste de vérification

Cocher chaque ligne ; une ligne non cochée bloque la mise en production.

### Configuration

- [ ] `COMPOSE_ENV_FILES` (ou `--env-file`) pointe sur le fichier de
      production pour **toutes** les commandes `docker compose`.
- [ ] `docker compose config --quiet` n'affiche aucun avertissement
      « variable is not set ».
- [ ] `ENVIRONNEMENT: production` est bien dans `docker-compose.yaml` pour
      `api` ; jamais `test` (clé tirée au hasard, pas de base : refus de
      démarrer).
- [ ] Aucun `--debug` ni `FLASK_DEBUG=1` dans le `CMD` du `Dockerfile` ni dans
      `docker-compose.yaml`.
- [ ] `/api/plante` répond 404.
- [ ] `FAIRE_CONFIANCE_PROXY` vaut `true` seulement si un reverse proxy
      réécrit `X-Forwarded-For`.

### Secrets

- [ ] `CLE_SECRETE_JWT` et `MOT_DE_PASSE_BASE` sont propres à la production et
      générés par `secrets.token_urlsafe`.
- [ ] Le fichier d'environnement de production est hors du dépôt, en `chmod 600`.
- [ ] `.env` est dans `.gitignore` et `.dockerignore`, et n'apparaît pas dans
      `git ls-files`.
- [ ] Aucun secret dans `docker-compose.yaml`, `alembic.ini`, le README,
      `annuaire.http` ou les messages de commit.
- [ ] Le journal ne contient ni mot de passe ni jeton complet (seulement les
      8 premiers caractères, `LONGUEUR_JETON_JOURNAL`).

### Réseau

- [ ] Postgres n'est publié que sur `127.0.0.1:5432`, jamais sur toutes les
      interfaces.
- [ ] L'API n'est publiée que sur `127.0.0.1:5000`. L'ouvrir à un autre poste
      est un choix explicite : remplacer `127.0.0.1` par l'adresse de
      l'interface voulue, jamais un `5000:5000` nu (toutes les interfaces).

### Base de données

- [ ] Sauvegarde (`pg_dump`) faite avant toute migration sur une base existante.
- [ ] `alembic current` affiche `(head)` après migration.
- [ ] `flask peupler` n'a **pas** été lancé.
- [ ] Aucun `down -v` sans sauvegarde récente.

### Comptes et accès

- [ ] Un admin existe, créé par `flask promouvoir`, avec un mot de passe fort.
- [ ] Sans jeton, `/api/moi` répond 401.

### Avant de fermer le terminal

- [ ] `pytest -q` vert sur le commit déployé, sur Postgres et sur SQLite, et
      `docker compose run --rm tests` vert dans l'image déployée.
- [ ] Les vérifications du §3.7 sont passées.
- [ ] `docker compose logs api` ne montre aucune erreur.
- [ ] Le commit déployé est noté (`git rev-parse --short HEAD`), pour savoir où
      revenir en cas de problème.

---

## Annexe : sans Docker

Si l'API tourne directement sur la machine (`.venv`), les mêmes variables sont
**exportées dans le shell** depuis un fichier hors du dépôt, et il ne faut aucun
`.env` dans le dossier du projet :

```bash
set -a; source ~/annuaire-production.env; set +a
# ce fichier contient alors aussi : ENVIRONNEMENT=production, FLASK_APP=annuaire:creer_app,
# FLASK_SKIP_DOTENV=1, URL_BASE_DE_DONNEES=postgresql+psycopg://…
```

- `ENVIRONNEMENT=production` doit être **exporté** : `annuaire/config.py` ne lit
  alors pas `.env`.
- `FLASK_SKIP_DOTENV=1` empêche la commande `flask` de lire `.env` d'elle-même,
  avant même que l'application ne soit créée.
- Ensuite, la séquence est la même, sans le préfixe `docker compose run --rm api` :
  `alembic upgrade head`, `flask run` (jamais `--debug`), inscription,
  `flask promouvoir`.
