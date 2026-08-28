# Annuaire des astronautes — Session 5 : répondre proprement

L'API ne renvoie plus des phrases mais du JSON, avec le code de statut qui
convient et les en-têtes attendus.

> Projet fil rouge de la formation « Flask, puis FastAPI ».
> Un commit par session : `git log --oneline` retrace la progression du code.

## Ce que cette session apporte

- Retourner un `dict` ou une `list` depuis une vue : Flask 2.2+ les sérialise
  en JSON et pose le `Content-Type` tout seul.
- Le code de statut fait partie de la réponse, au même titre que le corps :
  `200` lire, `201` créer, `204` supprimer sans rien à dire, `400` demande
  malformée, `404` ressource absente.
- L'en-tête `Location` sur un `201` : la réponse indique **où** la ressource
  créée est désormais joignable, construit avec `url_for`.
- Une route `GET /api/astronautes/<numero>` pour lire une ressource seule.

## Lancer

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install "flask>=3.1"

flask --app app run --debug        # http://127.0.0.1:5000
```

## Essayer

```bash
curl -i -X POST http://127.0.0.1:5000/api/astronautes \
     -H "Content-Type: application/json" \
     -d '{"nom": "Sally Ride", "role": "specialiste", "mission": "STS-7"}'
# → 201, en-tête Location

curl -i -X DELETE http://127.0.0.1:5000/api/astronautes/1    # → 204, corps vide
```
