"""Contraintes du domaine : longueurs, bornes et valeurs admises."""

from typing import Literal

# Longueurs de champs.
LONGUEUR_NOM = 100
LONGUEUR_NATIONALITE = 50

# Rôles d'un astronaute.
RoleAstronaute = Literal["commandant", "pilote", "specialiste"]
