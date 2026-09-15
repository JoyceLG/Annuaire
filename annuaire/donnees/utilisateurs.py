"""Accès aux données pour les utilisateurs."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..erreurs import EmailDejaUtilise, UtilisateurIntrouvable
from ..modeles import Utilisateur


def trouver(bdd: Session, id_utilisateur: int) -> Utilisateur:
    utilisateur = bdd.get(Utilisateur, id_utilisateur)
    if utilisateur is None:
        raise UtilisateurIntrouvable(id_utilisateur)
    return utilisateur


def trouver_par_email(bdd: Session, email: str) -> Utilisateur | None:
    """Renvoie None plutôt que de lever : l'appelant décide quoi en faire.

    La connexion, elle, ne doit pas révéler si l'adresse existe.
    """

    return bdd.scalar(select(Utilisateur).where(Utilisateur.email == email))


def creer(bdd: Session, email: str, empreinte: str) -> Utilisateur:
    """Enregistre un utilisateur à partir d'une empreinte déjà calculée."""

    if trouver_par_email(bdd, email) is not None:
        raise EmailDejaUtilise(email)

    utilisateur = Utilisateur(email=email, empreinte=empreinte)
    try:
        # Transaction imbriquée : en cas de collision entre la vérification
        # ci-dessus et l'INSERT, seul cet ajout est annulé.
        with bdd.begin_nested():
            bdd.add(utilisateur)
    except IntegrityError:
        raise EmailDejaUtilise(email)
    return utilisateur
