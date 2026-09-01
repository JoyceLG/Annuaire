# Annuaire des astronautes — Session 7 : valider ce qui entre

Rien de ce qui vient du client n'est cru sur parole. Une seule fonction,
`valider_astronaute`, tient toutes les règles.

> Projet fil rouge de la formation « Flask, puis FastAPI ».
> Un commit par session : `git log --oneline` retrace la progression du code.

## Ce que cette session apporte

- Les quatre contrôles, dans cet ordre : champ **présent**, champ du bon
  **type**, valeur dans l'ensemble **autorisé** (`ROLES_VALIDES`), et aucun
  champ **inconnu** — refuser l'inattendu plutôt que l'ignorer, sans quoi une
  faute de frappe dans un nom de champ passe inaperçue.
- Le mode partiel, qui permet à `PATCH` de réutiliser exactement la même
  fonction que `POST` et `PUT` sans dupliquer une règle.
- Une erreur de validation renvoie **toutes** les fautes d'un coup, pas
  seulement la première : un aller-retour par erreur, c'est une API pénible.

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
     -d '{"nom": 42, "role": "cuisinier", "couleur": "bleu"}'
# → 400, les trois problèmes signalés ensemble
```
