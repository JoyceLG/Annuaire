"""Routes pour l'annuaire des astronautes"""

from fastapi import Response, APIRouter

from annuaire.donnees.demonstration import ASTRONAUTES, demande_prochain_id
from annuaire.erreurs import AstronauteIntrouvable
from annuaire.schemas import AstronauteEntree, AstronautePatch, AstronauteSortie, Role

router = APIRouter()


@router.get("/api/astronautes", response_model=list[AstronauteSortie])
def lister_astronautes(role: Role | None = None):

    resultats = list(ASTRONAUTES.values())
    if role:
        resultats = [a for a in resultats if a["role"] == role]
    return resultats


@router.get("/api/astronautes/{id_astronaute}", response_model=AstronauteSortie)
def lire_astronaute(id_astronaute: int):

    astronaute = ASTRONAUTES.get(id_astronaute)
    if astronaute is None:
        raise AstronauteIntrouvable(id_astronaute)
    return astronaute


@router.post("/api/astronautes", response_model=AstronauteSortie, status_code=201)
def creer_astronaute(entree: AstronauteEntree, response: Response):

    prochain_id = demande_prochain_id()

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

    astronaute.update(entree.model_dump(exclude_unset=True))
    return astronaute


@router.delete("/api/astronautes/{id_astronaute}", status_code=204)
def supprimer(id_astronaute: int):
    """Supprime un astronaute de la liste ."""

    astronaute = ASTRONAUTES.get(id_astronaute)
    if astronaute is None:
        raise AstronauteIntrouvable(id_astronaute)

    del ASTRONAUTES[id_astronaute]
