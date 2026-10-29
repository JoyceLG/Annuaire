"""Gestionnaires d'erreurs pour l'annuaire des astronautes"""

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from annuaire.erreurs import (
    AstronauteIntrouvable,
    AuthentificationRequise,
    LimiteTropGrande,
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

    @app.exception_handler(AuthentificationRequise)
    async def gerer_authentification_requise(
        request: Request, erreur: AuthentificationRequise
    ):
        # Un 401 doit dire au client quel schéma d'authentification est attendu.
        return JSONResponse(
            status_code=401,
            content={"erreur": "Authentification requise"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(LimiteTropGrande)
    async def gerer_limite_trop_grande(request: Request, erreur: LimiteTropGrande):
        # 422 comme toute valeur refusée : le maximum vient de la configuration,
        # il ne peut pas être écrit dans Query(le=...) comme le minimum.
        return JSONResponse(status_code=422, content={"erreur": str(erreur)})
