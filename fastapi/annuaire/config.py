"""Configuration de l'application.

Une classe par environnement, choisie par la variable `ENVIRONNEMENT`
(`developpement`, `test` ou `production`) — voir `choisir_config`.
"""

import os


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


class ConfigDeveloppement(Config):
    """Développement : documentation interactive ouverte."""

    DOCUMENTATION_PUBLIQUE = True


class ConfigTest(Config):
    """Tests : documentation ouverte, comme en développement."""

    DOCUMENTATION_PUBLIQUE = True


class ConfigProduction(Config):
    """Production : documentation fermée, le schéma de l'API n'est pas publié."""

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
