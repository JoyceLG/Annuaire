"""Routes pour l'annuaire des astronautes"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response

from annuaire.contraintes import RoleAstronaute, verifier_qualification
from annuaire.dependances import (
    DepotAstronautesInjecte,
    PaginationInjectee,
    authentification_requise,
)
from annuaire.documentation import (
    REPONSE_400,
    REPONSE_401,
    REPONSE_404_ASTRONAUTE,
    REPONSE_422,
    REPONSE_422_AVEC_COHERENCE,
    REPONSE_422_PAGINATION,
)
from annuaire.donnees.demonstration import demande_prochain_id_astronaute
from annuaire.erreurs import AstronauteIntrouvable
from annuaire.schemas.astronautes import (
    AstronauteEntree,
    AstronautePatch,
    AstronauteSortie,
)

lecture = APIRouter(tags=["Astronautes"], prefix="/api/astronautes")

ecriture = APIRouter(
    prefix="/api/astronautes",
    tags=["Astronautes"],
    dependencies=[Depends(authentification_requise)],
    responses={**REPONSE_401},
)

IdAstronaute = Annotated[int, Path(ge=1, description="Identifiant de l'astronaute")]


@lecture.get(
    "",
    response_model=list[AstronauteSortie],
    summary="Lister les astronautes",
    responses={**REPONSE_422_PAGINATION},
)
def lister_astronautes(
    page: PaginationInjectee,
    depot_astronautes: DepotAstronautesInjecte,
    role: Annotated[
        RoleAstronaute | None, Query(description="Filtrer par rôle")
    ] = None
):
    """Renvoie la liste des astronautes, éventuellement filtrée par rôle."""

    resultats = list(depot_astronautes.values())
    if role:
        resultats = [a for a in resultats if a["role"] == role]
    return resultats[page.decalage : page.decalage + page.limite]

@lecture.get(
    "/{id_astronaute}",
    response_model=AstronauteSortie,
    summary="Consulter un astronaute",
    responses={**REPONSE_404_ASTRONAUTE},
)
def lire_astronaute(depot_astronautes: DepotAstronautesInjecte, id_astronaute: IdAstronaute):
    """Renvoie les informations d'un astronaute donné, identifié par son identifiant.

    Les initiales sont calculées par le serveur à partir du nom.
    """

    astronaute = depot_astronautes.get(id_astronaute)
    if astronaute is None:
        raise AstronauteIntrouvable(id_astronaute)
    return astronaute


@ecriture.post("",
    response_model=AstronauteSortie,
    summary="Créer un astronaute",
    responses={**REPONSE_400, **REPONSE_422},
    status_code=201)
def creer_astronaute(depot_astronautes: DepotAstronautesInjecte, entree: AstronauteEntree, response: Response):
    """Ajoute un astronaute et renvoie son en-tête Location."""

    prochain_id = demande_prochain_id_astronaute()

    astronaute = {"id": prochain_id, **entree.model_dump()}
    depot_astronautes[prochain_id] = astronaute
    response.headers["Location"] = f"/api/astronautes/{prochain_id}"

    return astronaute


@ecriture.put("/{id_astronaute}",
    response_model=AstronauteSortie,
    summary="Remplacer un astronaute",
    responses={**REPONSE_400, **REPONSE_404_ASTRONAUTE, **REPONSE_422},
    status_code=200)
def remplacer_astronaute(depot_astronautes: DepotAstronautesInjecte, entree: AstronauteEntree, id_astronaute: IdAstronaute):
    """Remplace les informations d'un astronaute donné : tous les champs requis."""

    astronaute = depot_astronautes.get(id_astronaute)
    if astronaute is None:
        raise AstronauteIntrouvable(id_astronaute)

    astronaute.update(entree.model_dump())
    return astronaute


@ecriture.patch("/{id_astronaute}",
    response_model=AstronauteSortie,
    summary="Modifier un astronaute",
    responses={**REPONSE_400, **REPONSE_404_ASTRONAUTE, **REPONSE_422_AVEC_COHERENCE},
    status_code=200)
def modifier_astronaute(depot_astronautes: DepotAstronautesInjecte, entree: AstronautePatch, id_astronaute: IdAstronaute):
    """Modifie partiellement les informations d'un astronaute donné : au moins un champ requis."""

    astronaute = depot_astronautes.get(id_astronaute)
    if astronaute is None:
        raise AstronauteIntrouvable(id_astronaute)

    modifications = entree.model_dump(exclude_unset=True)
    # Le schéma ne voit que le corps envoyé : la cohérence rôle / qualification
    # se vérifie sur l'astronaute tel qu'il serait après modification.
    resultat = {**astronaute, **modifications}
    verifier_qualification(resultat["role"], resultat["qualification"]["type"])
    astronaute.update(modifications)
    return astronaute


@ecriture.delete("/{id_astronaute}",
    summary="Supprimer un astronaute",
    responses={**REPONSE_404_ASTRONAUTE},
    status_code=204)
def supprimer(depot_astronautes: DepotAstronautesInjecte, id_astronaute: IdAstronaute):
    """Supprime un astronaute donné."""

    astronaute = depot_astronautes.get(id_astronaute)
    if astronaute is None:
        raise AstronauteIntrouvable(id_astronaute)

    del depot_astronautes[id_astronaute]
