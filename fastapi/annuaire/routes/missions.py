"""Routes pour les missions de l'annuaire"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response

from annuaire.bdd import SessionBdd
from annuaire.contraintes import ANNEE_MINIMALE
from annuaire.dependances import PaginationInjectee, authentification_requise
from annuaire.documentation import (
    REPONSE_400,
    REPONSE_401,
    REPONSE_404_MISSION,
    REPONSE_422,
    REPONSE_422_PAGINATION,
)
from annuaire.donnees import missions as donnees_missions
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
async def lister_missions(
    page: PaginationInjectee,
    bdd: SessionBdd,
    annee: Annotated[
        int | None,
        Query(ge=ANNEE_MINIMALE, description="Filtrer les missions depuis l'année"),
    ] = None,
):
    """Renvoie la liste des missions, éventuellement filtrée par année."""
    # Filtre et pagination sont faits par la base (WHERE, OFFSET, LIMIT),
    # plus en Python sur la liste complète.
    return await donnees_missions.lister(
        bdd, annee=annee, limite=page.limite, decalage=page.decalage
    )


@lecture.get(
    "/{id_mission}",
    response_model=MissionSortie,
    summary="Consulter une mission",
    responses={**REPONSE_404_MISSION},
)
async def lire_mission(bdd: SessionBdd, id_mission: IdMission):
    """Renvoie les informations d'une mission donnée, identifiée par son identifiant."""
    # On retourne l'objet SQLAlchemy : MissionSortie (from_attributes) le
    # convertit, programme calculé compris.
    return await donnees_missions.trouver(bdd, id_mission)


@ecriture.post(
    "",
    response_model=MissionSortie,
    summary="Créer une mission",
    responses={**REPONSE_400, **REPONSE_422},
    status_code=201,
)
async def creer_mission(bdd: SessionBdd, entree: MissionEntree, response: Response):
    """Ajoute une mission et renvoie son en-tête Location."""
    mission = await donnees_missions.creer(bdd, entree.model_dump())
    # Le commit appartient à la route : c'est elle qui décide quand la
    # transaction se termine. L'identifiant existe déjà depuis le flush.
    await bdd.commit()
    response.headers["Location"] = f"/api/missions/{mission.id}"
    return mission


@ecriture.put(
    "/{id_mission}",
    response_model=MissionSortie,
    summary="Remplacer une mission",
    responses={**REPONSE_400, **REPONSE_404_MISSION, **REPONSE_422},
    status_code=200,
)
async def remplacer_mission(bdd: SessionBdd, entree: MissionEntree, id_mission: IdMission):
    """Remplace les informations d'une mission donnée : tous les champs requis."""
    mission = await donnees_missions.trouver(bdd, id_mission)
    donnees_missions.modifier(mission, entree.model_dump())
    await bdd.commit()
    return mission


@ecriture.patch(
    "/{id_mission}",
    response_model=MissionSortie,
    summary="Modifier une mission",
    responses={**REPONSE_400, **REPONSE_404_MISSION, **REPONSE_422},
    status_code=200,
)
async def modifier_mission(bdd: SessionBdd, entree: MissionPatch, id_mission: IdMission):
    """Modifie partiellement les informations d'une mission donnée : au moins un champ requis."""
    mission = await donnees_missions.trouver(bdd, id_mission)
    donnees_missions.modifier(mission, entree.model_dump(exclude_unset=True))
    await bdd.commit()
    return mission


@ecriture.delete(
    "/{id_mission}",
    summary="Supprimer une mission",
    responses={**REPONSE_404_MISSION},
    status_code=204,
)
async def supprimer_mission(bdd: SessionBdd, id_mission: IdMission):
    """Supprime une mission donnée."""
    mission = await donnees_missions.trouver(bdd, id_mission)
    await donnees_missions.supprimer(bdd, mission)
    await bdd.commit()
