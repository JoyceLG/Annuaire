"""Modèles de données pour l'annuaire des astronautes"""

from typing import Annotated, Literal

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

from annuaire.contraintes import (
    LONGUEUR_NATIONALITE,
    LONGUEUR_NOM,
    RoleAstronaute,
    verifier_qualification,
)
from annuaire.schemas.commun import nettoyer


class QualificationPilote(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    type: Literal["pilote"]
    heures_vol: int = Field(ge=0)
    appareil: str


class QualificationScientifique(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    type: Literal["scientifique"]
    discipline: str
    doctorat: bool


class QualificationIngenieur(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    type: Literal["ingenieur"]
    specialite: str
    experience: int = Field(ge=0)


Qualification = Annotated[
    QualificationPilote | QualificationScientifique | QualificationIngenieur,
    Field(discriminator="type", description="Type de qualification de l'astronaute", examples=[
        {"type": "pilote", "heures_vol": 1500, "appareil": "F-16"}
    ]),
]

Nom = Annotated[
    str,
    BeforeValidator(nettoyer),
    StringConstraints(min_length=1, max_length=LONGUEUR_NOM),
    Field(description="Nom complet de l'astronaute", examples=["Sophie Adenot"]),
]

Nationalite = Annotated[
    str,
    BeforeValidator(nettoyer),
    StringConstraints(min_length=1, max_length=LONGUEUR_NATIONALITE),
    Field(description="Nationalité de l'astronaute", examples=["Française"]),
]

Role = Annotated[
    RoleAstronaute,
    Field(description="Rôle de l'astronaute", examples=["commandant", "pilote", "specialiste"])
]


class AstronauteEntree(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    nom: Nom
    role: Role
    nationalite: Nationalite
    qualification: Qualification

    @model_validator(mode="after")
    def _qualification_coherente_avec_role(self):
        # Le discriminateur valide la forme de la qualification, pas son
        # adéquation au rôle : ce croisement de deux champs se fait ici.
        verifier_qualification(self.role, self.qualification.type)
        return self


class AstronautePatch(BaseModel):
    # minProperties publie dans le schéma le refus du corps vide, que le
    # validateur applique : sans lui, `{}` paraît valide à qui lit /docs.
    model_config = ConfigDict(
        extra="forbid", strict=True, json_schema_extra={"minProperties": 1}
    )
    # SkipJsonSchema retire `null` du schéma publié : un champ peut être
    # absent, pas envoyé à null (le validateur ci-dessous le refuse).
    nom: Nom | SkipJsonSchema[None] = None
    role: Role | SkipJsonSchema[None] = None
    nationalite: Nationalite | SkipJsonSchema[None] = None
    qualification: Qualification | SkipJsonSchema[None] = None

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

    @computed_field
    @property
    def initiales(self) -> str:
        return "".join(partie[0].upper() for partie in self.nom.split() if partie)