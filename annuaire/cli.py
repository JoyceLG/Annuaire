"""Commandes `flask` du projet."""

import click
from flask import Flask
from flask.cli import with_appcontext
from sqlalchemy import func, select

from .bdd import session_bdd
from .donnees import utilisateurs as donnees_utilisateurs
from .modeles import Astronaute, Mission
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

    apollo_11 = Mission(nom="Apollo 11", programme="Apollo", annee=1969)
    apollo_12 = Mission(nom="Apollo 12", programme="Apollo", annee=1969)
    apollo_14 = Mission(nom="Apollo 14", programme="Apollo", annee=1971)

    # Les astronautes sont rattachés par la relation : SQLAlchemy ordonne les
    # INSERT et renseigne mission_id, sans qu'on ait à deviner les identifiants.
    bdd.add_all(
        [
            apollo_11,
            apollo_12,
            apollo_14,
            Astronaute(nom="Neil Armstrong", role="commandant",
                       nationalite="Etats-Unis", mission=apollo_11),
            Astronaute(nom="Alan Bean", role="pilote",
                       nationalite="Etats-Unis", mission=apollo_12),
            Astronaute(nom="Peter Conrad", role="commandant",
                       nationalite="Etats-Unis", mission=apollo_12),
            Astronaute(nom="Edgar Mitchell", role="pilote",
                       nationalite="Etats-Unis", mission=apollo_14),
            Astronaute(nom="Alan Shepard", role="commandant",
                       nationalite="Etats-Unis", mission=apollo_14),
        ]
    )
    bdd.commit()
    click.echo("Base peuplée : 3 missions, 5 astronautes.")
