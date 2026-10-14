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

from annuaire.contraintes import (
    LONGUEUR_NATIONALITE,
    LONGUEUR_NOM,
    RoleAstronaute,
    verifier_qualification,
)
from annuaire.schemas.commun import nettoyer


class QualificationPilote(BaseModel):
    type: Literal["pilote"]
    heures_vol: int = Field(ge=0)
    appareil: str


class QualificationScientifique(BaseModel):
    type: Literal["scientifique"]
    discipline: str
    doctorat: bool


class QualificationIngenieur(BaseModel):
    type: Literal["ingenieur"]
    specialite: str
    experience: int = Field(ge=0)


Qualification = Annotated[
    QualificationPilote | QualificationScientifique | QualificationIngenieur,
    Field(discriminator="type"),
]
Nom = Annotated[
    str,
    BeforeValidator(nettoyer),
    StringConstraints(min_length=1, max_length=LONGUEUR_NOM),
]
Nationalite = Annotated[
    str,
    BeforeValidator(nettoyer),
    StringConstraints(min_length=1, max_length=LONGUEUR_NATIONALITE),
]
Role = RoleAstronaute


class AstronauteEntree(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    nom: Nom
    role: RoleAstronaute
    nationalite: Nationalite
    qualification: Qualification

    @model_validator(mode="after")
    def _qualification_coherente_avec_role(self):
        # Le discriminateur valide la forme de la qualification, pas son
        # adéquation au rôle : ce croisement de deux champs se fait ici.
        verifier_qualification(self.role, self.qualification.type)
        return self


class AstronautePatch(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    nom: Nom | None = None
    role: Role | None = None
    nationalite: Nationalite | None = None
    qualification: Qualification | None = None

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