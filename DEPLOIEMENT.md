# Déploiement — liste de vérification

À dérouler dans l'ordre, case par case, avant chaque mise en production de
l'annuaire.

---

## 1. Variables d'environnement

La liste complète vit dans `annuaire/config.py` (`VARIABLES_ENVIRONNEMENT`) ;
`.env.exemple` en est le modèle. Une variable absente ou vide garde la valeur
par défaut de la classe de configuration.

En production, **aucun `.env` n'est lu** : les variables sont exportées dans le
shell (§3.3). `annuaire/config.py` n'appelle pas `load_dotenv()` quand
`ENVIRONNEMENT=production` est exporté, et `FLASK_SKIP_DOTENV=1` empêche la
commande `flask` de le faire à sa place.

### Obligatoires

| Variable | Rôle | Valeur en production |
|---|---|---|
| `ENVIRONNEMENT` | Choisit la classe de configuration (`developpement`, `test`, `production`). Un nom inconnu bloque le démarrage. | `production`. **Absente, c'est `developpement`** : `DEBUG` actif et route `/api/plante` exposée, sans aucun message d'erreur. |
| `CLE_SECRETE_JWT` | Signe et vérifie les jetons de connexion. Sans elle, `creer_app` refuse de démarrer. | Générée pour cette machine (§2), jamais celle du poste de développement. |
| `URL_BASE_DE_DONNEES` | Base utilisée par l'application **et** par Alembic (`migrations/env.py` lit la même config). Sans elle, `creer_app` refuse de démarrer. | Chemin absolu : `sqlite:////chemin/absolu/astronautes.db` (quatre `/`). |
| `FLASK_APP` | Indique à la commande `flask` où trouver l'application (`flask run`, `flask promouvoir`). | `annuaire:creer_app` |
| `FLASK_SKIP_DOTENV` | Empêche la commande `flask` de lire `.env` d'elle-même, avant même que l'application ne soit créée. Sans elle, `flask run` et `flask promouvoir` complètent en silence l'environnement avec un `.env` oublié. | `1` |

### Facultatives, à décider consciemment

| Variable | Défaut en production | Rôle / quand la changer |
|---|---|---|
| `DUREE_JETON_MINUTES` | `30` | Durée de validité d'un jeton. Plus court = moins de risque si un jeton fuit. |
| `ALGORITHME_JWT` | `HS256` | Ne pas toucher sans raison. |
| `FAIRE_CONFIANCE_PROXY` | `false` | Lire l'IP client dans `X-Forwarded-For`. `true` **uniquement** derrière un reverse proxy qui réécrit cet en-tête, sinon n'importe qui choisit l'IP inscrite au journal. |
| `ARGON2_TEMPS` | `3` | Coût du hachage des mots de passe (itérations). |
| `ARGON2_MEMOIRE` | `65536` (Kio, soit 64 Mio) | Mémoire consommée par chaque hachage en cours. |
| `ARGON2_PARALLELISME` | `4` | Fils utilisés par un hachage. |
| `NIVEAU_LOG` | `WARNING` | `INFO` pour voir connexions et refus d'accès. |
| `NIVEAU_LOG_WERKZEUG` | `WARNING` | Une ligne par requête HTTP dès `INFO`. |
| `FORMAT_LOG` | `json` | `json` pour un collecteur, `texte` pour lire à l'œil. |
| `FICHIER_LOG` | vide (sortie standard) | Chemin d'un fichier tournant (5 Mio, 3 archives). Le dossier doit exister et être accessible en écriture. |
| `ECHO_SQL` | `false` | Journalise chaque requête SQL. Jamais en production. |
| `POOL_TAILLE`, `POOL_DEBORDEMENT`, `POOL_RECYCLAGE_SECONDES`, `POOL_TIMEOUT_SECONDES` | `5`, `10`, `1800`, `30` | Pool de connexions. Ignorés par SQLite : les laisser vides. |

---

## 2. Générer la clé secrète

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

32 octets aléatoires (43 caractères), suffisant pour HS256.

- Une clé **par environnement** : développement et production n'en partagent
  jamais.
- La coller dans le fichier d'environnement de production (§3.3), hors du
  dépôt.
- Changer la clé **déconnecte tout le monde** : tous les jetons en circulation
  deviennent invalides. C'est aussi la procédure à suivre si elle a fuité.

---

## 3. Ordre des opérations

### 3.1 Avant de partir du poste

```bash
pytest -q                                # tout doit passer
git status                               # rien de non commité
git ls-files | grep -E '\.env$|\.db$'    # doit ne rien afficher
```

### 3.2 Installer

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3.3 Poser l'environnement

Les variables de production vivent dans un fichier **hors du dossier du
projet**, lisible par le seul compte qui lance l'application, et sont exportées
dans le shell. Aucun `.env` dans le dossier du projet.

```bash
ls .env                                   # doit répondre : aucun fichier
install -m 600 /dev/null ~/annuaire-production.env
# y écrire ENVIRONNEMENT=production, FLASK_SKIP_DOTENV=1, FLASK_APP,
# CLE_SECRETE_JWT, URL_BASE_DE_DONNEES (modèle : .env.exemple)

set -a; source ~/annuaire-production.env; set +a   # à refaire dans chaque shell
```

`ENVIRONNEMENT=production` doit être **exporté** : écrit seulement dans un
`.env`, il ne désactiverait pas la lecture de ce même `.env`.

Vérifier que la configuration se charge et que c'est bien la bonne :

```bash
python -c "
from annuaire import creer_app
app = creer_app()
print('DEBUG   :', app.config['DEBUG'])
print('TESTING :', app.config['TESTING'])
print('base    :', app.config['URL_BASE'])
print('routes  :', sorted({r.rule for r in app.url_map.iter_rules()}))
"
```

Attendu : `DEBUG False`, `TESTING False`, la bonne base, pas de `/api/plante`
dans les routes.

### 3.4 Migrer la base

```bash
cp astronautes.db astronautes.db.$(date +%F)   # sauvegarde, si la base existe déjà
alembic current                                # d'où on part
alembic upgrade head
alembic current                                # doit afficher (head)
```

- `migrations/env.py` lit `ENVIRONNEMENT` et `URL_BASE_DE_DONNEES` : lancer
  Alembic **dans le même environnement** que l'application, sinon on migre une
  autre base.
- **Pas de `flask peupler`** : c'est le jeu de démonstration Apollo.

### 3.5 Démarrer

```bash
flask run          # jamais --debug : il réactive la console de débogage Werkzeug
```

`ConfigProduction.valider` refuse `DEBUG` dans la configuration, mais
`--debug` agit après la création de l'application et passe donc sous ce
contrôle.

### 3.6 Créer l'admin

Aucune route ne crée d'admin : on s'inscrit comme tout le monde, puis on se
promeut en ligne de commande, sur la machine.

```bash
curl -s -X POST http://127.0.0.1:5000/api/inscription \
     -H "Content-Type: application/json" \
     -d '{"email": "admin@exemple.fr", "mot_de_passe": "<mot de passe fort>"}'

flask promouvoir admin@exemple.fr admin
```

`flask promouvoir` écrit directement en base : pas besoin de redémarrer, le
rôle est relu à chaque requête. La commande doit tourner avec la même
`URL_BASE_DE_DONNEES` que l'application.

### 3.7 Vérifier en vrai

```bash
# 1. Connexion et identité
JETON=$(curl -s -X POST http://127.0.0.1:5000/api/connexion \
        -H "Content-Type: application/json" \
        -d '{"email": "admin@exemple.fr", "mot_de_passe": "<mot de passe>"}' \
        | python -c "import sys, json; print(json.load(sys.stdin)['jeton'])")
curl -s http://127.0.0.1:5000/api/moi -H "Authorization: Bearer $JETON"   # role: admin

# 2. La route de débogage n'existe pas
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:5000/api/plante  # 404 attendu

# 3. Sans jeton, c'est refusé
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:5000/api/moi     # 401 attendu
```

Puis lire le journal : lignes JSON, niveau `WARNING` et plus, aucune trace
d'erreur au démarrage.

---

## 4. Liste de vérification

Adaptée de la liste du §6 au projet annuaire. Cocher chaque ligne ; une ligne
non cochée bloque la mise en production.

### Configuration

- [ ] `ENVIRONNEMENT=production` est posé explicitement (l'absence donne
      `developpement`, silencieusement).
- [ ] Jamais `ENVIRONNEMENT=test` : `ConfigTest` ignore l'environnement, tire
      une clé au hasard et travaille sur une base en mémoire, perdue à l'arrêt.
- [ ] `app.config["DEBUG"]` vaut `False` au démarrage réel (§3.3), et aucun
      `--debug` ni `FLASK_DEBUG=1` dans la commande de lancement.
- [ ] `/api/plante` répond 404.
- [ ] `CLE_SECRETE_JWT` est propre à la production et générée par `secrets`.
- [ ] `URL_BASE_DE_DONNEES` pointe vers la base de production, en chemin absolu.
- [ ] `FAIRE_CONFIANCE_PROXY` vaut `true` seulement si un reverse proxy
      réécrit `X-Forwarded-For`.
- [ ] Les réglages argon2 sont ceux par défaut (ou plus forts), jamais ceux de
      `ConfigTest`.

### Secrets

- [ ] `.env` est dans `.gitignore` et n'apparaît pas dans `git ls-files`.
- [ ] Aucun `.env` dans le dossier du projet sur la machine de production.
- [ ] Le fichier d'environnement de production est hors du projet, en
      `chmod 600`.
- [ ] `FLASK_SKIP_DOTENV=1` est exporté : sans `CLE_SECRETE_JWT` dans
      l'environnement, `flask routes` doit refuser de démarrer.
- [ ] Aucun secret dans `alembic.ini`, le README, `annuaire.http` ou les
      messages de commit.
- [ ] Le journal ne contient ni mot de passe ni jeton complet (seulement les
      8 premiers caractères, `LONGUEUR_JETON_JOURNAL`).

### Base de données

- [ ] Sauvegarde faite avant `alembic upgrade head`.
- [ ] `alembic current` affiche `(head)` après migration.
- [ ] `flask peupler` n'a **pas** été lancé.

### Comptes et accès

- [ ] Un admin existe, créé par `flask promouvoir`, avec un mot de passe fort.
- [ ] `test_toutes_les_vues_sont_declarees` passe : aucune vue ni publique ni
      protégée.
- [ ] Sans jeton, `/api/moi` répond 401.

### Dépendances

- N/A

### Journal et erreurs

- [ ] `FICHIER_LOG` : vide (sortie standard) ou un chemin dont le dossier
      existe et est accessible en écriture.
- [ ] Une erreur 500 renvoie le JSON générique de `gestionnaires.py`, sans
      trace Python.

### Avant de fermer le terminal

- [ ] `pytest -q` vert sur le commit déployé.
- [ ] Les vérifications du §3.7 sont passées.
- [ ] Le commit déployé est noté (`git rev-parse --short HEAD`), pour savoir où
      revenir en cas de problème.
