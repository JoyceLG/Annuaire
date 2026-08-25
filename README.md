# Annuaire des astronautes — Session 1 : qu'est-ce qu'un serveur web

Première application Flask. Une poignée de routes qui renvoient du texte ou du
HTML, et une liste d'astronautes Apollo codée en dur dans le module.

> Projet fil rouge de la formation « Flask, puis FastAPI ».
> Un commit par session : `git log --oneline` retrace la progression du code.

## Ce que cette session apporte

- Le cycle requête / réponse : le navigateur demande une URL, le serveur renvoie
  une chaîne, Flask l'emballe dans une réponse HTTP.
- `@app.route` décortiqué : ce n'est qu'un enregistrement dans une table
  « chemin → fonction », pas de magie.
- Le mode `--debug` : rechargement automatique et trace d'erreur dans le
  navigateur.

## Lancer

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install "flask>=3.1"

flask --app app run --debug        # http://127.0.0.1:5000
```

## Les routes

| Chemin                     | Renvoie                                  |
|----------------------------|------------------------------------------|
| `/`                        | un bonjour                               |
| `/wip`                     | un travail en cours                      |
| `/apropos`                 | un fragment de HTML                      |
| `/date`                    | la date et l'heure du serveur            |
| `/astronautes`             | la liste en `<ul>`                       |
| `/astronautes/<numero>`    | un astronaute par sa position (1 à 5)    |
