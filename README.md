# Annuaire des astronautes — Session 4 : recevoir des données

Le client peut enfin envoyer autre chose qu'une URL. Chaque astronaute devient
un dictionnaire `{nom, role, mission}` plutôt qu'une simple chaîne.

> Projet fil rouge de la formation « Flask, puis FastAPI ».
> Un commit par session : `git log --oneline` retrace la progression du code.

## Ce que cette session apporte

- Les trois endroits où une donnée peut arriver, et ce que chacun sert à dire :
  le **chemin** (quelle ressource), la **query string** (comment la présenter :
  filtre, tri, pagination), le **corps** (le contenu à créer ou modifier).
- `request.args` pour la query string, `request.get_json()` pour le corps.
- La route `/api/echo`, qui renvoie le détail de ce qu'elle a reçu : l'outil de
  diagnostic le plus utile quand on doute de ce qui arrive vraiment.

## Lancer

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install "flask>=3.1"

flask --app app run --debug        # http://127.0.0.1:5000
```

## Essayer

```bash
curl "http://127.0.0.1:5000/api/echo?a=1&b=2"
curl -X POST http://127.0.0.1:5000/api/astronautes \
     -H "Content-Type: application/json" \
     -d '{"nom": "Sally Ride", "role": "specialiste", "mission": "STS-7"}'
curl "http://127.0.0.1:5000/api/astronautes?role=commandant"
```
