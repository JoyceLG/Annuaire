# Annuaire des astronautes — Session 2 : routes et paramètres d'URL

Les routes ne sont plus figées : une partie du chemin devient une variable que
Flask convertit avant d'appeler la fonction.

> Projet fil rouge de la formation « Flask, puis FastAPI ».
> Un commit par session : `git log --oneline` retrace la progression du code.

## Ce que cette session apporte

- Les convertisseurs `int`, `float`, `string`, `path`, et leurs options
  (`min=`, `signed=`) : la validation la plus simple est celle que l'URL fait
  elle-même, avant que le code ne s'exécute.
- Le piège du slash final : `/astronautes` et `/astronautes/` ne sont pas la
  même route.
- `url_for` : on construit les liens à partir du **nom de la fonction**, jamais
  en recopiant le chemin à la main — sinon renommer une route casse tous les
  liens en silence.

## Lancer

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install "flask>=3.1"

flask --app app run --debug        # http://127.0.0.1:5000
```

## Les routes ajoutées

| Chemin                                      | Démontre                          |
|---------------------------------------------|-----------------------------------|
| `/accueil-astronautes`                      | `url_for`                         |
| `/astronautes/<numero>/lettre/<position>`   | deux paramètres dans un chemin    |
| `/carre/<int:n>`                            | le convertisseur `int`            |
| `/salut/<nom>`                              | le convertisseur par défaut       |
| `/celsius/<float(signed=True):degres>`      | une option de convertisseur       |
| `/recherche/<path:chemin>`                  | `path`, qui accepte les `/`       |
