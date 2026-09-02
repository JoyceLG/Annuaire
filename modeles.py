# modeles.py
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Classe de base commune à tous les modèles."""


class Astronaute(Base):
    __tablename__ = "astronautes"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(50))
    mission: Mapped[str] = mapped_column(String(50))
    nationalite: Mapped[str] = mapped_column(String(50))
    programme: Mapped[str] = mapped_column(String(50))
    

    def en_dict(self) -> dict:
        return {
            "id": self.id,
            "nom": self.nom,
            "role": self.role,
            "mission": self.mission,
            "nationalite": self.nationalite,
            "programme": self.programme,
        }