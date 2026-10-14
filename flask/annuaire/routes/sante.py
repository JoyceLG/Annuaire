"""Point de terminaison pour vérifier la santé de l'application."""

from flask import Blueprint
from sqlalchemy import literal, select
from sqlalchemy.exc import SQLAlchemyError

from ..bdd import session_bdd
from ..erreurs import BaseIndisponible
from .commun import PREFIXE_API, publique

bp = Blueprint("sante", __name__, url_prefix=PREFIXE_API)


@bp.get("/sante")
@publique
def sante():
    """Répond 200 si l'application joint sa base, 503 sinon."""

    try:
        session_bdd().scalar(select(literal(1)))
    except SQLAlchemyError as erreur:
        raise BaseIndisponible(str(erreur)) from erreur
    return {"statut": "ok"}
