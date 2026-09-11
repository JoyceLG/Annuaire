import os
import secrets

os.environ.setdefault("CLE_SECRETE_JWT", secrets.token_urlsafe(32))

import donnees
from argon2 import PasswordHasher

# Paramètres minimaux : uniquement en test, jamais en production
donnees.hacheur = PasswordHasher(time_cost=1, memory_cost=8, parallelism=1)
donnees.EMPREINTE_FACTICE = donnees.hacheur.hash("factice")