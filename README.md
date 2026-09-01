# Annuaire des astronautes — Session 8 : gestion centralisée des erreurs

Les vues ne fabriquent plus de réponses d'erreur. Elles lèvent une exception
métier ; un gestionnaire unique la traduit en HTTP.

> Projet fil rouge de la formation « Flask, puis FastAPI ».
> Un commit par session : `git log --oneline` retrace la progression du code.

## Ce que cette session apporte

- Des exceptions qui parlent du **domaine**, pas du web :
  `AstronauteIntrouvable`, `DonneesInvalides`. Le code métier n'a pas à savoir
  qu'un astronaute manquant vaut `404` — c'est une décision de la couche HTTP.
- `@app.errorhandler` pour chaque cas, plus un filet pour `HTTPException`
  (les erreurs levées par Flask lui-même) et un dernier pour `Exception`,
  qui garantit qu'aucune trace Python ne fuit vers le client.
- Un format d'erreur unique pour toute l'API : le client n'a qu'une seule
  structure à savoir lire.
- `lire_corps_json`, qui centralise la lecture du corps et sa validation.

## Lancer

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install "flask>=3.1"

flask --app app run --debug        # http://127.0.0.1:5000
```

## Essayer

```bash
curl -i http://127.0.0.1:5000/api/astronautes/999      # 404, format JSON maison
curl -i http://127.0.0.1:5000/chemin-inconnu           # 404, même format
curl -i -X DELETE http://127.0.0.1:5000/api/astronautes # 405, même format
```
