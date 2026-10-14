"""Gestionnaires d'erreurs pour l'annuaire des astronautes"""

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from annuaire.erreurs import (
    AstronauteIntrouvable,
    MissionIntrouvable,
    QualificationIncoherente,
)


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

    @app.exception_handler(QualificationIncoherente)
    async def gerer_qualification_incoherente(
        request: Request, erreur: QualificationIncoherente
    ):
        return JSONResponse(status_code=422, content={"erreur": str(erreur)})

    @app.exception_handler(RequestValidationError)
    async def gerer_validation(request: Request, erreur: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"detail": jsonable_encoder(erreur.errors())},
        )

    @app.exception_handler(MissionIntrouvable)
    async def gerer_mission_introuvable(
        request: Request, erreur: MissionIntrouvable
    ):
        return JSONResponse(
            status_code=404,
            content={"erreur": f"La mission {erreur.id_mission} n'existe pas"},
        )
