"""Modèles de données pour les missions de l'annuaire"""

from typing import Annotated

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StringConstraints,
    computed_field,
    model_validator,
)
from pydantic.json_schema import SkipJsonSchema

from annuaire.contraintes import ANNEE_MINIMALE, LONGUEUR_NOM_MISSION
from annuaire.schemas.commun import nettoyer

Nom = Annotated[
    str,
    BeforeValidator(nettoyer),
    StringConstraints(min_length=1, max_length=LONGUEUR_NOM_MISSION),
]
Annee = Annotated[int, Field(ge=ANNEE_MINIMALE)]

class MissionEntree(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    nom: Nom
    annee: Annee

class MissionPatch(BaseModel):
    # minProperties : voir AstronautePatch.
    model_config = ConfigDict(
        extra="forbid", strict=True, json_schema_extra={"minProperties": 1}
    )
    # Absent, pas null : voir AstronautePatch.
    nom: Nom | SkipJsonSchema[None] = None
    annee: Annee | SkipJsonSchema[None] = None

    @model_validator(mode="after")
    def _au_moins_un_champ_non_null(self):
        # model_fields_set ne contient que les champs présents dans le JSON :
        # c'est lui qui distingue « absent » de « laissé à sa valeur par défaut ».
        if not self.model_fields_set:
            raise ValueError("le corps ne peut pas être vide")
        # Un null enregistré casserait la réponse, MissionSortie exigeant chaque champ.
        if any(getattr(self, champ) is None for champ in self.model_fields_set):
            raise ValueError("un champ envoyé ne peut pas être null")
        return self

class MembreSortie(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nom: str


class MissionSortie(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    annee: int
    equipage: list[MembreSortie]      # traverse la relation

    @computed_field
    @property
    def programme(self) -> str:
        return self.nom.split()[0]