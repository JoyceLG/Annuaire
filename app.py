from flask import Flask, request, url_for

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
# SESSION 7
###################################


# Fonction de recherche par id
def trouver_astronaute(id_astronaute: int):
    for astronaute in ASTRONAUTES:
        if astronaute["id"] == id_astronaute:
            return astronaute
    return None


# Fonction de validation des données d'entrée
def valider_astronaute(donnees, partiel=False):
    """Renvoie un dictionnaire d'erreurs, vide si tout est valide."""
    erreurs = {}
    
    inconnus = set(donnees) - set(CHAMPS_ASTRONAUTE)
    if inconnus:
        erreurs["champs_inconnus"] = ", ".join(sorted(inconnus))
        return erreurs      # inutile de valider des champs qu'on refuse

    champs_verification = donnees if partiel else CHAMPS_ASTRONAUTE

    for champ in champs_verification:
        if champ not in donnees:
            erreurs[champ] = "champ obligatoire manquant"
        elif not isinstance(donnees[champ], str):
            erreurs[champ] = "doit être une chaîne de caractères"
        elif not donnees[champ].strip():
            erreurs[champ] = "ne doit pas être vide"

    if "role" in donnees:
        if donnees["role"] not in ROLES_VALIDES:
            erreurs["role"] = f"doit être l'un de : {', '.join(sorted(ROLES_VALIDES))}"

    return erreurs


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
    if astronaute is None:
        return {"erreur": f"L'astronaute {id_astronaute} n'existe pas"}, 404
    return astronaute


# Ajoute un astronaute à la liste
# Requete de test :
# POST invalide → 400 
# curl -i -X POST http://127.0.0.1:5000/api/astronautes -H "Content-Type: application/json" -d '{"nom": "X", "role": "pilote", "mission": "Apollo 1", "salaire": 50000}'
@app.post("/api/astronautes")
def ajoute_astronaute():

    global prochain_id

    donnees = request.get_json(silent=True)
    if not isinstance(donnees, dict):
        return {"erreur": "Le corps doit être un objet JSON"}, 400

    erreurs = valider_astronaute(donnees)
    if erreurs:
        return {"erreur": "Validation échouée", "details": erreurs}, 400

    nouvel_astronaute = {
        "id": prochain_id,
        "nom": donnees["nom"],
        "role": donnees["role"],
        "mission": donnees["mission"],
    }
    prochain_id += 1
    ASTRONAUTES.append(nouvel_astronaute)
    return (
        nouvel_astronaute,
        201,
        {"Location": url_for("lire_astronaute", id_astronaute=nouvel_astronaute["id"])},
    )


# Remplace l'astronaute
# Requetes de test :
# PUT incomplet → 400 (alors que le PATCH équivalent passerait)
# curl -i -X PUT http://127.0.0.1:5000/api/astronautes/2 -H "Content-Type: application/json" -d '{"nom": "Alan Bean"}'
# Et le test final : plus aucun 500 possible
# curl "http://127.0.0.1:5000/api/astronautes?role=pilote"

@app.put("/api/astronautes/<int(min=1):id_astronaute>")
def remplace_astronaute(id_astronaute: int):

    astronaute = trouver_astronaute(id_astronaute)
    if astronaute is None:
        return {"erreur": f"L'astronaute {id_astronaute} n'existe pas"}, 404

    donnees = request.get_json(silent=True)
    if not isinstance(donnees, dict):
        return {"erreur": "Le corps doit être un objet JSON"}, 400

    erreurs = valider_astronaute(donnees)
    if erreurs:
        return {"erreur": "Validation échouée", "details": erreurs}, 400

    astronaute["nom"] = donnees["nom"]
    astronaute["role"] = donnees["role"]
    astronaute["mission"] = donnees["mission"]
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
    if astronaute is None:
        return {"erreur": f"L'astronaute {id_astronaute} n'existe pas"}, 404

    donnees = request.get_json(silent=True)
    if not isinstance(donnees, dict):
        return {"erreur": "Le corps doit être un objet JSON"}, 400

    if not donnees:
        return {"erreur": "Rien à modifier"}, 400

    erreurs = valider_astronaute(donnees, True)
    if erreurs:
        return {"erreur": "Validation échouée", "details": erreurs}, 400

    if "nom" in donnees:
        astronaute["nom"] = donnees["nom"]
    if "role" in donnees:
        astronaute["role"] = donnees["role"]
    if "mission" in donnees:
        astronaute["mission"] = donnees["mission"]

    return astronaute, 200


# Retire l'astronaute de la liste
# Requete de test :
# curl -i -X DELETE http://127.0.0.1:5000/api/astronautes/1
@app.delete("/api/astronautes/<int(min=1):id_astronaute>")
def supprime_astronaute(id_astronaute: int):
    astronaute = trouver_astronaute(id_astronaute)
    if astronaute is None:
        return {"erreur": f"L'astronaute {id_astronaute} n'existe pas"}, 404
    ASTRONAUTES.remove(astronaute)
    return "", 204
