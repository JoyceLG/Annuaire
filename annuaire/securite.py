"""Hachage des mots de passe, jetons JWT, et les décorateurs d'accès.

Tout ce qui est réglable (clé, durée, coût du hachage) est lu dans
`current_app.config` au moment de l'appel, jamais à l'import du module.
"""

from datetime import UTC, datetime
from functools import wraps

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from flask import Flask, current_app, g, request
from sqlalchemy.orm import Session

from .bdd import session_bdd
from .donnees import utilisateurs as donnees_utilisateurs
from .erreurs import (
    IdentifiantsInvalides,
    JetonExpire,
    JetonInvalide,
    JetonManquant,
    PermissionRefusee,
)
from .modeles import Utilisateur
from .permissions import a_la_permission

# Mot de passe factice : son empreinte sert à consommer le même temps de calcul
# quand l'adresse n'existe pas, pour ne pas la trahir par un délai plus court.
_MOT_DE_PASSE_FACTICE = "mot-de-passe-qui-ne-sera-jamais-utilise"


# ======================= HACHAGE DES MOTS DE PASSE ========================


def initialiser_hachage(app: Flask) -> None:
    hacheur = PasswordHasher(
        time_cost=app.config["ARGON2_TEMPS"],
        memory_cost=app.config["ARGON2_MEMOIRE"],
        parallelism=app.config["ARGON2_PARALLELISME"],
    )
    app.extensions["hacheur"] = hacheur
    app.extensions["empreinte_factice"] = hacheur.hash(_MOT_DE_PASSE_FACTICE)


def hacher(mot_de_passe: str) -> str:
    return current_app.extensions["hacheur"].hash(mot_de_passe)


def verifier_identifiants(bdd: Session, email: str, mot_de_passe: str) -> Utilisateur:
    """Renvoie l'utilisateur, ou lève `IdentifiantsInvalides`.

    Même erreur et même délai que l'adresse existe ou non.
    """

    hacheur = current_app.extensions["hacheur"]
    utilisateur = donnees_utilisateurs.trouver_par_email(bdd, email)

    if utilisateur is None:
        try:
            hacheur.verify(current_app.extensions["empreinte_factice"], mot_de_passe)
        except VerifyMismatchError:
            pass
        raise IdentifiantsInvalides()

    try:
        hacheur.verify(utilisateur.empreinte, mot_de_passe)
    except VerifyMismatchError:
        raise IdentifiantsInvalides()
    return utilisateur


# ================================ JETONS ==================================


def creer_jeton(id_utilisateur: int) -> str:
    maintenant = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": str(id_utilisateur),
            "iat": maintenant,
            "exp": maintenant + current_app.config["DUREE_JETON"],
        },
        current_app.config["CLE_SECRETE_JWT"],
        algorithm="HS256",
    )


def lire_jeton(jeton: str) -> int:
    try:
        charge = jwt.decode(
            jeton, current_app.config["CLE_SECRETE_JWT"], algorithms=["HS256"]
        )
    except jwt.ExpiredSignatureError:
        raise JetonExpire()
    except jwt.InvalidTokenError:
        raise JetonInvalide()
    return int(charge["sub"])


def jeton_de_la_requete() -> str:
    entete = request.headers.get("Authorization", "")
    if not entete.startswith("Bearer "):
        raise JetonManquant()
    return entete.removeprefix("Bearer ")


# ============================== DÉCORATEURS ===============================


def _charger_utilisateur() -> Utilisateur:
    """Lit le jeton, charge l'utilisateur, et le range dans `g`."""

    id_utilisateur = lire_jeton(jeton_de_la_requete())
    g.utilisateur = donnees_utilisateurs.trouver(session_bdd(), id_utilisateur)
    return g.utilisateur


def authentification_requise(fonction):
    """Exige un jeton valide, sans exiger de permission particulière."""

    @wraps(fonction)
    def enveloppe(*args, **kwargs):
        _charger_utilisateur()
        return fonction(*args, **kwargs)

    # Marque lue par `refuser_par_defaut` : cette vue contrôle bien ses accès.
    enveloppe.protegee = True
    return enveloppe


def permission_requise(permission: str):
    """Exige un jeton valide *et* la permission donnée.

    Inutile de l'empiler avec `authentification_requise` : ce décorateur
    authentifie déjà, et empiler les deux décoderait le jeton deux fois.
    """

    def decorateur(fonction):
        @wraps(fonction)
        def enveloppe(*args, **kwargs):
            utilisateur = _charger_utilisateur()
            if not a_la_permission(utilisateur.role, permission):
                raise PermissionRefusee(permission)
            return fonction(*args, **kwargs)

        enveloppe.protegee = True
        return enveloppe

    return decorateur
