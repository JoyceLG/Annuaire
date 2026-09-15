"""Routes pour la gestion des missions."""

from flask import Blueprint, request, url_for

from .. import schemas
from ..bdd import session_bdd
from ..donnees import astronautes as donnees_astronautes
from ..donnees import missions as donnees_missions
from ..erreurs import MissionUtilisee
from ..securite import permission_requise
from .commun import lire_corps, publique

bp = Blueprint("missions", __name__, url_prefix="/api")


@bp.get("/missions/<int(min=1):id_mission>")
@publique
def lire(id_mission: int):
    return donnees_missions.trouver(session_bdd(), id_mission).en_dict()


@bp.get("/missions")
@publique
def lister():
    missions = donnees_missions.lister(
        session_bdd(), programme=request.args.get("programme")
    )
    return [m.en_dict() for m in missions]


@bp.get("/missions/<int(min=1):id_mission>/astronautes")
@publique
def lister_equipage(id_mission: int):
    mission = donnees_missions.trouver(session_bdd(), id_mission)
    return [a.en_dict() for a in mission.astronautes]


@bp.post("/missions")
@permission_requise("creer")
def ajouter():
    """Ajoute une mission et renvoie son en-tête Location."""

    champs = lire_corps(schemas.MissionEntree)

    bdd = session_bdd()
    mission = donnees_missions.creer(bdd, champs)
    bdd.commit()
    return (
        mission.en_dict(),
        201,
        {"Location": url_for("missions.lire", id_mission=mission.id)},
    )


@bp.put("/missions/<int(min=1):id_mission>")
@permission_requise("modifier")
def remplacer(id_mission: int):
    """Remplace les informations d'une mission donnée."""

    champs = lire_corps(schemas.MissionEntree)

    bdd = session_bdd()
    mission = donnees_missions.trouver(bdd, id_mission)
    for cle, valeur in champs.items():
        setattr(mission, cle, valeur)

    bdd.commit()
    return mission.en_dict(), 200


@bp.patch("/missions/<int(min=1):id_mission>")
@permission_requise("modifier")
def modifier(id_mission: int):
    """Modifie partiellement les informations d'une mission donnée."""

    champs = lire_corps(schemas.MissionPatch, partiel=True)

    bdd = session_bdd()
    mission = donnees_missions.trouver(bdd, id_mission)
    for cle, valeur in champs.items():
        setattr(mission, cle, valeur)

    bdd.commit()
    return mission.en_dict(), 200


@bp.delete("/missions/<int(min=1):id_mission>")
@permission_requise("supprimer")
def supprimer(id_mission: int):
    """Supprime une mission (204 sans corps), sauf si elle a encore un équipage."""

    bdd = session_bdd()
    mission = donnees_missions.trouver(bdd, id_mission)
    if donnees_astronautes.lister(bdd, mission_id=id_mission):
        raise MissionUtilisee(mission.id)

    donnees_missions.supprimer(bdd, mission)
    bdd.commit()
    return "", 204
