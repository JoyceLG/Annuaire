"""Routes pour l'annuaire des astronautes"""

from typing import Annotated

from fastapi import APIRouter, Path, Query, Response

from annuaire.contraintes import (
    LIMITE_FILTRE_MAX,
    LIMITE_FILTRE_MIN,
    RoleAstronaute,
    verifier_qualification,
)
from annuaire.donnees.demonstration import ASTRONAUTES, demande_prochain_id_astronaute
from annuaire.erreurs import AstronauteIntrouvable
from annuaire.schemas.astronautes import (
    AstronauteEntree,
    AstronautePatch,
    AstronauteSortie,
)

router = APIRouter()


@router.get("/api/astronautes", response_model=list[AstronauteSortie])
def lister_astronautes(
    role: Annotated[RoleAstronaute | None, Query(description="Filtrer par rôle")] = None,
    limite: Annotated[int, Query(ge=LIMITE_FILTRE_MIN, le=LIMITE_FILTRE_MAX, description="Nombre maximum de résultats")] = 20,
):
    resultats = list(ASTRONAUTES.values())
    if role:
        resultats = [a for a in resultats if a["role"] == role]
    return resultats[:limite]

@router.get("/api/astronautes/{id_astronaute}", response_model=AstronauteSortie)
def lire_astronaute(
    id_astronaute: Annotated[
        int, Path(ge=1, description="Identifiant de l'astronaute")
    ],
):

    astronaute = ASTRONAUTES.get(id_astronaute)
    if astronaute is None:
        raise AstronauteIntrouvable(id_astronaute)
    return astronaute


@router.post("/api/astronautes", response_model=AstronauteSortie, status_code=201)
def creer_astronaute(entree: AstronauteEntree, response: Response):

    prochain_id = demande_prochain_id_astronaute()

    astronaute = {"id": prochain_id, **entree.model_dump()}
    ASTRONAUTES[prochain_id] = astronaute
    response.headers["Location"] = f"/api/astronautes/{prochain_id}"

    return astronaute


@router.put(
    "/api/astronautes/{id_astronaute}", response_model=AstronauteSortie, status_code=200
)
def remplacer_astronaute(entree: AstronauteEntree, id_astronaute: int):
    """Remplace les informations d'un astronaute donné : tous les champs requis."""

    astronaute = ASTRONAUTES.get(id_astronaute)
    if astronaute is None:
        raise AstronauteIntrouvable(id_astronaute)

    astronaute.update(entree.model_dump())
    return astronaute


@router.patch(
    "/api/astronautes/{id_astronaute}", response_model=AstronauteSortie, status_code=200
)
def modifier_astronaute(entree: AstronautePatch, id_astronaute: int):
    """Modifie partiellement les informations d'un astronaute donné."""

    astronaute = ASTRONAUTES.get(id_astronaute)
    if astronaute is None:
        raise AstronauteIntrouvable(id_astronaute)

    modifications = entree.model_dump(exclude_unset=True)
    # Le schéma ne voit que le corps envoyé : la cohérence rôle / qualification
    # se vérifie sur l'astronaute tel qu'il serait après modification.
    resultat = {**astronaute, **modifications}
    verifier_qualification(resultat["role"], resultat["qualification"]["type"])
    astronaute.update(modifications)
    return astronaute


@router.delete("/api/astronautes/{id_astronaute}", status_code=204)
def supprimer(id_astronaute: int):
    """Supprime un astronaute de la liste ."""

    astronaute = ASTRONAUTES.get(id_astronaute)
    if astronaute is None:
        raise AstronauteIntrouvable(id_astronaute)

    del ASTRONAUTES[id_astronaute]