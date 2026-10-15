"""Routes pour les missions de l'annuaire"""

from typing import Annotated

from fastapi import APIRouter, Path, Query, Response

from annuaire.contraintes import ANNEE_MINIMALE, LIMITE_FILTRE_MAX, LIMITE_FILTRE_MIN
from annuaire.documentation import REPONSE_400, REPONSE_404_MISSION, REPONSE_422
from annuaire.donnees.demonstration import MISSIONS, demande_prochain_id_mission
from annuaire.erreurs import MissionIntrouvable
from annuaire.schemas.missions import MissionEntree, MissionPatch, MissionSortie

router = APIRouter(tags=["Missions"], prefix="/api/missions")

IdMission = Annotated[int, Path(ge=1, description="Identifiant de la mission")]


@router.get(
    "",
    response_model=list[MissionSortie],
    summary="Lister les missions",
)
def lister_missions(
    annee: Annotated[
        int | None,
        Query(ge=ANNEE_MINIMALE, description="Filtrer les missions depuis l'année"),
    ] = None,
    limite: Annotated[
        int,
        Query(
            ge=LIMITE_FILTRE_MIN,
            le=LIMITE_FILTRE_MAX,
            description="Nombre maximum de résultats",
        ),
    ] = 20,
):
    """Renvoie la liste des missions, éventuellement filtrée par année."""

    resultats = list(MISSIONS.values())
    if annee:
        resultats = [m for m in resultats if m["annee"] >= annee]
    return resultats[:limite]


@router.get(
    "/{id_mission}",
    response_model=MissionSortie,
    summary="Consulter une mission",
    responses={**REPONSE_404_MISSION},
)
def lire_mission(id_mission: IdMission):
    """Renvoie les informations d'une mission donnée, identifiée par son identifiant."""
    mission = MISSIONS.get(id_mission)
    if mission is None:
        raise MissionIntrouvable(id_mission)
    return mission


@router.post(
    "",
    response_model=MissionSortie,
    summary="Créer une mission",
    responses={**REPONSE_400, **REPONSE_422},
    status_code=201,
)
def creer_mission(entree: MissionEntree, response: Response):
    """Ajoute une mission et renvoie son en-tête Location."""

    prochain_id = demande_prochain_id_mission()

    mission = {"id": prochain_id, **entree.model_dump()}
    MISSIONS[prochain_id] = mission
    response.headers["Location"] = f"/api/missions/{prochain_id}"

    return mission


@router.put(
    "/{id_mission}",
    response_model=MissionSortie,
    summary="Remplacer une mission",
    responses={**REPONSE_400, **REPONSE_404_MISSION, **REPONSE_422},
    status_code=200,
)
def remplacer_mission(entree: MissionEntree, id_mission: IdMission):
    """Remplace les informations d'une mission donnée : tous les champs requis."""

    mission = MISSIONS.get(id_mission)
    if mission is None:
        raise MissionIntrouvable(id_mission)

    mission.update(entree.model_dump())
    return mission


@router.patch(
    "/{id_mission}",
    response_model=MissionSortie,
    summary="Modifier une mission",
    responses={**REPONSE_400, **REPONSE_404_MISSION, **REPONSE_422},
    status_code=200,
)
def modifier_mission(entree: MissionPatch, id_mission: IdMission):
    """Modifie partiellement les informations d'une mission donnée : au moins un champ requis."""

    mission = MISSIONS.get(id_mission)
    if mission is None:
        raise MissionIntrouvable(id_mission)

    mission.update(entree.model_dump(exclude_unset=True))
    return mission


@router.delete(
    "/{id_mission}",
    summary="Supprimer une mission",
    responses={**REPONSE_404_MISSION},
    status_code=204,
)
def supprimer_mission(id_mission: IdMission):
    """Supprime une mission donnée."""

    mission = MISSIONS.get(id_mission)
    if mission is None:
        raise MissionIntrouvable(id_mission)

    del MISSIONS[id_mission]
