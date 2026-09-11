from datetime import datetime, UTC

from flask import Blueprint, request, url_for, g
from functools import wraps
from pydantic import ValidationError, BaseModel

from modeles import Utilisateur
from session_web import session_bdd
from erreurs import DonneesInvalides, MissionUtilisee, JetonManquant

import schemas
import donnees
import jetons

bp = Blueprint("astronautes", __name__, url_prefix="/api")


class Tables:
    ASTRONAUTE = "astronaute"
    MISSION = "mission"


def lire_corps(modele: type[BaseModel], partiel: bool = False) -> dict:
    """Lit le corps JSON, le valide contre le modèle, renvoie un dict de champs."""

    corps = request.get_json(silent=True)
    if not isinstance(corps, dict):
        raise DonneesInvalides({"corps": "doit être un objet JSON"})

    if not corps:
        raise DonneesInvalides({"corps": "ne peut pas être vide"})

    try:
        entree = modele.model_validate(corps)
    except ValidationError as e:
        raise DonneesInvalides(schemas.convertir_erreurs(e))

    if partiel:
        donnees = entree.model_dump(exclude_unset=True)
    else:
        donnees = entree.model_dump()

    return donnees


def jeton_de_la_requete() -> str:
    entete = request.headers.get("Authorization", "")
    if not entete.startswith("Bearer "):
        raise JetonManquant()
    return entete.removeprefix("Bearer ")


def authentification_requise(fonction):
    @wraps(fonction)
    def enveloppe(*args, **kwargs):
        id_utilisateur = jetons.lire_jeton(jeton_de_la_requete())
        g.utilisateur = donnees.trouver_utilisateur(session_bdd(), id_utilisateur)
        return fonction(*args, **kwargs)

    return enveloppe


# ================= GET ===================


@bp.get("/astronautes/<int(min=1):id_astronaute>")
def lire_astronaute(id_astronaute: int):
    bdd = session_bdd()
    return donnees.trouver_astronaute(bdd, id_astronaute).en_dict()


@bp.get("/astronautes")
def liste_astronautes():
    bdd = session_bdd()
    astronautes = donnees.lister_astronautes(
        bdd,
        role=request.args.get("role"),
        mission_id=request.args.get("mission_id"),
    )
    return [a.en_dict() for a in astronautes]


@bp.get("/missions/<int(min=1):id_mission>")
def lire_mission(id_mission: int):
    bdd = session_bdd()
    return donnees.trouver_mission(bdd, id_mission).en_dict()


@bp.get("/missions")
def liste_missions():
    bdd = session_bdd()
    missions = donnees.lister_missions(
        bdd,
        programme=request.args.get("programme"),
    )
    return [m.en_dict() for m in missions]


@bp.get("/missions/<int(min=1):id_mission>/astronautes")
def liste_astronautes_mission(id_mission: int):
    bdd = session_bdd()
    mission = donnees.trouver_mission(bdd, id_mission)
    return [a.en_dict() for a in mission.astronautes]


@bp.get("/moi")
@authentification_requise
def lire_utilisateur_courant():
    utilisateur_courant: Utilisateur = g.utilisateur
    return (utilisateur_courant.en_dict(), 200)


# ================= POST ===================


@bp.post("/astronautes")
@authentification_requise
def ajoute_astronaute():

    donnees_entree = lire_corps(schemas.AstronauteEntree)

    bdd = session_bdd()
    astronaute = donnees.creer_astronaute(bdd, donnees_entree)
    bdd.commit()
    return (
        astronaute.en_dict(),
        201,
        {
            "Location": url_for(
                "astronautes.lire_astronaute", id_astronaute=astronaute.id
            )
        },
    )


@bp.post("/missions")
@authentification_requise
def ajoute_mission():
    """Ajoute une nouvelle mission à la liste, et renvoie son en-tête Location."""

    donnees_entree = lire_corps(schemas.MissionEntree)

    bdd = session_bdd()
    nouvelle_mission = donnees.creer_mission(bdd, donnees_entree)
    bdd.commit()

    return (
        nouvelle_mission.en_dict(),
        201,
        {
            "Location": url_for(
                "astronautes.lire_mission", id_mission=nouvelle_mission.id
            )
        },
    )


@bp.post("/inscription")
def inscription_utilisateur():

    donnees_entree = lire_corps(schemas.InscriptionEntree)

    bdd = session_bdd()
    nouvel_utilisateur = donnees.creer_utilisateur(
        bdd, donnees_entree["email"], donnees_entree["mot_de_passe"]
    )
    bdd.commit()

    return (nouvel_utilisateur.en_dict(), 201)


@bp.post("/connexion")
def connexion_utilisateur():

    donnees_entree = lire_corps(schemas.ConnexionEntree)

    bdd = session_bdd()
    utilisateur = donnees.verifier_identifiants(
        bdd, donnees_entree["email"], donnees_entree["mot_de_passe"]
    )
    valeur_retour = utilisateur.en_dict()
    
    utilisateur.derniere_connexion = datetime.now(UTC)
    bdd.commit()

    return {
        "jeton": jetons.creer_jeton(utilisateur.id),
        "utilisateur": valeur_retour,
    }, 200


# ================= PUT ===================


@bp.put("/astronautes/<int(min=1):id_astronaute>")
@authentification_requise
def remplace_astronaute(id_astronaute: int):
    """Remplace les informations d'un astronaute donné."""

    donnees_entree = lire_corps(schemas.AstronauteEntree)

    bdd = session_bdd()
    astronaute = donnees.trouver_astronaute(bdd, id_astronaute)

    if "mission_id" in donnees_entree:
        donnees.trouver_mission(bdd, donnees_entree["mission_id"])

    for cle, valeur in donnees_entree.items():
        setattr(astronaute, cle, valeur)

    bdd.commit()
    return astronaute.en_dict(), 200


@bp.put("/missions/<int(min=1):id_mission>")
@authentification_requise
def remplace_mission(id_mission: int):
    """Remplace les informations d'une mission donnée."""

    donnees_entree = lire_corps(schemas.MissionEntree)

    bdd = session_bdd()
    mission = donnees.trouver_mission(bdd, id_mission)

    for cle, valeur in donnees_entree.items():
        setattr(mission, cle, valeur)

    bdd.commit()
    return mission.en_dict(), 200


# ================= PATCH ===================


@bp.patch("/astronautes/<int(min=1):id_astronaute>")
@authentification_requise
def modifie_astronaute(id_astronaute: int):
    """Modifie partiellement les informations d'un astronaute donné."""

    donnees_entree = lire_corps(schemas.AstronautePatch, True)

    bdd = session_bdd()
    astronaute = donnees.trouver_astronaute(bdd, id_astronaute)

    if "mission_id" in donnees_entree:
        donnees.trouver_mission(bdd, donnees_entree["mission_id"])

    for cle, valeur in donnees_entree.items():
        setattr(astronaute, cle, valeur)

    bdd.commit()
    return astronaute.en_dict(), 200


@bp.patch("/missions/<int(min=1):id_mission>")
@authentification_requise
def modifie_mission(id_mission: int):
    """Modifie partiellement les informations d'une mission donnée."""

    donnees_entree = lire_corps(schemas.MissionPatch, True)

    bdd = session_bdd()
    mission = donnees.trouver_mission(bdd, id_mission)

    for cle, valeur in donnees_entree.items():
        setattr(mission, cle, valeur)

    bdd.commit()
    return mission.en_dict(), 200


# ================= DELETE ===================


@bp.delete("/astronautes/<int(min=1):id_astronaute>")
@authentification_requise
def supprime_astronaute(id_astronaute: int):
    """Supprime un astronaute de la liste (204 sans corps)."""

    bdd = session_bdd()
    astronaute = donnees.trouver_astronaute(bdd, id_astronaute)
    donnees.supprimer_astronaute(bdd, astronaute)
    bdd.commit()
    return "", 204


@bp.delete("/missions/<int(min=1):id_mission>")
@authentification_requise
def supprime_mission(id_mission: int):
    """Supprime une mission de la liste (204 sans corps)."""

    bdd = session_bdd()
    mission = donnees.trouver_mission(bdd, id_mission)
    if donnees.lister_astronautes(bdd, mission_id=id_mission):
        raise MissionUtilisee(mission.id)
    donnees.supprimer_mission(bdd, mission)
    bdd.commit()
    return "", 204
