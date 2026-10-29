"""Routes pour les missions de l'annuaire"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response

from annuaire.contraintes import ANNEE_MINIMALE
from annuaire.dependances import (
    DepotMissionsInjecte,
    PaginationInjectee,
    authentification_requise,
)
from annuaire.documentation import (
    REPONSE_400,
    REPONSE_401,
    REPONSE_404_MISSION,
    REPONSE_422,
    REPONSE_422_PAGINATION,
)
from annuaire.donnees.demonstration import demande_prochain_id_mission
from annuaire.erreurs import MissionIntrouvable
from annuaire.schemas.missions import MissionEntree, MissionPatch, MissionSortie

lecture = APIRouter(tags=["Missions"], prefix="/api/missions")

ecriture = APIRouter(
    prefix="/api/missions",
    tags=["Missions"],
    dependencies=[Depends(authentification_requise)],
    responses={**REPONSE_401},
)

IdMission = Annotated[int, Path(ge=1, description="Identifiant de la mission")]


@lecture.get(
    "",
    response_model=list[MissionSortie],
    summary="Lister les missions",
    responses={**REPONSE_422_PAGINATION},
)
def lister_missions(
    page: PaginationInjectee,
    depot_missions: DepotMissionsInjecte,
    annee: Annotated[
        int | None,
        Query(ge=ANNEE_MINIMALE, description="Filtrer les missions depuis l'année"),
    ] = None
):
    """Renvoie la liste des missions, éventuellement filtrée par année."""

    resultats = list(depot_missions.values())
    if annee:
        resultats = [m for m in resultats if m["annee"] >= annee]
    return resultats[page.decalage : page.decalage + page.limite]


@lecture.get(
    "/{id_mission}",
    response_model=MissionSortie,
    summary="Consulter une mission",
    responses={**REPONSE_404_MISSION},
)
def lire_mission(depot_missions: DepotMissionsInjecte, id_mission: IdMission):
    """Renvoie les informations d'une mission donnée, identifiée par son identifiant."""
    mission = depot_missions.get(id_mission)
    if mission is None:
        raise MissionIntrouvable(id_mission)
    return mission


@ecriture.post(
    "",
    response_model=MissionSortie,
    summary="Créer une mission",
    responses={**REPONSE_400, **REPONSE_422},
    status_code=201,
)
def creer_mission(depot_missions: DepotMissionsInjecte, entree: MissionEntree, response: Response):
    """Ajoute une mission et renvoie son en-tête Location."""

    prochain_id = demande_prochain_id_mission()

    mission = {"id": prochain_id, **entree.model_dump()}
    depot_missions[prochain_id] = mission
    response.headers["Location"] = f"/api/missions/{prochain_id}"

    return mission


@ecriture.put(
    "/{id_mission}",
    response_model=MissionSortie,
    summary="Remplacer une mission",
    responses={**REPONSE_400, **REPONSE_404_MISSION, **REPONSE_422},
    status_code=200,
)
def remplacer_mission(depot_missions: DepotMissionsInjecte, entree: MissionEntree, id_mission: IdMission):
    """Remplace les informations d'une mission donnée : tous les champs requis."""

    mission = depot_missions.get(id_mission)
    if mission is None:
        raise MissionIntrouvable(id_mission)

    mission.update(entree.model_dump())
    return mission


@ecriture.patch(
    "/{id_mission}",
    response_model=MissionSortie,
    summary="Modifier une mission",
    responses={**REPONSE_400, **REPONSE_404_MISSION, **REPONSE_422},
    status_code=200,
)
def modifier_mission(depot_missions: DepotMissionsInjecte, entree: MissionPatch, id_mission: IdMission):
    """Modifie partiellement les informations d'une mission donnée : au moins un champ requis."""

    mission = depot_missions.get(id_mission)
    if mission is None:
        raise MissionIntrouvable(id_mission)

    mission.update(entree.model_dump(exclude_unset=True))
    return mission


@ecriture.delete(
    "/{id_mission}",
    summary="Supprimer une mission",
    responses={**REPONSE_404_MISSION},
    status_code=204,
)
def supprimer_mission(depot_missions: DepotMissionsInjecte, id_mission: IdMission):
    """Supprime une mission donnée."""

    mission = depot_missions.get(id_mission)
    if mission is None:
        raise MissionIntrouvable(id_mission)

    del depot_missions[id_mission]
