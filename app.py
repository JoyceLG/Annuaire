from flask import Flask, url_for
from datetime import datetime

ASTRONAUTES = [
    "Neil Armstrong",
    "Alan Bean",
    "Peter Conrad",
    "Edgar Mitchell",
    "Alan Shepard",
]

app = Flask(__name__)

###################################
# SESSION 1
###################################


@app.route("/")
def accueil():
    return "Bonjour !"


@app.route("/wip")
def wip():
    return " Work in progress !"


@app.route("/apropos")
def apropos():
    return "<h1>À propos</h1><p>Ma première application Flask.</p>"


@app.route("/date")
def date():
    maintenant = datetime.now()
    return f"Date et heure actuelles : {maintenant:%d/%m/%Y à %H:%M:%S}"


@app.route("/astronautes")
def astronautes():
    lignes = "".join(f"<li>{nom}</li>" for nom in ASTRONAUTES)
    return f"<p>Astronautes d'Apollo&nbsp;:</p><ul>{lignes}</ul>"


@app.route("/astronautes/<int:numero>")
def astronaute(numero: int):
    if numero < 1 or numero > len(ASTRONAUTES):
        return f"Aucun astronaute numéro {numero}"
    return ASTRONAUTES[numero - 1]


###################################
# SESSION 2
###################################


@app.route("/accueil-astronautes")
def accueil_astronautes():
    lien = url_for("astronaute", numero=1)  # donne "/astronautes/1"
    return f'<a href="{lien}">Le premier astronaute</a>'


@app.route("/astronautes/<int:numero>/lettre/<int:position>")
def lettre_astronaute(numero: int, position: int):
    if numero < 1 or numero > len(ASTRONAUTES):
        return f"Aucun astronaute numéro {numero}"
    nom_astronaute = ASTRONAUTES[numero - 1]
    if position < 1 or position > len(nom_astronaute):
        return (
            f"Aucune lettre à la position {position} pour l'astronaute numéro {numero}"
        )
    return nom_astronaute[position - 1]


@app.route("/carre/<int:n>")
def carre(n: int):
    return f"Le carré de {n} est {n * n}"


@app.route("/salut/<nom>")
def message_perso(nom: str):
    return f"Salut {nom} !"


@app.route("/celsius/<float(signed=True):degres>")
def celsius2fahrenheit(degres: float):
    fahrenheit: float = (degres * 9 / 5) + 32
    return f"Conversion {degres}°C est égale à {fahrenheit}°F"


@app.route("/recherche/<path:chemin>")
def recherche_chemin(chemin: str):
    return chemin


###################################
# SESSION 3
###################################


@app.get("/mission")
def lire_mission():
    return "Mission : Apollo 11"


@app.post("/mission")
def demarrer_mission():
    return "Mission démarrée !"


@app.delete("/mission")
def annuler_mission():
    return "Mission annulée"


# Liste des noms, séparés par des virgules
@app.get("/api/astronautes")
def liste_astronautes():
    return "La liste des astronautes : " + ", ".join(ASTRONAUTES)


# Ajoute un astronaute à la liste
@app.post("/api/astronautes/<nom>")
def ajoute_astronaute(nom: str):
    ASTRONAUTES.append(nom)
    return f"{nom} a été ajouté à la liste des astronautes"


# Remplace l'astronaute par ce nom
@app.put("/api/astronautes/<int(min=1):numero>/<nom>")
def renomme_astronaute(numero: int, nom: str):
    if numero > len(ASTRONAUTES):
        return f"L'astronaute N°{numero} n'existe pas"

    ASTRONAUTES[numero - 1] = nom
    return f"L'astronaute N°{numero} a été remplacé par {nom}"


# Retire l'astronaute de la liste
@app.delete("/api/astronautes/<int(min=1):numero>")
def supprime_astronaute(numero: int):
    if numero > len(ASTRONAUTES):
        return f"L'astronaute N°{numero} n'existe pas"

    ASTRONAUTES.pop(numero - 1)
    return f"L'astronaute N°{numero} a été supprimé de la liste"
