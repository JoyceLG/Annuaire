"""Fixtures partagées par tous les fichiers de tests.

Aucune globale de module n'est réécrite : `creer_app` reçoit `ConfigTest` et
une base SQLite en mémoire, jetable à la fin de chaque test.
"""

import pytest
from sqlalchemy import select

from annuaire import creer_app
from annuaire.bdd import connexion
from annuaire.config import ConfigTest
from annuaire.modeles import Astronaute, Base, Mission, Utilisateur
from annuaire.permissions import RoleUtilisateur

MOT_DE_PASSE = "motdepassetreslong"


@pytest.fixture
def app():
    """Une application neuve, sur une base en mémoire déjà peuplée."""

    application = creer_app(ConfigTest)

    with application.app_context():
        moteur = connexion().moteur
        Base.metadata.create_all(moteur)

        with connexion().FabriqueSession() as session:
            apollo_11 = Mission(nom="Apollo 11", programme="Apollo", annee=1969)
            apollo_12 = Mission(nom="Apollo 12", programme="Apollo", annee=1969)
            apollo_17 = Mission(nom="Apollo 17", programme="Apollo", annee=1972)
            session.add_all([
                apollo_11,
                apollo_12,
                apollo_17,
                Astronaute(nom="Neil Armstrong", role="commandant",
                           nationalite="Etats-Unis", mission=apollo_11),
                Astronaute(nom="Alan Bean", role="pilote",
                           nationalite="Etats-Unis", mission=apollo_12),
                Astronaute(nom="Peter Conrad", role="commandant",
                           nationalite="Etats-Unis", mission=apollo_12),
            ])
            session.commit()

        yield application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def moteur(app):
    """Le moteur SQLAlchemy de l'application, pour espionner les requêtes SQL."""

    return connexion().moteur


@pytest.fixture
def session(app):
    """Une session directe sur la base du test, hors requête HTTP."""

    with connexion().FabriqueSession() as session:
        yield session


@pytest.fixture
def creer_utilisateur(app, client):
    """Fabrique d'utilisateurs : inscription, rôle éventuel, puis connexion.

    Renvoie les en-têtes d'authentification prêts à l'emploi.
    """

    def _creer(email: str, role: RoleUtilisateur = RoleUtilisateur.LECTEUR) -> dict:
        client.post(
            "/api/inscription",
            json={"email": email, "mot_de_passe": MOT_DE_PASSE},
        )
        if role is not RoleUtilisateur.LECTEUR:
            promouvoir(email, role)

        reponse = client.post(
            "/api/connexion",
            json={"email": email, "mot_de_passe": MOT_DE_PASSE},
        )
        return {"Authorization": f"Bearer {reponse.get_json()['jeton']}"}

    def promouvoir(email: str, role: RoleUtilisateur) -> None:
        """Équivalent test de `flask promouvoir` : aucune route n'expose le rôle,
        et il faut bien un premier admin."""

        with connexion().FabriqueSession() as session:
            utilisateur = session.scalar(
                select(Utilisateur).where(Utilisateur.email == email)
            )
            assert utilisateur is not None, f"utilisateur {email} introuvable"
            utilisateur.role = role
            session.commit()

    return _creer


@pytest.fixture
def entetes_lecteur(creer_utilisateur):
    return creer_utilisateur("lecteur@x.fr", RoleUtilisateur.LECTEUR)


@pytest.fixture
def entetes_editeur(creer_utilisateur):
    return creer_utilisateur("editeur@x.fr", RoleUtilisateur.EDITEUR)


@pytest.fixture
def entetes_admin(creer_utilisateur):
    return creer_utilisateur("admin@x.fr", RoleUtilisateur.ADMIN)


@pytest.fixture
def entetes_auth(creer_utilisateur):
    """Utilisateur « à tout faire » des tests CRUD : admin, car ils suppriment aussi."""

    return creer_utilisateur("test@x.fr", RoleUtilisateur.ADMIN)
