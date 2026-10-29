"""Modèles SQLAlchemy : ce qui est stocké en base.

Ne pas confondre avec `schemas/`, qui décrit le contrat d'API (Pydantic).
Un modèle peut contenir des colonnes internes qu'aucun schéma de sortie
n'expose.

La déclaration est identique en synchrone et en asynchrone : seul l'usage
de la session change. Ce module n'importe rien de FastAPI.
"""

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from annuaire.contraintes import LONGUEUR_NOM_MISSION


class Base(DeclarativeBase):
    """Classe de base commune à tous les modèles."""


class Mission(Base):
    __tablename__ = "missions"
    __table_args__ = {"sqlite_autoincrement": True}

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(LONGUEUR_NOM_MISSION))
    annee: Mapped[int]

    equipage: Mapped[list["MembreEquipage"]] = relationship(back_populates="mission")


class MembreEquipage(Base):
    __tablename__ = "equipage"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(100))
    mission_id: Mapped[int] = mapped_column(ForeignKey("missions.id"))

    mission: Mapped["Mission"] = relationship(back_populates="equipage")
