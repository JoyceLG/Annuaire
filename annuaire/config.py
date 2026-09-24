"""Configuration de l'application.

Une classe par environnement, choisie par la variable `ENVIRONNEMENT`
(`developpement`, `test` ou `production`) — voir `choisir_config`.

Les classes ne contiennent que des valeurs par défaut : les variables
d'environnement sont lues par `resoudre()`, à la création de l'application et
non à l'import du module. Importer `annuaire` sans `.env` ne lève donc rien,
et un test peut modifier l'environnement avant d'appeler `creer_app`.

Priorité, du plus faible au plus fort :
    attribut de classe  <  variable d'environnement  <  surcharge `creer_app`
"""

import os
import secrets

from datetime import timedelta
from typing import Any, Callable, Mapping

from dotenv import load_dotenv



def charger_dotenv() -> None:
    """Charge `.env`, sauf si `ENVIRONNEMENT=production` est exporté.

    En production, les variables viennent de l'environnement réel : un `.env`
    oublié sur la machine ne doit pas compléter en silence ce qui manque.
    La commande `flask` lit `.env` d'elle-même, avant ce module : en production,
    exporter aussi `FLASK_SKIP_DOTENV=1`.
    """

    if os.environ.get("ENVIRONNEMENT", "").strip().lower() == "production":
        return
    load_dotenv()


charger_dotenv()


# ========================= LECTURE DE L'ENVIRONNEMENT =========================


def en_texte(valeur: str) -> str:
    return valeur.strip()


def en_bool(valeur: str) -> bool:
    return valeur.strip().lower() in {"1", "true", "oui", "yes", "on"}


def en_minutes(valeur: str) -> timedelta:
    return timedelta(minutes=int(valeur))


# Réglage de l'application -> (nom de la variable d'environnement, conversion).
# Tout ce qui doit pouvoir changer sans toucher au code figure ici, et nulle
# part ailleurs : c'est la liste complète de ce qu'un déploiement peut régler.
VARIABLES_ENVIRONNEMENT: dict[str, tuple[str, Callable[[str], Any]]] = {
    "URL_BASE": ("URL_BASE_DE_DONNEES", en_texte),
    "ECHO_SQL": ("ECHO_SQL", en_bool),
    "CLE_SECRETE_JWT": ("CLE_SECRETE_JWT", en_texte),
    "DUREE_JETON": ("DUREE_JETON_MINUTES", en_minutes),
    "ALGORITHME_JWT": ("ALGORITHME_JWT", en_texte),
    "FAIRE_CONFIANCE_PROXY": ("FAIRE_CONFIANCE_PROXY", en_bool),
    "ARGON2_TEMPS": ("ARGON2_TEMPS", int),
    "ARGON2_MEMOIRE": ("ARGON2_MEMOIRE", int),
    "ARGON2_PARALLELISME": ("ARGON2_PARALLELISME", int),
    "NIVEAU_LOG": ("NIVEAU_LOG", en_texte),
    "NIVEAU_LOG_WERKZEUG": ("NIVEAU_LOG_WERKZEUG", en_texte),
    "FORMAT_LOG": ("FORMAT_LOG", en_texte),
    "FICHIER_LOG": ("FICHIER_LOG", en_texte),
    "POOL_TAILLE": ("POOL_TAILLE", int),
    "POOL_DEBORDEMENT": ("POOL_DEBORDEMENT", int),
    "POOL_RECYCLAGE": ("POOL_RECYCLAGE_SECONDES", int),
    "POOL_TIMEOUT": ("POOL_TIMEOUT_SECONDES", int),
}


class Config:
    """Réglages communs. Les classes filles ne font que les ajuster."""

    # --- Base de données -----------------------------------------------------
    # Aucune base par défaut : le code ne connaît aucune technologie de base,
    # elle vient tout entière de l'URL (`URL_BASE_DE_DONNEES`). Changer de base
    # revient à changer cette URL et à installer le pilote correspondant.
    URL_BASE = None
    ECHO_SQL = False

    # Pool de connexions : ignoré par les bases sans serveur (SQLite).
    POOL_TAILLE = 5
    POOL_DEBORDEMENT = 10
    POOL_RECYCLAGE = 1800
    POOL_TIMEOUT = 30

    # --- Authentification ----------------------------------------------------
    # Aucune valeur par défaut : une clé de repli en dur serait une clé connue
    # de tous. `valider` refuse de démarrer si l'environnement ne la fournit pas.
    CLE_SECRETE_JWT = None
    DUREE_JETON = timedelta(minutes=30)
    ALGORITHME_JWT = "HS256"

    # Coût du hachage argon2 : les valeurs par défaut de la bibliothèque.
    ARGON2_TEMPS = 3
    ARGON2_MEMOIRE = 65536
    ARGON2_PARALLELISME = 4

    # Ne faire confiance à `X-Forwarded-For` que derrière un reverse proxy qui
    # le réécrit : sans cela, n'importe quel client choisit l'IP qu'on journalise.
    FAIRE_CONFIANCE_PROXY = False

    # --- Journalisation ------------------------------------------------------
    NIVEAU_LOG = "INFO"
    NIVEAU_LOG_WERKZEUG = "WARNING"
    FORMAT_LOG = "json"
    FORMAT_HORODATAGE = "%Y-%m-%dT%H:%M:%S"
    FICHIER_LOG = None
    TAILLE_MAX_LOG = 5 * 1024 * 1024
    NOMBRE_FICHIERS_LOG = 3

    # --- Traçage des requêtes ------------------------------------------------
    LONGUEUR_REQUETE_ID = 12
    LONGUEUR_JETON_JOURNAL = 8

    # Réglages sans lesquels l'application ne peut pas fonctionner. En minuscule
    # pour que `resoudre` ne le confonde pas avec un réglage de l'application.
    requis: tuple[str, ...] = ("CLE_SECRETE_JWT", "URL_BASE")

    @classmethod
    def depuis_environnement(cls) -> dict[str, Any]:
        """Les réglages effectivement présents dans l'environnement."""

        reglages: dict[str, Any] = {}
        for cle, (variable, convertir) in VARIABLES_ENVIRONNEMENT.items():
            brute = os.environ.get(variable)
            if brute is None or not brute.strip():
                continue
            try:
                reglages[cle] = convertir(brute)
            except ValueError as erreur:
                raise RuntimeError(
                    f"Variable d'environnement {variable} illisible : {brute!r} ({erreur})"
                ) from erreur
        return reglages

    @classmethod
    def resoudre(cls, **surcharges) -> dict[str, Any]:
        """Les réglages effectifs : classe, puis environnement, puis surcharges."""

        reglages = {
            nom: getattr(cls, nom)
            for nom in dir(cls)
            if nom[:1].isalpha() and nom.isupper()
        }
        reglages.update(cls.depuis_environnement())
        reglages.update(surcharges)
        return reglages

    @classmethod
    def valider(cls, reglages: Mapping[str, Any]) -> None:
        """Vérifie les réglages effectifs — surcharges comprises."""

        manquants = [nom for nom in cls.requis if not reglages.get(nom)]
        if manquants:
            variables = ", ".join(
                VARIABLES_ENVIRONNEMENT.get(nom, (nom,))[0] for nom in manquants
            )
            raise RuntimeError(f"Réglages manquants : {variables}")


class ConfigDeveloppement(Config):
    """Développement : débogage activé, journal lisible à l'œil."""

    DEBUG = True

    NIVEAU_LOG = "DEBUG"
    # Sans cela, `NIVEAU_LOG=DEBUG` ne montrerait quand même aucune requête HTTP.
    NIVEAU_LOG_WERKZEUG = "INFO"
    # Du JSON sur une seule ligne n'a d'intérêt que pour un collecteur de logs.
    FORMAT_LOG = "texte"


class ConfigTest(Config):
    """Tests : clé éphémère, hachage au rabais.

    La base est fournie par `tests/conftest.py` (variable `URL_BASE_TESTS`),
    en surcharge de `creer_app` : cette classe ne lit pas l'environnement.
    """

    # Tirée au hasard, et jamais celle du développeur : les tests passent sur une
    # machine sans `.env`, et un jeton fabriqué ici ne vaut rien ailleurs.
    CLE_SECRETE_JWT = secrets.token_urlsafe(32)

    # Paramètres minimaux : uniquement en test, jamais en production.
    ARGON2_TEMPS = 1
    ARGON2_MEMOIRE = 8
    ARGON2_PARALLELISME = 1

    NIVEAU_LOG = "WARNING"
    FORMAT_LOG = "texte"
    TESTING = True

    @classmethod
    def depuis_environnement(cls) -> dict[str, Any]:
        """Aucune : un test ne doit pas dépendre du `.env` de la machine.

        Sans cette coupure, `NIVEAU_LOG=DEBUG` dans un `.env` local changerait
        le résultat des tests, et la vraie clé de signature servirait à les
        faire passer.
        """

        return {}


class ConfigProduction(Config):
    """Production : débogage interdit, journal restreint."""

    TESTING = False
    DEBUG = False

    NIVEAU_LOG = "WARNING"

    @classmethod
    def valider(cls, reglages: Mapping[str, Any]) -> None:
        super().valider(reglages)
        if reglages.get("DEBUG"):
            raise RuntimeError(
                "DEBUG est actif en production : la console de débogage Werkzeug "
                "exposerait un interpréteur Python à distance."
            )


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
