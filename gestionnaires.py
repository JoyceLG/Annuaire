from werkzeug.exceptions import HTTPException
from erreurs import AstronauteIntrouvable, DonneesInvalides


def enregistrer_gestionnaires(app):
    """
    Enregistre les gestionnaires d'erreurs pour l'application Flask.

    Parameters
    ----------
    app : Flask
        L'application Flask pour laquelle enregistrer les gestionnaires d'erreurs.

    """
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
