---
name: validate-projet-annuaire
description: Valide une session de la formation sur le projet Annuaire — relit le code de la session, lance les tests, fait des retours avant toute correction, met le README à jour, puis crée le commit unique de la session et le fusionne dans main. À utiliser quand l'autrice demande de valider, clôturer, commiter ou fusionner sa session.
---

# Valider une session du projet Annuaire

Dérouler les étapes dans l'ordre. Deux points d'arrêt obligatoires : après la
revue (étape 4) et avant de pousser (étape 8). Tout est rédigé en français.

Rappel des règles du projet : voir `CLAUDE.md`. En particulier, **aucune
référence aux sessions suivantes**, ni dans le code, ni dans la doc, ni dans le
commit.

Commandes Python : `.venv/bin/python`, `.venv/bin/alembic`,
`.venv/bin/ruff`.

## 1. Situer la session

```bash
git status --short
git branch --show-current
git log main --oneline -3
git log main..HEAD --oneline          # commits de la session déjà faits
```

- **Numéro N** : celui de la branche `sessionNN`, sinon le dernier
  `Session N` de `main` + 1.
- **Titre** : celui de la session N dans `../../programme-formation-fastapi-flask-part4.md`
  (à défaut les autres fichiers `programme-*.md`), en minuscules et raccourci
  comme les précédents (`journal applicatif`, `configuration et secrets`).
- Si on est sur `main` avec des modifications, créer la branche
  `git switch -c sessionNN` avant toute chose.
- S'il n'y a rien de nouveau par rapport à `main`, le dire et s'arrêter.

Annoncer en une ligne : « Session N — titre, X fichiers modifiés ».

## 2. Lire tout ce qui a changé

```bash
git diff main --stat
git diff main                          # commits de la branche + copie de travail
git status --short | grep '^??'        # fichiers nouveaux, à lire en entier
```

Lire chaque fichier modifié en entier, pas seulement le diff, quand le
contexte compte (config, sécurité, tests).

## 3. Vérifier

Lancer toutes ces vérifications, puis les rapporter ensemble :

```bash
.venv/bin/python -m pytest -q
```

- **Tests** : tous doivent passer. Noter le nombre de tests (il va dans le README).
- **Tests dans Docker** : `docker compose build tests && docker compose run --rm tests`.
  Même image que l'API, sur Postgres : c'est l'environnement réellement déployé.
- **Prérequis** : `URL_BASE_TESTS` renseignée dans `.env` (base de test
  Postgres démarrée par `docker compose up -d base`, ou `sqlite://`). Sans
  elle, pytest s'arrête avec un message explicatif. Si Postgres est disponible,
  lancer aussi la suite avec `URL_BASE_TESTS=sqlite://` : les deux doivent
  passer, c'est la preuve que le code ne dépend d'aucune base.
- **Migrations** : sur la base de test, jamais sur celle de l'API :
  ```bash
  URL_BASE_TESTS=$(grep '^URL_BASE_TESTS=' .env | cut -d= -f2-)   # vit dans .env, pas dans le shell
  URL_BASE_DE_DONNEES=$URL_BASE_TESTS .venv/bin/alembic upgrade head
  URL_BASE_DE_DONNEES=$URL_BASE_TESTS .venv/bin/alembic check
  URL_BASE_DE_DONNEES=$URL_BASE_TESTS .venv/bin/alembic downgrade base
  ```
  `alembic check` doit répondre « No new upgrade operations detected ». Sinon,
  un modèle a changé sans migration. La descente doit aller jusqu'au bout.
- **SQL écrit à la main** : `grep -rnE "sa\.text\(|import .*\btext\b" annuaire migrations/versions`
  ne doit rien trouver (règle « Indépendance de la base » de `CLAUDE.md`).
- **Ruff**, sur les seuls fichiers Python modifiés, à titre indicatif (le projet
  n'est pas propre au sens de ruff, ne pas signaler l'existant) :
  `.venv/bin/ruff check <fichiers modifiés>`.
- **Les nouveaux tests peuvent-ils échouer ?** Pour chaque test ajouté, repérer
  les `assert` toujours vrais (`... else True`, `hasattr` sur un attribut qui
  n'existe pas, test qui ne fait qu'importer un module). En cas de doute, casser
  temporairement le code testé, relancer le test, vérifier qu'il échoue, puis
  restaurer (sauvegarde dans le scratchpad, jamais `git checkout` sur un
  fichier non commité).
- **Cohérence du projet** (règles de `CLAUDE.md`) :
  - nouvelle variable d'environnement présente dans `VARIABLES_ENVIRONNEMENT`,
    `.env.exemple` et `DEPLOIEMENT.md` ;
  - nouvel import tiers présent dans `requirements.txt` ;
  - toute nouvelle vue porte `@publique` ou un décorateur d'accès ;
  - erreurs levées en exceptions métier, traduites dans `gestionnaires.py` ;
  - rien de lu à l'import ; pas de secret en dur ; `.env` et `*.db` non suivis
    (`git ls-files | grep -E '\.env$|\.db$'` ne doit rien afficher) ;
  - identifiants, commentaires et messages en français.
- **Correction et sécurité** : bugs, cas limites, comportement réel différent
  de ce que le code ou la doc annonce. Quand c'est possible, le démontrer par
  une commande plutôt que l'affirmer.
- **Documentation** : `README.md`, `DEPLOIEMENT.md`, `.env.exemple` et
  `annuaire.http` décrivent-ils encore le code ?

## 4. Rendre les retours — point d'arrêt

Présenter à l'autrice, avant de toucher au code :

- le résultat des tests et des migrations ;
- les défauts trouvés, du plus grave au moins grave, chacun avec le fichier et
  la ligne, ce qui ne va pas, la preuve (commande ou raisonnement) et la
  correction proposée ;
- éventuellement, quelques remarques mineures, clairement séparées.

Puis **s'arrêter et attendre sa réponse**. Ne corriger que ce qu'elle
valide. Après correction, relancer l'étape 3 sur ce qui a changé ; pour un
test corrigé, vérifier qu'il échoue bien quand on casse le code.

S'il n'y a aucun défaut, le dire en une phrase et passer à l'étape 5 sans
attendre.

## 5. Mettre à jour le README

Le README décrit l'état du projet à la fin de la session N. Garder la
structure des sessions précédentes (`git show main:README.md`) :

```markdown
# Annuaire des astronautes — Session N : titre

<Deux lignes : ce qu'est l'API, et ce que cette session change.>

> Projet fil rouge de la formation « Flask, puis FastAPI ».
> Un commit par session : `git log --oneline` retrace la progression du code.

## Ce que cette session apporte
<Une puce par nouveauté : **ce qui change**, puis pourquoi.>

## Lancer
<Installation, variables, alembic upgrade head, flask peupler, flask run,
pytest -q avec le nombre de tests à jour.>

## Organisation des fichiers
<Arborescence à jour : nouveaux fichiers ajoutés, fichiers supprimés retirés.>

## Rôles et permissions

## Points de repère
```

- Retirer toute mention « session en cours » ou « branche non fusionnée ».
- Mettre à jour le nombre de tests.
- Les puces de « Ce que cette session apporte » viennent du diff avec `main`,
  pas de la session précédente.

## 6. Le commit unique de la session

Un seul commit par session. Si la branche contient déjà des commits (par
exemple « Session N — … (en cours) »), les fusionner en un seul :

```bash
git reset --soft main
git add -A
git status --short                     # vérifier : ni .env, ni *.db, ni cache
git commit
```

Message, sur le modèle des sessions précédentes :

```
Session N — titre

<Une phrase qui résume ce que la session change.>

- <une ligne par apport, en minuscules, sans point final>
- ...

<ligne d'attribution Co-Authored-By prévue par Claude Code>
```

## 7. Fusionner dans main

```bash
git switch main
git merge --ff-only sessionNN
git log --oneline -3
```

Si l'avance rapide est refusée, `main` a bougé : s'arrêter et le signaler, ne
jamais faire de merge commit ni de rebase de `main`.

## 8. Pousser — point d'arrêt

Demander confirmation avant de publier, puis :

```bash
git push origin main
git push origin --delete sessionNN     # seulement si la branche existe sur GitHub
git branch -D sessionNN
git status -sb                         # doit afficher main...origin/main, sans écart
```

## 9. Bilan

En quelques lignes : le commit (hash et titre), le nombre de tests, ce qui a été
corrigé à la demande de l'autrice, ce qui a été signalé mais laissé tel quel,
et l'état de GitHub (poussé ou non).
