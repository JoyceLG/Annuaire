from flask import Flask, request, url_for

ASTRONAUTES = [
    {"nom": "Neil Armstrong", "role": "commandant", "mission": "Apollo 11"},
    {"nom": "Alan Bean", "role": "pilote", "mission": "Apollo 12"},
    {"nom": "Peter Conrad", "role": "commandant", "mission": "Apollo 12"},
    {"nom": "Edgar Mitchell", "role": "pilote", "mission": "Apollo 14"},
    {"nom": "Alan Shepard", "role": "commandant", "mission": "Apollo 14"},
]

app = Flask(__name__)


###################################
# SESSION 5
###################################


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
@app.get("/api/astronautes/<int(min=1):numero>")
def lire_astronaute(numero: int):
    if numero > len(ASTRONAUTES):
        return {"erreur": f"L'astronaute {numero} n'existe pas"}, 404
    return ASTRONAUTES[numero - 1]


# Ajoute un astronaute à la liste
# Requete de test :
# curl -i -X POST http://127.0.0.1:5000/api/astronautes -H "Content-Type: application/json" -d '{"nom": "Michel Colin", "role": "commandant", "mission": "Apollo 15"}'
@app.post("/api/astronautes")
def ajoute_astronaute():
    donnees = request.get_json()
    nouvel_astronaute = {
        "nom": donnees.get("nom"),
        "role": donnees.get("role"),
        "mission": donnees.get("mission"),
    }
    ASTRONAUTES.append(nouvel_astronaute)
    numero = len(ASTRONAUTES)
    return (
        nouvel_astronaute,
        201,
        {"Location": url_for("lire_astronaute", numero=numero)},
    )


# Remplace l'astronaute
# Requete de test :
# curl -i -X PUT http://127.0.0.1:5000/api/astronautes/6 -H "Content-Type: application/json" -d '{"nom": "Michael Collins", "role": "pilote", "mission": "Apollo 11"}'
@app.put("/api/astronautes/<int(min=1):numero>")
def remplace_astronaute(numero: int):
    if numero > len(ASTRONAUTES):
        return {"erreur": f"L'astronaute {numero} n'existe pas"}, 404
    donnees = request.get_json()
    nom = donnees.get("nom")
    role = donnees.get("role")
    mission = donnees.get("mission")
    astronaute_remplacement = {"nom": nom, "role": role, "mission": mission}
    ASTRONAUTES[numero - 1] = astronaute_remplacement
    return astronaute_remplacement, 200


# Retire l'astronaute de la liste
# Requete de test :
# curl -i -X DELETE http://127.0.0.1:5000/api/astronautes/1
@app.delete("/api/astronautes/<int(min=1):numero>")
def supprime_astronaute(numero: int):
    if numero > len(ASTRONAUTES):
        return {"erreur": f"L'astronaute {numero} n'existe pas"}, 404

    ASTRONAUTES.pop(numero - 1)
    return "", 204
