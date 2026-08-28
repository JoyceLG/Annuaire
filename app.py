from flask import Flask, request, url_for

ASTRONAUTES: list[dict[str, str | int]] = [
    {"id": 1, "nom": "Neil Armstrong", "role": "commandant", "mission": "Apollo 11"},
    {"id": 2, "nom": "Alan Bean", "role": "pilote", "mission": "Apollo 12"},
    {"id": 3, "nom": "Peter Conrad", "role": "commandant", "mission": "Apollo 12"},
    {"id": 4, "nom": "Edgar Mitchell", "role": "pilote", "mission": "Apollo 14"},
    {"id": 5, "nom": "Alan Shepard", "role": "commandant", "mission": "Apollo 14"},
]

prochain_id = 6

app = Flask(__name__)


###################################
# SESSION 6
###################################


# Fonction de recherche par id
def trouver_astronaute(id_astronaute: int) -> dict[str, int | str] | None:
    for astronaute in ASTRONAUTES:
        if astronaute["id"] == id_astronaute:
            return astronaute
    return None


# Renvoie le detail de la requete recue
# Requete de test :
# curl -i -X POST "http://127.0.0.1:5000/api/echo?ville=Houston" -H "Content-Type: application/json" -d '{"message": "ok"}'
@app.route("/api/echo", methods=["GET", "POST"])
def echo() -> dict[str, str | dict[str, str] | None]:
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
# curl -i -X POST http://127.0.0.1:5000/api/astronautes -H "Content-Type: application/json" -d '{"nom": "Michel Colin", "role": "commandant", "mission": "Apollo 15"}'
@app.post("/api/astronautes")
def ajoute_astronaute():
    global prochain_id
    donnees = request.get_json()
    nouvel_astronaute: dict[str, int | str] = {
        "id": prochain_id,
        "nom": donnees.get("nom"),
        "role": donnees.get("role"),
        "mission": donnees.get("mission"),
    }
    prochain_id += 1
    ASTRONAUTES.append(nouvel_astronaute)
    return (
        nouvel_astronaute,
        201,
        {"Location": url_for("lire_astronaute", id_astronaute=nouvel_astronaute["id"])},
    )


# Remplace l'astronaute
# Requete de test :
# curl -i -X PUT http://127.0.0.1:5000/api/astronautes/6 -H "Content-Type: application/json" -d '{"nom": "Michael Collins", "role": "pilote", "mission": "Apollo 11"}'
@app.put("/api/astronautes/<int(min=1):id_astronaute>")
def remplace_astronaute(id_astronaute: int):
    astronaute = trouver_astronaute(id_astronaute)
    if astronaute is None:
        return {"erreur": f"L'astronaute {id_astronaute} n'existe pas"}, 404
    donnees = request.get_json()
    astronaute["nom"] = donnees.get("nom")
    astronaute["role"] = donnees.get("role")
    astronaute["mission"] = donnees.get("mission")
    return astronaute, 200


# Modifie l'astronaute de la liste
# Requete de test :
# curl -X PATCH http://127.0.0.1:5000/api/astronautes/3 -H "Content-Type: application/json" -d '{"role": "pilote"}'
@app.patch("/api/astronautes/<int(min=1):id_astronaute>")
def modifie_astronaute(id_astronaute: int):
    
    astronaute = trouver_astronaute(id_astronaute)
    
    if astronaute is None:
        return {"erreur": f"L'astronaute {id_astronaute} n'existe pas"}, 404
    
    donnees = request.get_json()
    
    if not donnees:
        return {"erreur": "Rien à modifier"}, 400

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
