"""Routes pour la gestion des utilisateurs."""

import logging

from datetime import UTC, datetime

from flask import Blueprint, g

from .. import schemas, securite
from ..bdd import session_bdd
from ..donnees import utilisateurs as donnees_utilisateurs
from ..erreurs import PermissionRefusee
from ..modeles import Utilisateur
from ..permissions import a_la_permission
from ..securite import authentification_requise
from .commun import PREFIXE_API, lire_corps, publique

bp = Blueprint("utilisateurs", __name__, url_prefix=PREFIXE_API)
logger = logging.getLogger(__name__)


@bp.post("/inscription")
@publique
def inscrire():
    """Crée un compte. Le rôle n'est pas choisi ici : tout inscrit est lecteur."""

    champs = lire_corps(schemas.InscriptionEntree)

    bdd = session_bdd()
    utilisateur = donnees_utilisateurs.creer(
        bdd, champs["email"], securite.hacher(champs["mot_de_passe"])
    )
    bdd.commit()
    return utilisateur.en_dict(), 201


@bp.post("/connexion")
@publique
def connecter():
    champs = lire_corps(schemas.ConnexionEntree)

    bdd = session_bdd()
    utilisateur = securite.verifier_identifiants(
        bdd, champs["email"], champs["mot_de_passe"]
    )

    resume = utilisateur.en_dict()
    jeton = securite.creer_jeton(utilisateur.id)

    utilisateur.derniere_connexion = datetime.now(UTC)
    bdd.commit()

    logger.info(f"Utilisateur {utilisateur.id} connecté à {utilisateur.derniere_connexion}")
    
    return {"jeton": jeton, "utilisateur": resume}, 200


@bp.get("/moi")
@authentification_requise
def lire_courant():
    utilisateur: Utilisateur = g.utilisateur
    return utilisateur.en_dict(), 200


@bp.patch("/utilisateurs/<int(min=1):id_utilisateur>")
@authentification_requise
def modifier(id_utilisateur: int):
    """Modifie l'adresse d'un utilisateur : la sienne, ou celle d'autrui si admin."""

    if g.utilisateur.id != id_utilisateur and not a_la_permission(
        g.utilisateur.role, "administrer"
    ):
        raise PermissionRefusee(permission="modifier autrui", utilisateur=g.utilisateur.email, chemin=f"/utilisateurs/{id_utilisateur}")

    champs = lire_corps(schemas.UtilisateurPatch, partiel=True)

    bdd = session_bdd()
    utilisateur = donnees_utilisateurs.trouver(bdd, id_utilisateur)

    for cle, valeur in champs.items():
        setattr(utilisateur, cle, valeur)

    bdd.commit()
    return utilisateur.en_dict(), 200
