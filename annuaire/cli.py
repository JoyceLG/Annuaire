"""Commandes `flask` du projet."""

import click
from flask import Flask
from flask.cli import with_appcontext
from sqlalchemy import func, select

from .bdd import session_bdd
from .donnees import demonstration
from .donnees import utilisateurs as donnees_utilisateurs
from .modeles import Mission
from .permissions import RoleUtilisateur


def enregistrer_commandes(app: Flask) -> None:
    app.cli.add_command(promouvoir)
    app.cli.add_command(peupler)


@click.command("promouvoir")
@click.argument("email")
@click.argument("role", type=click.Choice([r.value for r in RoleUtilisateur]))
@with_appcontext
def promouvoir(email: str, role: str):
    """Change le rôle d'un utilisateur.

    Seul moyen de créer le premier admin : aucune route ne l'expose.
    """

    bdd = session_bdd()
    utilisateur = donnees_utilisateurs.trouver_par_email(bdd, email)
    if utilisateur is None:
        raise click.ClickException(f"Aucun utilisateur avec l'adresse {email}.")

    utilisateur.role = role
    bdd.commit()
    click.echo(f"{email} est désormais {role}.")


@click.command("peupler")
@with_appcontext
def peupler():
    """Insère le jeu de données Apollo de démonstration."""

    bdd = session_bdd()
    if bdd.scalar(select(func.count()).select_from(Mission)):
        raise click.ClickException("La base contient déjà des missions.")

    bdd.add_all(demonstration.construire())
    bdd.commit()
    click.echo(
        f"Base peuplée : {len(demonstration.MISSIONS)} missions, "
        f"{len(demonstration.ASTRONAUTES)} astronautes."
    )
