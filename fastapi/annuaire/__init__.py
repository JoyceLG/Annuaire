from fastapi import FastAPI

from annuaire.config import Config, choisir_config
from annuaire.gestionnaires import enregistrer_gestionnaires
from annuaire.routes import astronautes, missions, technique

__all__ = ["creer_app"]

def creer_app(config: type[Config] | str | None = None) -> FastAPI:
    """Construit une application FastAPI."""
    
    if config is None or isinstance(config, str):
        config = choisir_config(config)

    documentee = config.DOCUMENTATION_PUBLIQUE

    app = FastAPI(
        title="Annuaire des astronautes",
        description=(
            "API de gestion des astronautes et de leurs missions.\n\n"
            "Projet fil rouge de la formation Flask puis FastAPI."
        ),
        version="1.0.0",
        openapi_tags=[
            {"name": "Astronautes", "description": "Membres d'équipage et leurs qualifications."},
            {"name": "Missions", "description": "Missions spatiales."},
            {"name": "Technique", "description": "Points de contrôle de l'application."},
        ],
        docs_url="/docs" if documentee else None,
        redoc_url="/redoc" if documentee else None,
        openapi_url="/openapi.json" if documentee else None,
    )
    
    app.include_router(astronautes.router)
    app.include_router(technique.router)
    app.include_router(missions.router)
    enregistrer_gestionnaires(app)
    
    return app
