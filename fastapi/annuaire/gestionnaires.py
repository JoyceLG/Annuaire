"""Gestionnaires d'erreurs pour l'annuaire des astronautes"""

from fastapi import Request
from fastapi.responses import JSONResponse
from annuaire.erreurs import AstronauteIntrouvable


def enregistrer_gestionnaires(app):
    """
    Enregistre les gestionnaires d'erreurs pour l'application FastAPI.

    Parameters
    ----------
    app : FastAPI
        L'application FastAPI pour laquelle enregistrer les gestionnaires d'erreurs.

    """

    @app.exception_handler(AstronauteIntrouvable)
    async def gerer_astronaute_introuvable(
        request: Request, erreur: AstronauteIntrouvable
    ):
        return JSONResponse(
            status_code=404,
            content={"erreur": f"L'astronaute {erreur.id_astronaute} n'existe pas"},
        )
