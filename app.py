from flask import Flask, request, url_for
from werkzeug.exceptions import HTTPException

ASTRONAUTES: list[dict[str, str | int]] = [
    {"id": 1, "nom": "Neil Armstrong", "role": "commandant", "mission": "Apollo 11"},
    {"id": 2, "nom": "Alan Bean", "role": "pilote", "mission": "Apollo 12"},
    {"id": 3, "nom": "Peter Conrad", "role": "commandant", "mission": "Apollo 12"},
    {"id": 4, "nom": "Edgar Mitchell", "role": "pilote", "mission": "Apollo 14"},
    {"id": 5, "nom": "Alan Shepard", "role": "commandant", "mission": "Apollo 14"},
]

CHAMPS_ASTRONAUTE = ("nom", "role", "mission")
ROLES_VALIDES = {"commandant", "pilote", "specialiste"}

prochain_id = 6

app = Flask(__name__)


###################################
# SESSION 8
###################################


class ErreurApi(Exception):
    """Classe de base pour les erreurs métier."""


class AstronauteIntrouvable(ErreurApi):
    def __init__(self, id_astronaute: int):
        self.id_astronaute = id_astronaute
        super().__init__(f"L'astronaute {id_astronaute} n'existe pas")


class DonneesInvalides(ErreurApi):
    def __init__(self, details: dict):
        self.details = details
        super().__init__("Validation échouée")


@app.errorhandler(404)
def gerer_404(erreur):
    return {"erreur": "Ressource introuvable"}, 404


@app.errorhandler(HTTPException)
def gerer_erreur_http(erreur):
    return {"erreur": erreur.description}, erreur.code


@app.errorhandler(AstronauteIntrouvable)
def gerer_astronaute_introuvable(erreur):
    return {"erreur": str(erreur)}, 404


@app.errorhandler(DonneesInvalides)
def gerer_donnees_invalides(erreur):
    return {"erreur": str(erreur), "details": erreur.details}, 400


@app.errorhandler(Exception)
def gerer_erreur_inattendue(erreur):
    app.logger.exception("Erreur non gérée")
    return {"erreur": "Erreur interne du serveur"}, 500


# Fonction de recherche par id
def trouver_astronaute(id_astronaute: int):
    for astronaute in ASTRONAUTES:
        if astronaute["id"] == id_astronaute:
            return astronaute
    raise AstronauteIntrouvable(id_astronaute)


# Fonction de validation des données d'entrée
def valider_astronaute(donnees, partiel=False):
    """Renvoie un dictionnaire d'erreurs, vide si tout est valide."""
    erreurs = {}

    inconnus = set(donnees) - set(CHAMPS_ASTRONAUTE)
    if inconnus:
        erreurs["champs_inconnus"] = ", ".join(sorted(inconnus))
        return erreurs  # inutile de valider des champs qu'on refuse

    champs_verification = donnees if partiel else CHAMPS_ASTRONAUTE

    for champ in champs_verification:
        if champ not in donnees:
            erreurs[champ] = "champ obligatoire manquant"
        elif not isinstance(donnees[champ], str):
            erreurs[champ] = "doit être une chaîne de caractères"
        elif not donnees[champ].strip():
            erreurs[champ] = "ne doit pas être vide"

    if "role" in donnees and "role" not in erreurs:
        if donnees["role"] not in ROLES_VALIDES:
            erreurs["role"] = f"doit être l'un de : {', '.join(sorted(ROLES_VALIDES))}"

    return erreurs


def lire_corps_json(partiel: bool = False) -> dict:
    """Lit et valide le corps JSON, ou lève DonneesInvalides."""
    
    donnees = request.get_json(silent=True)
    
    if not isinstance(donnees, dict):
        raise DonneesInvalides({"corps": "doit être un objet JSON"})

    erreurs = valider_astronaute(donnees, partiel)
    if erreurs:
        raise DonneesInvalides(erreurs)
    
    return donnees


# Renvoie le detail de la requete recue
# Requete de test :
# curl -i -X POST "http://127.0.0.1:5000/api/echo?ville=Houston" -H "Content-Type: application/json" -d '{"message": "ok"}'
@app.route("/api/echo", methods=["GET", "POST"])
def echo():
    return {
        "methode": request.method,
        "chemin": request.path,
        "query_string": dict(request.args),
        "content_type": request.headers.get("Content-Type"),
        "corps_json": request.get_json(silent=True),
    }


# Liste des noms
# Requete de test : curl -i "http://127.0.0.1:5000/api/astronautes?role=commandant&mission=Apollo%2011"
@app.get("/api/astronautes")
def liste_astronautes():
    filtre_role = request.args.get("role")
    filtre_mission = request.args.get("mission")
    resultats = ASTRONAUTES
    if filtre_role:
        resultats = [n for n in resultats if filtre_role.lower() in n["role"].lower()]
    if filtre_mission:
        resultats = [
            n for n in resultats if filtre_mission.lower() in n["mission"].lower()
        ]

    return resultats


# Donne les infos d'un astronaute demandé
# Requete de test : curl -i http://127.0.0.1:5000/api/astronautes/2
@app.get("/api/astronautes/<int(min=1):id_astronaute>")
def lire_astronaute(id_astronaute: int):
    astronaute = trouver_astronaute(id_astronaute)
    return astronaute


# Ajoute un astronaute à la liste
# Requete de test :
# curl -i -X POST http://127.0.0.1:5000/api/astronautes -H "Content-Type: application/json" -d '{"nom": "Michel Colin", "role": "commandant", "mission": "Apollo 15"}'
# POST invalide → 400
# curl -i -X POST http://127.0.0.1:5000/api/astronautes -H "Content-Type: application/json" -d '{"nom": "X", "role": "pilote", "mission": "Apollo 1", "salaire": 50000}'
@app.post("/api/astronautes")
def ajoute_astronaute():

    global prochain_id

    donnees = lire_corps_json()
    nouvel_astronaute = {"id": prochain_id, **donnees}
    prochain_id += 1
    ASTRONAUTES.append(nouvel_astronaute)
    return (
        nouvel_astronaute,
        201,
        {"Location": url_for("lire_astronaute", id_astronaute=nouvel_astronaute["id"])},
    )


# Remplace l'astronaute
# Requetes de test :
# curl -i -X PUT http://127.0.0.1:5000/api/astronautes/6 -H "Content-Type: application/json" -d '{"nom": "Michael Collins", "role": "pilote", "mission": "Apollo 11"}'
# PUT incomplet → 400 (alors que le PATCH équivalent passerait)
# curl -i -X PUT http://127.0.0.1:5000/api/astronautes/2 -H "Content-Type: application/json" -d '{"nom": "Alan Bean"}'


@app.put("/api/astronautes/<int(min=1):id_astronaute>")
def remplace_astronaute(id_astronaute: int):

    astronaute = trouver_astronaute(id_astronaute)

    donnees = lire_corps_json()
    
    astronaute.update(donnees)
    return astronaute, 200


# Modifie l'astronaute de la liste
# Requetes de test :
# PATCH avec un rôle invalide → 400
# curl -i -X PATCH http://127.0.0.1:5000/api/astronautes/2 -H "Content-Type: application/json" -d '{"role": "cosmonaute"}'
# PATCH avec un seul champ valide → 200
# curl -i -X PATCH http://127.0.0.1:5000/api/astronautes/2 -H "Content-Type: application/json" -d '{"role": "pilote"}'
@app.patch("/api/astronautes/<int(min=1):id_astronaute>")
def modifie_astronaute(id_astronaute: int):

    astronaute = trouver_astronaute(id_astronaute)

    donnees = lire_corps_json(True)
    
    astronaute.update(donnees) 

    return astronaute, 200


# Retire l'astronaute de la liste
# Requete de test :
# curl -i -X DELETE http://127.0.0.1:5000/api/astronautes/1
@app.delete("/api/astronautes/<int(min=1):id_astronaute>")
def supprime_astronaute(id_astronaute: int):
    astronaute = trouver_astronaute(id_astronaute)
    ASTRONAUTES.remove(astronaute)
    return "", 204
