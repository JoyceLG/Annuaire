"""Modèles SQLAlchemy : ce qui est stocké en base.

Ne pas confondre avec `schemas/`, qui décrit le contrat d'API (Pydantic).
Un modèle peut contenir des colonnes internes qu'aucun schéma de sortie
n'expose.

La déclaration est identique en synchrone et en asynchrone : seul l'usage
de la session change. Ce module n'importe rien de FastAPI.
"""

from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from annuaire.contraintes import LONGUEUR_NOM_MISSION


class Base(DeclarativeBase):
    """Classe de base commune à tous les modèles."""


class Mission(Base):
    __tablename__ = "missions"
    # Sans AUTOINCREMENT, SQLite réattribue le plus grand identifiant libéré :
    # supprimer la mission 4 puis en créer une autre redonnerait 4, et un
    # client qui avait mémorisé /api/missions/4 pointerait vers une autre
    # mission. C'est la garantie de la session 6 (un identifiant n'est jamais
    # réutilisé). PostgreSQL n'a pas ce défaut ; l'option n'a d'effet que sur
    # SQLite.
    __table_args__ = {"sqlite_autoincrement": True}

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(LONGUEUR_NOM_MISSION))
    annee: Mapped[int]
