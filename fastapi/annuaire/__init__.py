from fastapi import FastAPI

from annuaire.bdd import cycle_de_vie
from annuaire.config import Config, choisir_config
from annuaire.gestionnaires import enregistrer_gestionnaires
from annuaire.routes import astronautes, documentation, missions, technique

__all__ = ["creer_app"]

def creer_app(config: type[Config] | str | None = None) -> FastAPI:
    """Construit une application FastAPI."""
    
    if config is None or isinstance(config, str):
        config = choisir_config(config)

    publique = config.DOCUMENTATION_PUBLIQUE

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
        # Documentation publique : FastAPI sert lui-même les trois routes.
        # Sinon, routes/documentation.py les sert derrière une connexion.
        docs_url="/docs" if publique else None,
        redoc_url="/redoc" if publique else None,
        openapi_url="/openapi.json" if publique else None,
        # Ouvre le moteur et le pool avant la première requête, les ferme
        # après la dernière. Lit app.state.config, posé juste en dessous :
        # le lifespan ne s'exécute qu'au démarrage du serveur, donc après.
        lifespan=cycle_de_vie,
    )
    # Lue à chaque requête par la dépendance `configuration` : c'est la
    # configuration choisie ici qui s'applique, pas celle d'ENVIRONNEMENT.
    app.state.config = config
    
    app.include_router(astronautes.lecture)
    app.include_router(astronautes.ecriture)
    app.include_router(technique.router)
    app.include_router(missions.lecture)
    app.include_router(missions.ecriture)
    if not publique:
        app.include_router(documentation.router)
    enregistrer_gestionnaires(app)
    
    return app
