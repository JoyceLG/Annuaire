"""Contraintes du domaine : longueurs, bornes et valeurs admises.

Source unique pour les schémas Pydantic (ce que l'API accepte) et les modèles
SQLAlchemy (ce que la base stocke). Les deux doivent s'accorder : une colonne
plus courte que la validation tronquerait silencieusement, l'inverse laisserait
passer des données que la base refuse.
"""

from typing import Literal, get_args

# Longueurs de champs, partagées par `schemas.py` et `modeles.py`.
LONGUEUR_NOM = 100
LONGUEUR_NATIONALITE = 50
LONGUEUR_NOM_MISSION = 50
LONGUEUR_PROGRAMME = 50
LONGUEUR_EMAIL = 255
LONGUEUR_EMPREINTE = 255
LONGUEUR_ROLE_UTILISATEUR = 20

# Bornes métier.
ANNEE_MINIMALE = 1900

# Politique de mot de passe, appliquée à l'inscription.
MOT_DE_PASSE_MIN = 12
MOT_DE_PASSE_MAX = 128

# Rôles d'un astronaute — à ne pas confondre avec `permissions.RoleUtilisateur`,
# qui décrit les droits d'un compte.
RoleAstronaute = Literal["commandant", "pilote", "specialiste"]
ROLES_ASTRONAUTE: tuple[str, ...] = get_args(RoleAstronaute)

# La colonne doit accueillir le plus long des rôles admis, avec de la marge pour
# en ajouter un sans migration.
LONGUEUR_ROLE_ASTRONAUTE = 50
