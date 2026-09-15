"""Schémas Pydantic pour la validation des corps de requête."""

from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    ValidationError,
)


def _non_vide(valeur: str) -> str:
    nettoye = valeur.strip()
    if not nettoye:
        raise ValueError("ne doit pas être vide")
    return nettoye


def convertir_erreurs(erreur: ValidationError) -> dict[str, str]:
    details = {}
    for detail in erreur.errors():
        champ = ".".join(str(p) for p in detail["loc"]) or "corps"
        details[champ] = detail["msg"]
    return details



Nom = Annotated[
    str, StringConstraints(min_length=1, max_length=100), AfterValidator(_non_vide)
]
Nationalite = Annotated[
    str, StringConstraints(min_length=1, max_length=50), AfterValidator(_non_vide)
]
Role = Literal["commandant", "pilote", "specialiste"]
MissionId = Annotated[int, Field(gt=0)]
Annee = Annotated[int, Field(gt=1900)]


class AstronauteEntree(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    nom: Nom
    role: Role
    nationalite: Nationalite
    mission_id: MissionId


class AstronautePatch(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    nom: Nom | None = None
    role: Role | None = None
    nationalite: Nationalite | None = None
    mission_id: MissionId | None = None


class MissionEntree(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    nom: Nom
    annee: Annee


class MissionPatch(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    nom: Nom | None = None
    annee: Annee | None = None


class InscriptionEntree(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    email: EmailStr
    mot_de_passe: Annotated[str, StringConstraints(min_length=12, max_length=128)]


class UtilisateurPatch(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    email: EmailStr

class ConnexionEntree(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    email: EmailStr
    mot_de_passe: Annotated[str, StringConstraints(min_length=1, max_length=128)]