"""Schémas Pydantic pour la validation des corps de requête."""

from typing import Annotated

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    ValidationError,
)

from .contraintes import (
    ANNEE_MINIMALE,
    LONGUEUR_EMAIL,
    LONGUEUR_NATIONALITE,
    LONGUEUR_NOM,
    MOT_DE_PASSE_MAX,
    MOT_DE_PASSE_MIN,
    RoleAstronaute,
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
    str,
    StringConstraints(min_length=1, max_length=LONGUEUR_NOM),
    AfterValidator(_non_vide),
]
Nationalite = Annotated[
    str,
    StringConstraints(min_length=1, max_length=LONGUEUR_NATIONALITE),
    AfterValidator(_non_vide),
]
Role = RoleAstronaute
MissionId = Annotated[int, Field(gt=0)]
Annee = Annotated[int, Field(gt=ANNEE_MINIMALE)]
Email = Annotated[EmailStr, StringConstraints(max_length=LONGUEUR_EMAIL)]

# À l'inscription : la politique de mot de passe s'applique.
MotDePasseNeuf = Annotated[
    str, StringConstraints(min_length=MOT_DE_PASSE_MIN, max_length=MOT_DE_PASSE_MAX)
]
# À la connexion : seule la borne haute est reprise, pour ne pas hacher un corps
# de requête démesuré. Y remettre `MOT_DE_PASSE_MIN` refuserait les comptes créés
# sous une politique plus ancienne, et révélerait la politique à un attaquant.
MotDePasseExistant = Annotated[
    str, StringConstraints(min_length=1, max_length=MOT_DE_PASSE_MAX)
]


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
    email: Email
    mot_de_passe: MotDePasseNeuf


class UtilisateurPatch(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    email: Email


class ConnexionEntree(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    email: Email
    mot_de_passe: MotDePasseExistant