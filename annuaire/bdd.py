"""Moteur SQLAlchemy et session liée à la requête.

Le moteur n'est plus une globale de module : il appartient à l'application,
rangé dans `app.extensions`. Deux applications peuvent donc coexister dans le
même processus — c'est ce qui permet aux tests de se passer de `monkeypatch`.
"""

from dataclasses import dataclass

from flask import Flask, current_app, g
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


@dataclass(frozen=True)
class Connexion:
    moteur: Engine
    FabriqueSession: sessionmaker


def initialiser(app: Flask) -> None:
    url = app.config["URL_BASE"]
    options = {}
    if url == "sqlite://":
        # Base en mémoire : sans pool statique, chaque session ouvrirait une
        # connexion neuve, donc une base vide. Utile aux tests uniquement.
        options = {"poolclass": StaticPool, "connect_args": {"check_same_thread": False}}

    moteur = create_engine(url, echo=app.config["ECHO_SQL"], **options)
    app.extensions["bdd"] = Connexion(moteur, sessionmaker(bind=moteur))
    app.teardown_appcontext(fermer_session)


def connexion() -> Connexion:
    """Le moteur et la fabrique de sessions de l'application courante."""

    return current_app.extensions["bdd"]


def session_bdd() -> Session:
    """La session de la requête en cours, créée à la demande."""

    if "bdd" not in g:
        g.bdd = connexion().FabriqueSession()
    return g.bdd


def fermer_session(exception=None) -> None:
    session = g.pop("bdd", None)
    if session is not None:
        session.close()
