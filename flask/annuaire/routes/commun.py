"""Outils partagés par les blueprints : lecture du corps et garde-fou d'accès."""

import uuid
import time

from flask import current_app, request, g
from pydantic import BaseModel, ValidationError

from .. import schemas
from ..erreurs import DonneesInvalides, PermissionRefusee

# Préfixe commun aux blueprints. Lu à l'import du module, donc hors de portée de
# `app.config` : c'est le contrat d'URL de l'API, pas un réglage de déploiement.
PREFIXE_API = "/api"

# En-tête de corrélation, lu en entrée et réémis en sortie.
EN_TETE_REQUETE_ID = "X-Request-ID"


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
    raise PermissionRefusee(permission="accès", utilisateur="inconnu", chemin=f"{request.endpoint} non déclarée")


def demarrer_requete():
    """Initialise les informations de suivi pour la requête en cours."""
    
    recu = request.headers.get(EN_TETE_REQUETE_ID)
    g.requete_id = recu or uuid.uuid4().hex[: current_app.config["LONGUEUR_REQUETE_ID"]]
    g.debut = time.perf_counter()


def terminer_requete(reponse):
    """Ajoute l'ID de requête aux en-têtes de la réponse HTTP."""
    
    reponse.headers[EN_TETE_REQUETE_ID] = g.get("requete_id", "-")
    return reponse

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
