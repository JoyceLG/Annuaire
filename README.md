# Annuaire des astronautes — Session 10 : organiser son code

Le fichier unique de 230 lignes éclate en modules. `app.py` ne fait plus
qu'assembler les morceaux.

> Projet fil rouge de la formation « Flask, puis FastAPI ».
> Un commit par session : `git log --oneline` retrace la progression du code.

## Ce que cette session apporte

- Les **Blueprints** : un groupe de routes déclaré ailleurs, enregistré sur
  l'application avec son préfixe d'URL.
- **Les imports ne vont que dans un sens.** `routes` importe `donnees`, jamais
  l'inverse. Un import circulaire n'est pas un accident, c'est le signe que la
  responsabilité est mal placée.
- **Aucun `import flask` dans les modules métier.** `donnees.py` et
  `validation.py` ignorent qu'il existe un web : ils seraient réutilisables
  depuis un script ou une tâche planifiée.
- Le refactoring a été fait *après* les tests de la session 9, et pas avant :
  le filet existait déjà quand on a tout déplacé.

## Lancer

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install "flask>=3.1" pytest

pytest -q                          # 22 tests
flask --app app run --debug        # http://127.0.0.1:5000
```

## Organisation

```
app.py            assemblage : Flask(), gestionnaires, blueprint
routes.py         le blueprint et ses vues — la seule couche qui parle HTTP
donnees.py        la liste en mémoire et les opérations dessus
validation.py     les règles de validation
erreurs.py        les exceptions métier
gestionnaires.py  exception métier → réponse HTTP
annuaire.http     requêtes prêtes à jouer (extension REST Client de VS Code)
test_app.py       la suite de tests
```
