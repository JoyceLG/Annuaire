"""Rôles et permissions : la table de référence, et rien d'autre."""

from enum import StrEnum


class RoleUtilisateur(StrEnum):
    LECTEUR = "lecteur"
    EDITEUR = "editeur"
    ADMIN = "admin"


PERMISSIONS: dict[str, set[str]] = {
    RoleUtilisateur.LECTEUR: {"lire"},
    RoleUtilisateur.EDITEUR: {"lire", "creer", "modifier"},
    RoleUtilisateur.ADMIN: {"lire", "creer", "modifier", "supprimer", "administrer"},
}


# Rôle attribué à tout nouvel inscrit : le moins doté. Le promouvoir passe
# obligatoirement par `flask promouvoir`, aucune route ne l'expose.
ROLE_PAR_DEFAUT = RoleUtilisateur.LECTEUR


def a_la_permission(role: str, permission: str) -> bool:
    """Le rôle donné accorde-t-il cette permission ?"""

    return permission in PERMISSIONS.get(role, set())
