# Annuaire des astronautes — Session 3 : les méthodes HTTP

Une même URL peut répondre différemment selon le verbe employé. La liste
d'astronautes devient modifiable — en mémoire, le temps d'un lancement.

> Projet fil rouge de la formation « Flask, puis FastAPI ».
> Un commit par session : `git log --oneline` retrace la progression du code.

## Ce que cette session apporte

- La sémantique de `GET`, `POST`, `PUT`, `DELETE` : ce que chacun promet à
  celui qui appelle (lire sans effet de bord, créer, remplacer, supprimer).
- `404` contre `405` : chemin inconnu contre chemin connu sollicité avec le
  mauvais verbe.
- `curl` comme outil de test : le navigateur ne sait envoyer que des `GET`, il
  ne suffit plus.
- Les raccourcis `@app.get` / `@app.post` / `@app.put` / `@app.delete`.

## Lancer

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install "flask>=3.1"

flask --app app run --debug        # http://127.0.0.1:5000
```

## Essayer

```bash
curl http://127.0.0.1:5000/api/astronautes
curl -X POST http://127.0.0.1:5000/api/astronautes/Sally%20Ride
curl -X PUT http://127.0.0.1:5000/api/astronautes/1/Buzz%20Aldrin
curl -X DELETE http://127.0.0.1:5000/api/astronautes/1
curl -X DELETE http://127.0.0.1:5000/astronautes      # 405, pas 404
```

Les modifications vivent dans une liste Python : tout repart à zéro au
redémarrage du serveur.
