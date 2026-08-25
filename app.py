from flask import Flask
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

