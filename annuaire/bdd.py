"""Moteur SQLAlchemy et session liée à la requête.

Le moteur n'est plus une globale de module : il appartient à l'application,
rangé dans `app.extensions`. Deux applications peuvent donc coexister dans le
même processus — c'est ce qui permet aux tests de se passer de `monkeypatch`.
"""

from dataclasses import dataclass

from flask import Flask, current_app, g
from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


@dataclass(frozen=True)
class Connexion:
    moteur: Engine
    FabriqueSession: sessionmaker


def est_en_memoire(url: URL) -> bool:
    """La base vit-elle uniquement en RAM ?

    Comparer la chaîne à "sqlite://" raterait les autres écritures de la même
    base : "sqlite:///:memory:" et "sqlite://:memory:".
    """

    return url.get_backend_name() == "sqlite" and url.database in (None, "", ":memory:")


def options_moteur(app: Flask, url: URL) -> dict:
    """Les options de connexion adaptées à la base visée."""

    if est_en_memoire(url):
        # Sans pool statique, chaque session ouvrirait une connexion neuve,
        # donc une base vide. Utile aux tests uniquement.
        return {"poolclass": StaticPool, "connect_args": {"check_same_thread": False}}

    if url.get_backend_name() == "sqlite":
        # SQLite sur fichier ignore le dimensionnement d'un pool réseau.
        return {}

    return {
        "pool_size": app.config["POOL_TAILLE"],
        "max_overflow": app.config["POOL_DEBORDEMENT"],
        "pool_recycle": app.config["POOL_RECYCLAGE"],
        "pool_timeout": app.config["POOL_TIMEOUT"],
        # Écarte les connexions coupées par le serveur pendant une inactivité.
        "pool_pre_ping": True,
    }


def initialiser(app: Flask) -> None:
    url = make_url(app.config["URL_BASE"])
    moteur = create_engine(
        url, echo=app.config["ECHO_SQL"], **options_moteur(app, url)
    )
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
