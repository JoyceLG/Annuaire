"""Accès à la base, un module par agrégat.

Ces fonctions ne connaissent ni Flask ni HTTP : elles reçoivent une session
SQLAlchemy et lèvent les exceptions métier de `annuaire.erreurs`. Le hachage
des mots de passe n'est pas ici mais dans `annuaire.securite` : ce module
persiste une empreinte, il ne la fabrique pas.
"""

from . import astronautes, missions, utilisateurs

__all__ = ["astronautes", "missions", "utilisateurs"]
