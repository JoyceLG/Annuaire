from flask import Blueprint, request, url_for
from session_web import session_bdd
import donnees
from erreurs import DonneesInvalides
import validation

bp = Blueprint("astronautes", __name__, url_prefix="/api")


def lire_corps_json(partiel: bool = False) -> dict:
    """Lit et valide le corps JSON, ou lève DonneesInvalides."""

    donnees_entree = request.get_json(silent=True)

    if not isinstance(donnees_entree, dict):
        raise DonneesInvalides({"corps": "doit être un objet JSON"})
    
    if partiel and not donnees_entree:
        raise DonneesInvalides({"corps": "ne peut pas être vide"})

    erreurs = validation.valider_astronaute(donnees_entree, partiel)
    if erreurs:
        raise DonneesInvalides(erreurs)

    return donnees_entree



@bp.route("/echo", methods=["GET", "POST"])
def echo():
    """Renvoie le détail de la requête reçue."""
    return {
        "methode": request.method,
        "chemin": request.path,
        "query_string": dict(request.args),
        "content_type": request.headers.get("Content-Type"),
        "corps_json": request.get_json(silent=True),
    }


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
        mission=request.args.get("mission"),
    )
    return [a.en_dict() for a in astronautes]


@bp.post("/astronautes")
def ajoute_astronaute():
    """Ajoute un nouvel astronaute à la liste, et renvoie son en-tête Location."""

    donnees_entree = lire_corps_json()
    bdd = session_bdd()
    nouvel_astronaute = donnees.creer_astronaute(bdd, donnees_entree)
    bdd.commit()
    return (
        nouvel_astronaute.en_dict(),
        201,
        {
            "Location": url_for(
                "astronautes.lire_astronaute", id_astronaute=nouvel_astronaute.id
            )
        },
    )


@bp.put("/astronautes/<int(min=1):id_astronaute>")
def remplace_astronaute(id_astronaute: int):
    """Remplace les informations d'un astronaute donné."""

    bdd = session_bdd()
    astronaute = donnees.trouver_astronaute(bdd, id_astronaute)

    donnees_entree = lire_corps_json()

    astronaute.nom = donnees_entree["nom"]
    astronaute.role = donnees_entree["role"]
    astronaute.mission = donnees_entree["mission"]
    bdd.commit()
    return astronaute.en_dict(), 200


@bp.patch("/astronautes/<int(min=1):id_astronaute>")
def modifie_astronaute(id_astronaute: int):
    """Modifie partiellement les informations d'un astronaute donné."""

    bdd = session_bdd()
    astronaute = donnees.trouver_astronaute(bdd, id_astronaute)

    donnees_entree = lire_corps_json(True)
    
    for cle, valeur in donnees_entree.items():
        setattr(astronaute, cle, valeur)
    bdd.commit()
    return astronaute.en_dict(), 200


@bp.delete("/astronautes/<int(min=1):id_astronaute>")
def supprime_astronaute(id_astronaute: int):
    """Supprime un astronaute de la liste (204 sans corps)."""


    bdd = session_bdd()
    astronaute = donnees.trouver_astronaute(bdd, id_astronaute)
    donnees.supprimer_astronaute(bdd, astronaute)
    bdd.commit()
    return "", 204
