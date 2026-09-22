"""Routes pour la gestion des astronautes."""

from flask import Blueprint, request, url_for

from .. import schemas
from ..bdd import session_bdd
from ..donnees import astronautes as donnees_astronautes
from ..donnees import missions as donnees_missions
from ..securite import permission_requise
from .commun import lire_corps, publique

bp = Blueprint("astronautes", __name__, url_prefix="/api")


@bp.get("/plante")
@publique
def plante():
    return 1 / 0

@bp.get("/astronautes/<int(min=1):id_astronaute>")
@publique
def lire(id_astronaute: int):
    return donnees_astronautes.trouver(session_bdd(), id_astronaute).en_dict()


@bp.get("/astronautes")
@publique
def lister():
    astronautes = donnees_astronautes.lister(
        session_bdd(),
        role=request.args.get("role"),
        mission_id=request.args.get("mission_id"),
    )
    return [a.en_dict() for a in astronautes]


@bp.post("/astronautes")
@permission_requise("creer")
def ajouter():
    champs = lire_corps(schemas.AstronauteEntree)

    bdd = session_bdd()
    astronaute = donnees_astronautes.creer(bdd, champs)
    bdd.commit()
    return (
        astronaute.en_dict(),
        201,
        {"Location": url_for("astronautes.lire", id_astronaute=astronaute.id)},
    )


@bp.put("/astronautes/<int(min=1):id_astronaute>")
@permission_requise("modifier")
def remplacer(id_astronaute: int):
    """Remplace les informations d'un astronaute donné : tous les champs requis."""

    champs = lire_corps(schemas.AstronauteEntree)

    bdd = session_bdd()
    astronaute = donnees_astronautes.trouver(bdd, id_astronaute)
    if "mission_id" in champs:
        donnees_missions.trouver(bdd, champs["mission_id"])

    for cle, valeur in champs.items():
        setattr(astronaute, cle, valeur)

    bdd.commit()
    return astronaute.en_dict(), 200


@bp.patch("/astronautes/<int(min=1):id_astronaute>")
@permission_requise("modifier")
def modifier(id_astronaute: int):
    """Modifie partiellement les informations d'un astronaute donné."""

    champs = lire_corps(schemas.AstronautePatch, partiel=True)

    bdd = session_bdd()
    astronaute = donnees_astronautes.trouver(bdd, id_astronaute)
    if "mission_id" in champs:
        donnees_missions.trouver(bdd, champs["mission_id"])

    for cle, valeur in champs.items():
        setattr(astronaute, cle, valeur)

    bdd.commit()
    return astronaute.en_dict(), 200


@bp.delete("/astronautes/<int(min=1):id_astronaute>")
@permission_requise("supprimer")
def supprimer(id_astronaute: int):
    """Supprime un astronaute de la liste (204 sans corps)."""

    bdd = session_bdd()
    astronaute = donnees_astronautes.trouver(bdd, id_astronaute)
    donnees_astronautes.supprimer(bdd, astronaute)
    bdd.commit()
    return "", 204
