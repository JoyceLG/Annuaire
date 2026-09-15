"""API de l'annuaire des astronautes.

`creer_app` est la fabrique d'application : tout l'état — moteur SQLAlchemy,
hacheur, clé JWT — est rangé dans l'objet Flask plutôt que dans des globales
de module. Deux applications peuvent ainsi coexister, et les tests n'ont plus
à réécrire les attributs du paquet.

Lancer l'API :  flask --app "annuaire:creer_app" run --debug
"""

from flask import Flask

from . import bdd
from .cli import enregistrer_commandes
from .config import Config
from .gestionnaires import enregistrer_gestionnaires
from .routes import enregistrer_blueprints
from .securite import initialiser_hachage

__all__ = ["creer_app"]


def creer_app(config: type[Config] = Config, **surcharges) -> Flask:
    """Construit une application. Les surcharges priment sur la configuration."""

    app = Flask(__name__)
    app.config.from_object(config)
    app.config.update(surcharges)

    if not app.config["CLE_SECRETE_JWT"]:
        raise RuntimeError(
            "CLE_SECRETE_JWT est vide. Définissez-la avant de lancer l'application :\n"
            '  export CLE_SECRETE_JWT=$(python -c "import secrets;'
            ' print(secrets.token_urlsafe(32))")'
        )

    bdd.initialiser(app)
    initialiser_hachage(app)
    enregistrer_gestionnaires(app)
    enregistrer_blueprints(app)
    enregistrer_commandes(app)
    return app
