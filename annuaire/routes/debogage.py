"""Routes d'aide au débogage, enregistrées uniquement quand `DEBUG` est actif.

Elles n'ont aucune raison d'exister en production : `/plante` y offrirait à
n'importe qui le moyen de provoquer une erreur 500 à volonté.
"""
import time

from flask import Blueprint

from .commun import PREFIXE_API, publique

bp = Blueprint("debogage", __name__, url_prefix=PREFIXE_API)


@bp.get("/attente")
@publique
def attente():
    """Simule un appel à un service externe lent.

    `time.sleep` bloque le worker exactement comme le ferait une requête
    réseau : pour un worker WSGI synchrone, attendre le réseau ou attendre
    un minuteur sont indiscernables. C'est ce qui rend cette simulation
    représentative — et c'est précisément ce que l'async changera.
    """
    time.sleep(0.5)
    return {"statut": "termine"}


@bp.get("/plante")
@publique
def plante():
    """Lève une erreur non gérée, pour vérifier le gestionnaire 500 et le journal."""

    return 1 / 0
