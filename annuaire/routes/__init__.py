"""Les blueprints, un par ressource, plus le garde-fou d'accès."""

from flask import Flask

from . import astronautes, debogage, missions, utilisateurs
from .commun import demarrer_requete, refuser_par_defaut, terminer_requete

BLUEPRINTS = (astronautes.bp, missions.bp, utilisateurs.bp)


def enregistrer_blueprints(app: Flask) -> None:
    for bp in BLUEPRINTS:
        app.register_blueprint(bp)

    # Les routes de débogage ne sont même pas déclarées hors développement :
    # une route absente ne peut pas être appelée par erreur.
    if app.config.get("DEBUG"):
        app.register_blueprint(debogage.bp)

    # Posé sur l'application et non sur un blueprint : une vue ajoutée hors
    # blueprint doit elle aussi se déclarer publique ou protégée.
    app.before_request(refuser_par_defaut)
    app.before_request(demarrer_requete)
    app.after_request(terminer_requete)
