# Annuaire des astronautes — Session 6 : les identifiants

Un astronaute n'est plus désigné par sa position dans la liste mais par un `id`
stable, qui ne bouge plus quand un voisin disparaît.

> Projet fil rouge de la formation « Flask, puis FastAPI ».
> Un commit par session : `git log --oneline` retrace la progression du code.

## Ce que cette session apporte

- **Position n'est pas identité.** Avec un numéro de position, supprimer le
  deuxième élément renomme silencieusement tous les suivants : l'URL d'une
  ressource se met à désigner sa voisine. Corrigé par un `id` attribué à la
  création et jamais réutilisé (`prochain_id`).
- La fonction `trouver_astronaute(id)`, seul endroit qui sait comment on
  retrouve un enregistrement.
- `PUT` contre `PATCH` : remplacer tout l'objet, ou ne toucher qu'aux champs
  fournis. Ce qui les sépare vraiment, c'est ce qu'ils font d'un champ
  **absent** — `PUT` le remet à sa valeur par défaut, `PATCH` le laisse tel
  quel.

## Lancer

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install "flask>=3.1"

flask --app app run --debug        # http://127.0.0.1:5000
```

## Essayer

```bash
curl -X DELETE http://127.0.0.1:5000/api/astronautes/2
curl http://127.0.0.1:5000/api/astronautes/3       # toujours Peter Conrad

curl -X PATCH http://127.0.0.1:5000/api/astronautes/3 \
     -H "Content-Type: application/json" -d '{"role": "pilote"}'
```
