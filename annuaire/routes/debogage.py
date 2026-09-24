"""Routes d'aide au débogage, enregistrées uniquement quand `DEBUG` est actif.

Elles n'ont aucune raison d'exister en production : `/plante` y offrirait à
n'importe qui le moyen de provoquer une erreur 500 à volonté.
"""

from flask import Blueprint

from .commun import PREFIXE_API, publique

bp = Blueprint("debogage", __name__, url_prefix=PREFIXE_API)


@bp.get("/plante")
@publique
def plante():
    """Lève une erreur non gérée, pour vérifier le gestionnaire 500 et le journal."""

    return 1 / 0
