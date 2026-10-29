"""Dépendances injectables, communes aux routes.

Ce module importe FastAPI : il appartient à la couche web, au même titre
que `routes/`. Rien ici ne doit remonter dans `donnees/`.
"""

import logging
from typing import Annotated

from fastapi import Cookie, Depends, Header, Query, Request
from pydantic import BaseModel

from annuaire.config import Config
from annuaire.donnees.demonstration import ASTRONAUTES
from annuaire.erreurs import AuthentificationRequise, LimiteTropGrande

logger = logging.getLogger(__name__)

class Pagination(BaseModel):
    limite: int
    decalage: int


def configuration(request: Request) -> type[Config]:
    """Injecte la classe de configuration de l'application.

    C'est celle que `creer_app` a reçue ou choisie, rangée dans
    `app.state` : relire `ENVIRONNEMENT` ici ignorerait une classe passée
    directement à `creer_app`.
    """
    return request.app.state.config


def pagination(
    config: Annotated[type[Config], Depends(configuration)],
    limite: Annotated[
        int | None,
        Query(ge=1, description="Nombre maximum de résultats (défaut et maximum fixés par la configuration)"),
    ] = None,
    decalage: Annotated[int, Query(ge=0, description="Nombre de résultats à sauter")] = 0,
) -> Pagination:
    """Paramètres de pagination, communs à toutes les listes."""
    if limite is None:
        limite = config.LIMITE_PAGINATION_DEFAUT
    if limite > config.LIMITE_PAGINATION_MAX:
        raise LimiteTropGrande(limite, config.LIMITE_PAGINATION_MAX)
    return Pagination(limite=limite, decalage=decalage)


def depot_astronautes():
    """Ouvre un accès aux données pour la durée de la requête.

    Le `finally` s'exécute même si la route lève une exception : c'est ce
    qui garantit qu'aucune ressource ne fuit.
    """
    logger.debug("ouverture de l'accès aux données")
    try:
        yield ASTRONAUTES
    finally:
        logger.debug("fermeture de l'accès aux données")


def authentification_requise(
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    """Contrôle provisoire : exige un en-tête `Authorization: Bearer <jeton>`.

    L'objectif est de poser le mécanisme, pas la cryptographie : le jeton
    n'est pas vérifié, il doit seulement être présent (`jeton_valide`).
    """
    if not jeton_valide(jeton_de_l_en_tete(authorization)):
        raise AuthentificationRequise()


# Le cookie posé par la connexion à la documentation (routes/documentation.py).
NOM_COOKIE_DOCUMENTATION = "jeton_documentation"


def jeton_valide(jeton: str | None) -> bool:
    """Seul endroit qui juge un jeton, qu'il vienne d'un en-tête ou d'un cookie.

    Contrôle provisoire : un jeton non vide suffit.
    """
    return bool(jeton and jeton.strip())


def jeton_de_l_en_tete(authorization: str | None) -> str | None:
    """Le jeton d'un en-tête `Authorization: Bearer <jeton>`, sinon None."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    return authorization.removeprefix("Bearer ")


def documentation_autorisee(
    authorization: Annotated[str | None, Header()] = None,
    jeton_documentation: Annotated[str | None, Cookie()] = None,
) -> bool:
    """Dit si la requête peut lire la documentation, sans jamais refuser.

    Ne pas refuser est son usage propre : `/docs` et `/redoc` l'injectent
    pour afficher le formulaire de connexion à qui n'est pas connecté, ce
    qu'une dépendance qui lève un 401 ne leur permettrait pas.
    `documentation_requise` en fait un refus, pour `/openapi.json`.

    Swagger UI charge `/openapi.json` par une requête séparée, partie du
    navigateur : elle ne porte pas d'en-tête Authorization, seulement les
    cookies du site. D'où le cookie, accepté ici en plus de l'en-tête.

    Les routes de l'API, elles, n'acceptent que l'en-tête : un cookie part
    avec toute requête vers le site, même déclenchée par une page tierce, et
    les ouvrirait aux attaques CSRF.
    """
    return jeton_valide(jeton_de_l_en_tete(authorization)) or jeton_valide(
        jeton_documentation
    )


def documentation_requise(
    autorisee: Annotated[bool, Depends(documentation_autorisee)],
) -> None:
    """Refuse la requête (401) si `documentation_autorisee` ne l'accepte pas."""
    if not autorisee:
        raise AuthentificationRequise()


# Forme réutilisable : on écrit `page: PaginationInjectee` dans les routes.
PaginationInjectee = Annotated[Pagination, Depends(pagination)]

# Forme réutilisable : on écrit `depot_astronautes: DepotAstronautesInjecte` dans les routes.
DepotAstronautesInjecte = Annotated[dict, Depends(depot_astronautes)]
