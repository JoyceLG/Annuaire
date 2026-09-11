# Annuaire des astronautes — Session 15 : comptes et mots de passe

Une table `utilisateurs`, et des mots de passe qui ne sont jamais stockés.

> Projet fil rouge de la formation « Flask, puis FastAPI ».
> Un commit par session : `git log --oneline` retrace la progression du code.

## Ce que cette session apporte

- **Argon2** (`argon2-cffi`) plutôt que SHA-256. Un hachage de mot de passe
  doit être *lent* : SHA-256 est conçu pour être rapide, donc excellent pour
  celui qui teste des milliards de candidats. `essai_hachage.py` mesure l'écart
  au lieu de l'affirmer.
- **Le sel**, inclus dans l'empreinte Argon2 : deux comptes avec le même mot de
  passe n'ont pas la même empreinte, et une table précalculée ne sert à rien.
- **Séparation stricte** : l'email identifie, l'empreinte authentifie. Aucune
  route ne renvoie jamais l'empreinte.
- **Anti-énumération à la connexion** : email inconnu et mot de passe faux
  donnent la même réponse *et* le même temps de réponse. Sans quoi le temps de
  réponse dit à l'attaquant quels comptes existent.
  Attention : comparer à une chaîne factice non hachée ne protège de rien — il
  faut une véritable empreinte factice précalculée. Mesuré ici à un facteur
  ~85 000 d'écart avant correction.

## Lancer

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install "flask>=3.1" "sqlalchemy>=2.0" alembic "pydantic[email]>=2" argon2-cffi pytest

alembic upgrade head
python peupler.py
flask --app app run --debug        # http://127.0.0.1:5000
pytest -q                          # 73 tests

python essai_hachage.py            # la démonstration Argon2 contre SHA-256
```
