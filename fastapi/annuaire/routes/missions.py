"""Routes pour les missions de l'annuaire"""

from typing import Annotated

from fastapi import APIRouter, Path, Query, Response

from annuaire.contraintes import ANNEE_MINIMALE, LIMITE_FILTRE_MAX, LIMITE_FILTRE_MIN
from annuaire.donnees.demonstration import MISSIONS, demande_prochain_id_mission
from annuaire.erreurs import MissionIntrouvable
from annuaire.schemas.missions import MissionEntree, MissionPatch, MissionSortie

router = APIRouter()

@router.get("/api/missions", response_model=list[MissionSortie])
def lister_missions(
    annee: Annotated[int | None, Query(ge=ANNEE_MINIMALE, description="Filtrer les missions depuis l'année")] = None,
    limite: Annotated[int, Query(ge=LIMITE_FILTRE_MIN, le=LIMITE_FILTRE_MAX, description="Nombre maximum de résultats")] = 20,
):

    resultats = list(MISSIONS.values())
    if annee:
        resultats = [m for m in resultats if m["annee"] >= annee]
    return resultats[:limite]


@router.get("/api/missions/{id_mission}", response_model=MissionSortie)
def lire_mission(id_mission: Annotated[
        int, Path(ge=1, description="Identifiant de la mission")
    ],
):
    mission = MISSIONS.get(id_mission)
    if mission is None:
        raise MissionIntrouvable(id_mission)
    return mission


@router.post("/api/missions", response_model=MissionSortie, status_code=201)
def creer_mission(entree: MissionEntree, response: Response):
    """Ajoute une mission et renvoie son en-tête Location."""

    prochain_id = demande_prochain_id_mission()

    mission = {"id": prochain_id, **entree.model_dump()}
    MISSIONS[prochain_id] = mission
    response.headers["Location"] = f"/api/missions/{prochain_id}"

    return mission

@router.put("/api/missions/{id_mission}", response_model=MissionSortie, status_code=200)
def remplacer_mission(entree: MissionEntree, id_mission: int):
    """Remplace les informations d'une mission donnée."""

    mission = MISSIONS.get(id_mission)
    if mission is None:
        raise MissionIntrouvable(id_mission)

    mission.update(entree.model_dump())
    return mission


@router.patch("/api/missions/{id_mission}", response_model=MissionSortie, status_code=200)
def modifier_mission(entree: MissionPatch, id_mission: int):
    """Modifie partiellement les informations d'une mission donnée."""

    mission = MISSIONS.get(id_mission)
    if mission is None:
        raise MissionIntrouvable(id_mission)

    mission.update(entree.model_dump(exclude_unset=True))
    return mission


@router.delete("/api/missions/{id_mission}", status_code=204)
def supprimer_mission(id_mission: int):
    """Supprime une mission donnée."""

    mission = MISSIONS.get(id_mission)
    if mission is None:
        raise MissionIntrouvable(id_mission)

    del MISSIONS[id_mission]