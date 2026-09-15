"""Outils partagés par les blueprints : lecture du corps et garde-fou d'accès."""

from flask import current_app, request
from pydantic import BaseModel, ValidationError

from .. import schemas
from ..erreurs import DonneesInvalides, PermissionRefusee


def publique(fonction):
    """Marque une vue comme accessible sans jeton.

    Le marqueur est posé sur la fonction elle-même, et non dans une liste de
    noms tenue à la main : impossible de le désynchroniser en renommant la vue.
    """

    fonction.publique = True
    return fonction


def refuser_par_defaut():
    """Refuse toute vue qui n'est ni publique ni protégée par un décorateur.

    Un oubli se solde par un 403 bien visible, jamais par une route ouverte.
    """

    if request.endpoint in (None, "static"):
        # URL inconnue (Flask répondra 404) ou fichier statique de Flask.
        return

    vue = current_app.view_functions.get(request.endpoint)
    if getattr(vue, "publique", False) or getattr(vue, "protegee", False):
        return
    raise PermissionRefusee(f"{request.endpoint} non déclarée")


def lire_corps(modele: type[BaseModel], partiel: bool = False) -> dict:
    """Lit le corps JSON, le valide contre le modèle, renvoie un dict de champs."""

    corps = request.get_json(silent=True)
    if not isinstance(corps, dict):
        raise DonneesInvalides({"corps": "doit être un objet JSON"})

    if not corps:
        raise DonneesInvalides({"corps": "ne peut pas être vide"})

    try:
        entree = modele.model_validate(corps)
    except ValidationError as erreur:
        raise DonneesInvalides(schemas.convertir_erreurs(erreur))

    # En PATCH, seuls les champs réellement envoyés sont repris : un champ
    # absent ne doit pas écraser la valeur existante avec sa valeur par défaut.
    return entree.model_dump(exclude_unset=partiel)
