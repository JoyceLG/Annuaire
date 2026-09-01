from flask import Blueprint, request, url_for
import donnees
from erreurs import DonneesInvalides
import validation

bp = Blueprint("astronautes", __name__, url_prefix="/api")


def lire_corps_json(partiel: bool = False) -> dict:
    """Lit et valide le corps JSON, ou lève DonneesInvalides."""

    donnees_entree = request.get_json(silent=True)

    if not isinstance(donnees_entree, dict):
        raise DonneesInvalides({"corps": "doit être un objet JSON"})

    erreurs = validation.valider_astronaute(donnees_entree, partiel)
    if erreurs:
        raise DonneesInvalides(erreurs)

    return donnees_entree


@bp.get("/astronautes")
def liste_astronautes():
    """Liste les astronautes, éventuellement filtrés par rôle et mission."""

    filtre_role = request.args.get("role")
    filtre_mission = request.args.get("mission")
    resultats = donnees.ASTRONAUTES
    if filtre_role:
        resultats = [n for n in resultats if filtre_role.lower() in n["role"].lower()]
    if filtre_mission:
        resultats = [
            n for n in resultats if filtre_mission.lower() in n["mission"].lower()
        ]

    return resultats


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
    """Renvoie les informations d'un astronaute donné."""
    return donnees.trouver_astronaute(id_astronaute)


@bp.post("/astronautes")
def ajoute_astronaute():
    """Ajoute un nouvel astronaute à la liste, et renvoie son en-tête Location."""

    donnees_entree = lire_corps_json()
    nouvel_astronaute = {"id": donnees.prochain_id, **donnees_entree}
    donnees.prochain_id += 1
    donnees.ASTRONAUTES.append(nouvel_astronaute)
    return (
        nouvel_astronaute,
        201,
        {
            "Location": url_for(
                "astronautes.lire_astronaute", id_astronaute=nouvel_astronaute["id"]
            )
        },
    )


@bp.put("/astronautes/<int(min=1):id_astronaute>")
def remplace_astronaute(id_astronaute: int):
    """Remplace les informations d'un astronaute donné."""

    astronaute = donnees.trouver_astronaute(id_astronaute)

    donnees_entree = lire_corps_json()

    astronaute.update(donnees_entree)
    return astronaute, 200


@bp.patch("/astronautes/<int(min=1):id_astronaute>")
def modifie_astronaute(id_astronaute: int):
    """Modifie partiellement les informations d'un astronaute donné."""

    astronaute = donnees.trouver_astronaute(id_astronaute)

    donnees_entree = lire_corps_json(True)

    astronaute.update(donnees_entree)

    return astronaute, 200


@bp.delete("/astronautes/<int(min=1):id_astronaute>")
def supprime_astronaute(id_astronaute: int):
    """Supprime un astronaute de la liste (204 sans corps)."""

    astronaute = donnees.trouver_astronaute(id_astronaute)
    donnees.ASTRONAUTES.remove(astronaute)
    return "", 204
