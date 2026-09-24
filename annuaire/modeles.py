"""Modèles de données pour l'application."""

from datetime import UTC, datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .contraintes import (
    LONGUEUR_EMAIL,
    LONGUEUR_EMPREINTE,
    LONGUEUR_NATIONALITE,
    LONGUEUR_NOM,
    LONGUEUR_NOM_MISSION,
    LONGUEUR_PROGRAMME,
    LONGUEUR_ROLE_ASTRONAUTE,
    LONGUEUR_ROLE_UTILISATEUR,
)
from .permissions import ROLE_PAR_DEFAUT


class Base(DeclarativeBase):
    """Classe de base commune à tous les modèles."""


class Mission(Base):
    __tablename__ = "missions"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(LONGUEUR_NOM_MISSION), unique=True)
    programme: Mapped[str] = mapped_column(String(LONGUEUR_PROGRAMME))
    annee: Mapped[int]

    astronautes: Mapped[list["Astronaute"]] = relationship(back_populates="mission")

    def en_dict(self) -> dict:
        return {
            "id": self.id,
            "nom": self.nom,
            "programme": self.programme,
            "annee": self.annee,
        }


class Astronaute(Base):
    __tablename__ = "astronautes"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(LONGUEUR_NOM))
    role: Mapped[str] = mapped_column(String(LONGUEUR_ROLE_ASTRONAUTE))
    nationalite: Mapped[str] = mapped_column(String(LONGUEUR_NATIONALITE))

    mission_id: Mapped[int] = mapped_column(ForeignKey("missions.id"))
    mission: Mapped["Mission"] = relationship(back_populates="astronautes")

    def en_dict(self) -> dict:
        return {
            "id": self.id,
            "nom": self.nom,
            "role": self.role,
            "nationalite": self.nationalite,
            "mission_id": self.mission_id,
        }


class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(LONGUEUR_EMAIL), unique=True, index=True)
    empreinte: Mapped[str] = mapped_column(String(LONGUEUR_EMPREINTE))
    cree_le: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    derniere_connexion: Mapped[datetime | None] = mapped_column(default=None)
    role: Mapped[str] = mapped_column(
        String(LONGUEUR_ROLE_UTILISATEUR), default=ROLE_PAR_DEFAUT
    )

    def en_dict(self) -> dict:
        return {"id": self.id, "email": self.email, "derniere_connexion": self.derniere_connexion, "role": self.role}