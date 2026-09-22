"""Gestionnaires d'erreurs pour l'application Flask."""

import logging

from werkzeug.exceptions import HTTPException

from .erreurs import (
    AstronauteIntrouvable,
    DonneesInvalides,
    EmailDejaUtilise,
    IdentifiantsInvalides,
    JetonExpire,
    JetonInvalide,
    JetonManquant,
    MissionDejaExistante,
    MissionIntrouvable,
    MissionUtilisee,
    PermissionRefusee,
    UtilisateurIntrouvable,
)

logger = logging.getLogger(__name__)


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

    @app.errorhandler(MissionIntrouvable)
    def gerer_mission_introuvable(erreur):
        return {"erreur": str(erreur)}, 404

    @app.errorhandler(MissionDejaExistante)
    def gerer_mission_deja_existante(erreur):
        return {"erreur": str(erreur)}, 409

    @app.errorhandler(DonneesInvalides)
    def gerer_donnees_invalides(erreur):
        return {"erreur": str(erreur), "details": erreur.details}, 400

    @app.errorhandler(MissionUtilisee)
    def gerer_mission_utilisee(erreur):
        return {"erreur": str(erreur)}, 409

    @app.errorhandler(EmailDejaUtilise)
    def gerer_email_deja_utilise(erreur):
        return {"erreur": str(erreur)}, 409

    @app.errorhandler(IdentifiantsInvalides)
    def gerer_identifiants_invalides(erreur):
        logger.warning(
            "Identifiants invalides pour l'email %s depuis l'IP %s",
            erreur.email,
            erreur.ip,
        )
        return {"erreur": "Identifiants invalides"}, 401

    @app.errorhandler(UtilisateurIntrouvable)
    def gerer_utilisateur_introuvable(erreur):
        return {"erreur": str(erreur)}, 404

    @app.errorhandler(JetonManquant)
    def gerer_jeton_manquant(erreur):
        return {"erreur": str(erreur)}, 401

    @app.errorhandler(JetonExpire)
    def gerer_jeton_expire(erreur):
        logger.warning("Jeton expiré : %s", erreur.jeton_court)
        return {"erreur": "Jeton expiré"}, 401

    @app.errorhandler(JetonInvalide)
    def gerer_jeton_invalide(erreur):
        logger.warning("Jeton invalide : %s", erreur.jeton_court)
        return {"erreur": "Jeton invalide"}, 401

    @app.errorhandler(PermissionRefusee)
    def gerer_permission_refusee(erreur):
        logger.warning(
            "Permission %s refusée pour l'utilisateur %s sur le chemin %s",
            erreur.permission,
            erreur.utilisateur,
            erreur.chemin,
        )
        return {"erreur": "Permission refusée"}, 403

    @app.errorhandler(Exception)
    def gerer_erreur_inattendue(erreur):
        app.logger.exception("Erreur non gérée")
        logger.error("Erreur non gérée : %s", str(erreur), exc_info=True)
        return {"erreur": "Erreur interne du serveur"}, 500
