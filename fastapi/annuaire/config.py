"""Configuration de l'application.

Une classe par environnement, choisie par la variable `ENVIRONNEMENT`
(`developpement`, `test` ou `production`) — voir `choisir_config`.
"""

import os

from sqlalchemy.pool import StaticPool


class Config:
    """Réglages communs. Les classes filles ne font que les ajuster.

    La documentation interactive (`/docs`, `/redoc`, `/openapi.json`) est
    fermée dans cette classe de base : chaque environnement choisit de
    l'exposer. Attention, sans `ENVIRONNEMENT`, c'est le développement qui
    est choisi (voir `choisir_config`) : la documentation est alors ouverte.
    En production, `ENVIRONNEMENT=production` doit donc être exporté.
    """

    DOCUMENTATION_PUBLIQUE = False
    LIMITE_PAGINATION_DEFAUT = 20
    LIMITE_PAGINATION_MAX = 100

    # --- Base de données -----------------------------------------------
    # Adresse de connexion, au format dialecte+pilote://... Le pilote doit
    # être asynchrone (aiosqlite, asyncpg) : SQLAlchemy refuse un pilote
    # synchrone avec create_async_engine.
    URL_BASE: str = os.environ.get("URL_BASE", "")
    # Affiche chaque requête SQL générée. Utile pour voir selectinload
    # travailler ; à proscrire en production (volume, valeurs sensibles).
    ECHO_SQL = False
    # Options passées telles quelles à create_async_engine. Chaque
    # environnement fournit les siennes : le code du moteur ne connaît
    # ainsi aucun dialecte particulier.
    OPTIONS_MOTEUR: dict = {}
    # Crée les tables au démarrage. PROVISOIRE : en production, le schéma
    # appartient à Alembic, et les deux ne doivent jamais coexister
    # (bug de la session 12, « duplicate column »).
    CREER_SCHEMA = False
    # Insère le jeu de démonstration si la base est vide.
    DONNEES_DEMONSTRATION = False


class ConfigDeveloppement(Config):
    """Développement : documentation ouverte, base SQLite locale."""

    DOCUMENTATION_PUBLIQUE = True
    # Un fichier SQLite par défaut : l'application démarre sans conteneur.
    # Pour PostgreSQL, exporter URL_BASE=postgresql+asyncpg://...
    URL_BASE = os.environ.get("URL_BASE", "sqlite+aiosqlite:///./annuaire_dev.db")
    ECHO_SQL = True
    CREER_SCHEMA = True
    DONNEES_DEMONSTRATION = True


class ConfigTest(Config):
    """Tests : documentation ouverte, base SQLite en mémoire.

    URL_BASE ignore volontairement l'environnement : un test ne doit jamais
    pouvoir viser une vraie base par accident (leçon de la session 20).
    """

    DOCUMENTATION_PUBLIQUE = True
    URL_BASE = "sqlite+aiosqlite:///:memory:"
    # SQLite en mémoire crée une base PAR CONNEXION. Le pool en ouvrant
    # plusieurs, une route lirait une base vide pendant que le démarrage
    # remplissait une autre. StaticPool force une connexion unique.
    OPTIONS_MOTEUR = {
        "poolclass": StaticPool,
        "connect_args": {"check_same_thread": False},
    }
    CREER_SCHEMA = True
    DONNEES_DEMONSTRATION = True


class ConfigProduction(Config):
    """Production : documentation fermée, le schéma de l'API n'est pas publié.

    URL_BASE vient uniquement de l'environnement, sans valeur par défaut : elle
    contient un mot de passe (leçon de la session 19). Son absence est
    détectée au démarrage, voir bdd.cycle_de_vie.
    """

    DOCUMENTATION_PUBLIQUE = False


# Le nom lisible d'un environnement vers sa classe. Seul endroit à compléter
# si un quatrième environnement apparaît (recette, démo...).
CONFIGS: dict[str, type[Config]] = {
    "developpement": ConfigDeveloppement,
    "test": ConfigTest,
    "production": ConfigProduction,
}

ENVIRONNEMENT_PAR_DEFAUT = "developpement"


def choisir_config(nom: str | None = None) -> type[Config]:
    """La classe de configuration correspondant à `nom`, sinon à `ENVIRONNEMENT`.

    Un nom inconnu est une erreur immédiate : mieux vaut refuser de démarrer
    que lancer la production avec les réglages de développement à cause
    d'une faute de frappe.
    """

    nom = (nom or os.environ.get("ENVIRONNEMENT") or ENVIRONNEMENT_PAR_DEFAUT).strip().lower()
    if nom not in CONFIGS:
        connus = ", ".join(sorted(CONFIGS))
        raise RuntimeError(f"Environnement inconnu : {nom!r} (attendu : {connus})")
    return CONFIGS[nom]
