"""Modèles de données pour l'annuaire des astronautes"""

from pydantic import (
    BaseModel,
    ConfigDict,
    StringConstraints,
    AfterValidator,
    model_validator,
)
from typing import Annotated

from annuaire.contraintes import LONGUEUR_NATIONALITE
from annuaire.contraintes import RoleAstronaute, LONGUEUR_NOM


def _non_vide(valeur: str) -> str:
    nettoye = valeur.strip()
    if not nettoye:
        raise ValueError("ne doit pas être vide")
    return nettoye


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


class AstronauteEntree(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    nom: Nom
    role: Role
    nationalite: Nationalite


class AstronautePatch(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    nom: Nom | None = None
    role: Role | None = None
    nationalite: Nationalite | None = None

    @model_validator(mode="after")
    def _au_moins_un_champ_non_null(self):
        # model_fields_set ne contient que les champs présents dans le JSON :
        # c'est lui qui distingue « absent » de « laissé à sa valeur par défaut ».
        if not self.model_fields_set:
            raise ValueError("le corps ne peut pas être vide")
        # Un null enregistré casserait la réponse, AstronauteSortie exigeant chaque champ.
        if any(getattr(self, champ) is None for champ in self.model_fields_set):
            raise ValueError("un champ envoyé ne peut pas être null")
        return self


class AstronauteSortie(BaseModel):
    id: int
    nom: str
    role: RoleAstronaute
    nationalite: str
