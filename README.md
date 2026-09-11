# Annuaire des astronautes — Session 16 : rester connecté

L'API délivre un jeton JWT à la connexion, et les routes protégées le
réclament.

> Projet fil rouge de la formation « Flask, puis FastAPI ».
> Un commit par session : `git log --oneline` retrace la progression du code.

## Ce que cette session apporte

- JWT avec PyJWT : un jeton **signé, pas chiffré**. Son contenu est lisible par
  n'importe qui — on n'y met donc jamais de secret, seulement de quoi identifier
  le porteur (`sub`, `iat`, `exp`).
- `algorithms=[...]` en liste blanche à la vérification, **obligatoire** : sans
  elle, un attaquant choisit l'algorithme à notre place, `none` compris.
- Le décorateur `authentification_requise` : un seul endroit qui sait lire
  l'en-tête `Authorization`, vérifier le jeton et charger l'utilisateur.
- La clé secrète vient de l'environnement, et l'application **refuse de
  démarrer** si elle est absente. Pas de valeur par défaut : une clé de repli
  silencieuse est une porte ouverte qu'on oublie de refermer.
  Un `os.environ.setdefault` dans le code applicatif annulerait ce *fail fast*
  et donnerait une clé différente par worker en production.

## Lancer

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install "flask>=3.1" "sqlalchemy>=2.0" alembic "pydantic[email]>=2" pyjwt argon2-cffi pytest

export CLE_SECRETE_JWT=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

alembic upgrade head
python peupler.py
flask --app app run --debug        # http://127.0.0.1:5000
pytest -q                          # 80 tests
```

`conftest.py` fournit aux tests une clé jetable et des paramètres Argon2
allégés — uniquement en test, jamais en production.

## Essayer

```bash
curl -X POST http://127.0.0.1:5000/api/utilisateurs \
     -H "Content-Type: application/json" \
     -d '{"email": "camille@example.com", "mot_de_passe": "un-mot-de-passe-long"}'

JETON=$(curl -s -X POST http://127.0.0.1:5000/api/connexion \
     -H "Content-Type: application/json" \
     -d '{"email": "camille@example.com", "mot_de_passe": "un-mot-de-passe-long"}' \
     | python -c "import json,sys; print(json.load(sys.stdin)['jeton'])")

curl -H "Authorization: Bearer $JETON" http://127.0.0.1:5000/api/astronautes
```
