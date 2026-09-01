# Annuaire des astronautes — Session 9 : tester son API

22 tests pytest sur le client de test Flask. Ils tournent sans lancer de serveur
et sans toucher au réseau.

> Projet fil rouge de la formation « Flask, puis FastAPI ».
> Un commit par session : `git log --oneline` retrace la progression du code.

## Ce que cette session apporte

- Le client de test Flask : il appelle l'application directement en mémoire,
  donc une suite complète tient en une poignée de secondes.
- Les fixtures pytest, pour repartir d'un état propre à chaque test — sans
  quoi les tests se contaminent l'un l'autre selon leur ordre d'exécution.
- **Un test ne vaut que par ce qu'il serait capable de faire rougir.** Un test
  qui passerait aussi avec du code faux ne teste rien : il faut choisir des
  données qui distinguent réellement le bon comportement du mauvais.

## Lancer

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install "flask>=3.1" pytest

pytest -q                          # 22 tests
flask --app app run --debug        # http://127.0.0.1:5000
```

## Fichiers

- `app.py` — l'application complète (données, validation, erreurs, routes)
- `test_app.py` — la suite de tests
