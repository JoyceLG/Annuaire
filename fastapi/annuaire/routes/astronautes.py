"""Routes pour l'annuaire des astronautes"""

from typing import Annotated

from fastapi import APIRouter, Path, Query, Response

from annuaire.contraintes import (
    LIMITE_FILTRE_MAX,
    LIMITE_FILTRE_MIN,
    RoleAstronaute,
    verifier_qualification,
)
from annuaire.documentation import (
    REPONSE_400,
    REPONSE_404_ASTRONAUTE,
    REPONSE_422,
    REPONSE_422_AVEC_COHERENCE,
)
from annuaire.donnees.demonstration import ASTRONAUTES, demande_prochain_id_astronaute
from annuaire.erreurs import AstronauteIntrouvable
from annuaire.schemas.astronautes import (
    AstronauteEntree,
    AstronautePatch,
    AstronauteSortie,
)

router = APIRouter(tags=["Astronautes"], prefix="/api/astronautes")

IdAstronaute = Annotated[int, Path(ge=1, description="Identifiant de l'astronaute")]


@router.get(
    "",
    response_model=list[AstronauteSortie],
    summary="Lister les astronautes",
)
def lister_astronautes(
    role: Annotated[
        RoleAstronaute | None, Query(description="Filtrer par rôle")
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
    """Renvoie la liste des astronautes, éventuellement filtrée par rôle."""

    resultats = list(ASTRONAUTES.values())
    if role:
        resultats = [a for a in resultats if a["role"] == role]
    return resultats[:limite]


@router.get(
    "/{id_astronaute}",
    response_model=AstronauteSortie,
    summary="Consulter un astronaute",
    responses={**REPONSE_404_ASTRONAUTE},
)
def lire_astronaute(id_astronaute: IdAstronaute):
    """Renvoie les informations d'un astronaute donné, identifié par son identifiant.

    Les initiales sont calculées par le serveur à partir du nom.
    """

    astronaute = ASTRONAUTES.get(id_astronaute)
    if astronaute is None:
        raise AstronauteIntrouvable(id_astronaute)
    return astronaute


@router.post("",
    response_model=AstronauteSortie,
    summary="Créer un astronaute",
    responses={**REPONSE_400, **REPONSE_422},
    status_code=201)
def creer_astronaute(entree: AstronauteEntree, response: Response):
    """Ajoute un astronaute et renvoie son en-tête Location."""

    prochain_id = demande_prochain_id_astronaute()

    astronaute = {"id": prochain_id, **entree.model_dump()}
    ASTRONAUTES[prochain_id] = astronaute
    response.headers["Location"] = f"/api/astronautes/{prochain_id}"

    return astronaute


@router.put("/{id_astronaute}",
    response_model=AstronauteSortie,
    summary="Remplacer un astronaute",
    responses={**REPONSE_400, **REPONSE_404_ASTRONAUTE, **REPONSE_422},
    status_code=200)
def remplacer_astronaute(entree: AstronauteEntree, id_astronaute: IdAstronaute):
    """Remplace les informations d'un astronaute donné : tous les champs requis."""

    astronaute = ASTRONAUTES.get(id_astronaute)
    if astronaute is None:
        raise AstronauteIntrouvable(id_astronaute)

    astronaute.update(entree.model_dump())
    return astronaute


@router.patch("/{id_astronaute}",
    response_model=AstronauteSortie,
    summary="Modifier un astronaute",
    responses={**REPONSE_400, **REPONSE_404_ASTRONAUTE, **REPONSE_422_AVEC_COHERENCE},
    status_code=200)
def modifier_astronaute(entree: AstronautePatch, id_astronaute: IdAstronaute):
    """Modifie partiellement les informations d'un astronaute donné : au moins un champ requis."""

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


@router.delete("/{id_astronaute}",
    summary="Supprimer un astronaute",
    responses={**REPONSE_404_ASTRONAUTE},
    status_code=204)
def supprimer(id_astronaute: IdAstronaute):
    """Supprime un astronaute donné."""

    astronaute = ASTRONAUTES.get(id_astronaute)
    if astronaute is None:
        raise AstronauteIntrouvable(id_astronaute)

    del ASTRONAUTES[id_astronaute]
