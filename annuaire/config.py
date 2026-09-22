"""Configuration de l'application.

Une classe par environnement. `creer_app` les lit avec `app.config.from_object`,
puis applique les surcharges passées en mots-clés — c'est ainsi que les tests
pointent vers une base temporaire sans toucher aux globales du paquet.
"""

import os
import secrets
from datetime import timedelta


class Config:
    """Réglages de l'application lancée normalement."""

    # Source unique de l'URL de base : `migrations/env.py` la lit ici aussi,
    # pour que l'application et Alembic ne puissent plus diverger.
    URL_BASE = os.environ.get("URL_BASE_DONNEES", "sqlite:///astronautes.db")
    ECHO_SQL = False

    # Lue à la création de l'application, et non à l'import du module : importer
    # `annuaire` sans la variable d'environnement ne doit pas lever d'erreur.
    CLE_SECRETE_JWT = os.environ.get("CLE_SECRETE_JWT")
    DUREE_JETON = timedelta(minutes=30)

    # Coût du hachage argon2 : les valeurs par défaut de la bibliothèque.
    ARGON2_TEMPS = 3
    ARGON2_MEMOIRE = 65536
    ARGON2_PARALLELISME = 4
    
    # Niveau de journalisation par défaut pour l'application Flask.
    NIVEAU_LOG = "DEBUG"


class ConfigTest(Config):
    """Réglages des tests : base jetable, clé éphémère, hachage au rabais."""

    URL_BASE = "sqlite://"
    CLE_SECRETE_JWT = secrets.token_urlsafe(32)

    # Paramètres minimaux : uniquement en test, jamais en production.
    ARGON2_TEMPS = 1
    ARGON2_MEMOIRE = 8
    ARGON2_PARALLELISME = 1
    
    # Niveau de journalisation pour les tests.
    NIVEAU_LOG = "WARNING"
