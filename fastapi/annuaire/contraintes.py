"""Contraintes du domaine : longueurs, bornes et valeurs admises."""

from typing import Literal

from annuaire.erreurs import QualificationIncoherente

# Longueurs de champs.
LONGUEUR_NOM = 100
LONGUEUR_NOM_MISSION = 100
LONGUEUR_NATIONALITE = 50

# Rôles d'un astronaute.
RoleAstronaute = Literal["commandant", "pilote", "specialiste"]

# Types de qualification admis pour chaque rôle.
QUALIFICATIONS_PAR_ROLE: dict[str, frozenset[str]] = {
    "commandant": frozenset({"pilote", "scientifique", "ingenieur"}),
    "pilote": frozenset({"pilote"}),
    "specialiste": frozenset({"scientifique", "ingenieur"}),
}


def verifier_qualification(role: str, type_qualification: str) -> None:
    """Lève QualificationIncoherente si le rôle n'admet pas ce type de qualification."""
    admises = QUALIFICATIONS_PAR_ROLE[role]
    if type_qualification not in admises:
        raise QualificationIncoherente(role, admises)

# Bornes métier.
ANNEE_MINIMALE = 1900
LIMITE_FILTRE_MIN = 1
LIMITE_FILTRE_MAX = 100