"""Accès à la base : moteur, fabrique de sessions, cycle de vie.

Ce module importe FastAPI (pour `Request`) : il appartient à la couche web.
Les fonctions de `donnees/` reçoivent la session en paramètre et ignorent
tout de FastAPI.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from annuaire.donnees.demonstration import MISSIONS_DEMONSTRATION
from annuaire.modeles import Base, Mission

logger = logging.getLogger(__name__)


@asynccontextmanager
async def cycle_de_vie(app: FastAPI):
    """Ouvre les ressources durables au démarrage, les ferme à l'arrêt.

    Tout ce qui précède le `yield` s'exécute avant la première requête ;
    tout ce qui suit, après la dernière. C'est le scope `lifespan` d'ASGI
    (session 22) : le point d'accroche qui manquait à Flask.
    """
    config = app.state.config

    # Fail fast (session 19) : sans adresse, refuser de démarrer plutôt que
    # d'échouer à la première requête, peut-être des heures plus tard.
    if not config.URL_BASE:
        raise RuntimeError("URL_BASE n'est pas configurée")

    # Un seul moteur par application : il porte le pool de connexions.
    moteur = create_async_engine(config.URL_BASE, echo=config.ECHO_SQL, **config.OPTIONS_MOTEUR)

    if config.CREER_SCHEMA:
        async with moteur.begin() as connexion:
            # create_all est synchrone : run_sync l'exécute à travers le
            # pont greenlet. PROVISOIRE, voir Config.CREER_SCHEMA.
            await connexion.run_sync(Base.metadata.create_all)

    # expire_on_commit=False : par défaut, SQLAlchemy marque les objets
    # comme périmés après un commit, et le premier accès à un attribut les
    # recharge. En asynchrone, ce rechargement implicite est impossible (un
    # accès d'attribut ne peut pas être awaité) et lèverait une erreur. La
    # session mourant avec la requête, le risque de donnée périmée est nul.
    fabrique = async_sessionmaker(moteur, expire_on_commit=False)

    if config.DONNEES_DEMONSTRATION:
        await _peupler_si_vide(fabrique)

    app.state.fabrique = fabrique
    logger.info("base de données prête")
    try:
        yield
    finally:
        # Rend les connexions du pool. Sans cela, l'arrêt de l'application
        # laisserait des connexions ouvertes côté PostgreSQL.
        await moteur.dispose()
        logger.info("connexions à la base fermées")


async def _peupler_si_vide(fabrique: async_sessionmaker[AsyncSession]) -> None:
    """Insère le jeu de démonstration, uniquement dans une table vide."""
    async with fabrique() as session:
        nombre = await session.scalar(select(func.count()).select_from(Mission))
        if nombre:
            return
        session.add_all(Mission(**valeurs) for valeurs in MISSIONS_DEMONSTRATION)
        await session.commit()


async def session_bdd(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Une session par requête, fermée quoi qu'il arrive.

    Dépendance à `yield` (session 26) : le `async with` garantit la
    fermeture, y compris quand la route lève une exception.
    """
    async with request.app.state.fabrique() as session:
        yield session


# Forme réutilisable : on écrit `bdd: SessionBdd` dans les routes.
SessionBdd = Annotated[AsyncSession, Depends(session_bdd)]
