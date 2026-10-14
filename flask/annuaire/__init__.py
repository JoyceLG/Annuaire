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
from .config import Config, choisir_config
from .gestionnaires import enregistrer_gestionnaires
from .journal import configurer_journal
from .routes import enregistrer_blueprints
from .securite import initialiser_hachage

__all__ = ["creer_app"]


def creer_app(config: type[Config] | str | None = None, **surcharges) -> Flask:
    """Construit une application. Les surcharges priment sur la configuration.

    `config` accepte une classe (`creer_app(ConfigTest)`, ce que font les tests),
    un nom d'environnement (`creer_app("production")`), ou rien : la variable
    d'environnement `ENVIRONNEMENT` tranche alors, et à défaut le développement.
    """

    if config is None or isinstance(config, str):
        config = choisir_config(config)

    app = Flask(__name__)
    # `resoudre` empile les trois sources dans l'ordre : attributs de classe,
    # variables d'environnement, puis surcharges. La validation porte donc sur
    # ce que l'application utilisera vraiment, et non sur la seule classe.
    app.config.update(config.resoudre(**surcharges))
    config.valider(app.config)

    bdd.initialiser(app)
    initialiser_hachage(app)
    enregistrer_gestionnaires(app)
    enregistrer_blueprints(app)
    enregistrer_commandes(app)
    configurer_journal(app)
    return app
