"""Les blueprints, un par ressource, plus le garde-fou d'accès."""

from flask import Flask

from . import astronautes, missions, utilisateurs
from .commun import refuser_par_defaut

BLUEPRINTS = (astronautes.bp, missions.bp, utilisateurs.bp)


def enregistrer_blueprints(app: Flask) -> None:
    for bp in BLUEPRINTS:
        app.register_blueprint(bp)

    # Posé sur l'application et non sur un blueprint : une vue ajoutée hors
    # blueprint doit elle aussi se déclarer publique ou protégée.
    app.before_request(refuser_par_defaut)
