"""Fixtures partagées par tous les fichiers de tests.

Aucune globale de module n'est réécrite : `creer_app` reçoit `ConfigTest` et,
en surcharge, la base de test donnée par `URL_BASE_TESTS`. Chaque test repart
de tables neuves, supprimées à la fin du test.
"""

import os
from pathlib import Path

import pytest
from flask import Flask
from sqlalchemy import select
from sqlalchemy.engine import make_url

from annuaire import creer_app
from annuaire.bdd import Connexion, est_en_memoire
from annuaire.config import ConfigTest
from annuaire.modeles import Astronaute, Base, Mission, Utilisateur
from annuaire.permissions import RoleUtilisateur

MOT_DE_PASSE = "motdepassetreslong"

# Les tests suppriment toutes les tables : seule une base dont le nom porte ce
# suffixe peut leur être confiée, jamais celle de l'API par une faute de frappe.
SUFFIXE_BASE_TESTS = "_tests"


@pytest.fixture(scope="session")
def url_base_tests() -> str:
    """L'URL de la base de test, vérifiée une fois pour toute la session."""

    texte = os.environ.get("URL_BASE_TESTS", "").strip()
    if not texte:
        pytest.exit(
            "URL_BASE_TESTS manquante : la renseigner dans .env (modèle : "
            ".env.exemple), par exemple sqlite:// pour une base en mémoire.",
            returncode=1,
        )
    url = make_url(texte)
    # Une base en mémoire disparaît avec le test : il n'y a rien à protéger.
    if est_en_memoire(url):
        return texte
    # `stem` retire l'extension : annuaire_tests (Postgres) comme annuaire_tests.db.
    nom = Path(url.database or "").stem
    if not nom.endswith(SUFFIXE_BASE_TESTS):
        pytest.exit(
            f"Base de test refusée : {url.database!r} ne se termine pas par "
            f"{SUFFIXE_BASE_TESTS!r}. Les tests en suppriment toutes les tables.",
            returncode=1,
        )
    return texte


def connexion_de(application: Flask) -> Connexion:
    """Le moteur et la fabrique de sessions, sans contexte applicatif ouvert.

    `annuaire.bdd.connexion()` passe par `current_app`. Les fixtures n'ouvrent
    pas de contexte : chaque requête du client de test ouvre alors le sien, et
    reçoit une session neuve, comme en production.
    """

    return application.extensions["bdd"]


@pytest.fixture
def app(url_base_tests):
    """Une application neuve, sur des tables neuves déjà peuplées."""

    application = creer_app(ConfigTest, URL_BASE=url_base_tests)
    bdd = connexion_de(application)

    # Suppression d'abord : une exécution interrompue a pu laisser des tables,
    # et des tables recréées repartent de l'identifiant 1.
    Base.metadata.drop_all(bdd.moteur)
    Base.metadata.create_all(bdd.moteur)

    with bdd.FabriqueSession() as session:
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

    Base.metadata.drop_all(bdd.moteur)
    # Rend les connexions du pool : sans cela, chaque test en laisserait
    # d'ouvertes jusqu'à la fin de la session.
    bdd.moteur.dispose()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def moteur(app):
    """Le moteur SQLAlchemy de l'application, pour espionner les requêtes SQL."""

    return connexion_de(app).moteur


@pytest.fixture
def session(app):
    """Une session directe sur la base du test, hors requête HTTP."""

    with connexion_de(app).FabriqueSession() as session:
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

        with connexion_de(app).FabriqueSession() as session:
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
