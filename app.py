from flask import Flask, request

ASTRONAUTES = [
    {"nom": "Neil Armstrong", "role": "commandant", "mission": "Apollo 11"},
    {"nom": "Alan Bean", "role": "pilote", "mission": "Apollo 12"},
    {"nom": "Peter Conrad", "role": "commandant", "mission": "Apollo 12"},
    {"nom": "Edgar Mitchell", "role": "pilote", "mission": "Apollo 14"},
    {"nom": "Alan Shepard", "role": "commandant", "mission": "Apollo 14"},
]

app = Flask(__name__)


###################################
# SESSION 4
###################################

@app.route("/api/echo", methods=["GET", "POST"])
def echo():
    lignes = [
        f"Méthode : {request.method}",
        f"Chemin : {request.path}",
        f"Query string : {dict(request.args)}",
        f"Content-Type : {request.headers.get('Content-Type')}",
        f"Corps JSON : {request.get_json(silent=True)}",
    ]
    return "<br>".join(lignes)


# Liste des noms, séparés par des virgules
# Requete de test : curl "http://127.0.0.1:5000/api/astronautes?role=commandant&mission=Apollo%2011"
@app.get("/api/astronautes")
def liste_astronautes():
    filtre_role = request.args.get("role")
    filtre_mission = request.args.get("mission")
    resultats = ASTRONAUTES
    if filtre_role:
        resultats = [n for n in resultats if filtre_role.lower() in n["role"].lower()]
    if filtre_mission:
        resultats = [n for n in resultats if filtre_mission.lower() in n["mission"].lower()]
    return "Astronautes : " + ", ".join(n["nom"] for n in resultats)


# Ajoute un astronaute à la liste
# Requete de test : 
# curl -X POST http://127.0.0.1:5000/api/astronautes -H "Content-Type: application/json" -d '{"nom": "Michel Colin", "role": "pilote", "mission": "Apollo 11"}'
@app.post("/api/astronautes")
def ajoute_astronaute():
    donnees = request.get_json()
    nom = donnees.get("nom")
    role = donnees.get("role")
    mission = donnees.get("mission")
    nouvel_astronaute = {"nom": nom, "role": role, "mission": mission}
    ASTRONAUTES.append(nouvel_astronaute)
    return f"{nom} a été ajouté à la liste des astronautes"


# Remplace l'astronaute
# curl -X PUT http://127.0.0.1:5000/api/astronautes/6 -H "Content-Type: application/json" -d '{"nom": "Michael Collins", "role": "pilote", "mission": "Apollo 11"}'
@app.put("/api/astronautes/<int(min=1):numero>")
def remplace_astronaute(numero: int):
    if numero > len(ASTRONAUTES):
        return f"L'astronaute N°{numero} n'existe pas"
    donnees = request.get_json()
    nom = donnees.get("nom")
    role = donnees.get("role")
    mission = donnees.get("mission")
    astronaute_remplacement = {"nom": nom, "role": role, "mission": mission}
    ASTRONAUTES[numero - 1] = astronaute_remplacement
    return f"L'astronaute N°{numero} a été remplacé par {nom}"


# Retire l'astronaute de la liste
@app.delete("/api/astronautes/<int(min=1):numero>")
def supprime_astronaute(numero: int):
    if numero > len(ASTRONAUTES):
        return f"L'astronaute N°{numero} n'existe pas"

    ASTRONAUTES.pop(numero - 1)
    return f"L'astronaute N°{numero} a été supprimé de la liste"