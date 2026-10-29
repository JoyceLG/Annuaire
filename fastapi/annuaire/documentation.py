"""Fragments de documentation OpenAPI réutilisables.

Chaque fragment porte un modèle (`model`) en plus de son exemple : le schéma
publié dit alors la forme exacte du corps d'erreur, et un outil qui confronte
l'application à son schéma peut le vérifier.
"""

from typing import Any

from pydantic import BaseModel


class Erreur(BaseModel):
    """Erreur levée par une route et traduite par un gestionnaire."""

    erreur: str


class ErreurValidation(BaseModel):
    """Erreur de validation de Pydantic, telle que FastAPI la renvoie."""

    detail: list[dict[str, Any]]


class ErreurCorpsIllisible(BaseModel):
    """Corps qui ne peut même pas être décodé : FastAPI répond 400 avant toute validation."""

    detail: str


def reponse_404(exemple: str) -> dict:
    return {
        404: {
            "model": Erreur,
            "description": "La ressource demandée n'existe pas.",
            "content": {"application/json": {"example": {"erreur": exemple}}},
        }
    }


REPONSE_404_ASTRONAUTE = reponse_404("L'astronaute 42 n'existe pas")
REPONSE_404_MISSION = reponse_404("La mission 42 n'existe pas")

REPONSE_400 = {
    400: {
        "model": ErreurCorpsIllisible,
        "description": "Le corps de la requête n'est pas un texte UTF-8 lisible.",
        "content": {
            "application/json": {
                "example": {"detail": "There was an error parsing the body"}
            }
        },
    }
}

EXEMPLE_ERREUR_VALIDATION = {
    "detail": [
        {
            "type": "missing",
            "loc": ["body", "nom"],
            "msg": "Field required",
            "input": {},
        }
    ]
}

REPONSE_422 = {
    422: {
        "model": ErreurValidation,
        "description": "Les données soumises ne sont pas valides.",
        "content": {"application/json": {"example": EXEMPLE_ERREUR_VALIDATION}},
    }
}

# Le PATCH d'un astronaute vérifie la cohérence rôle / qualification dans la
# route, sur l'astronaute modifié : cette erreur-là a le format {"erreur": ...}.
REPONSE_422_AVEC_COHERENCE = {
    422: {
        "model": ErreurValidation | Erreur,
        "description": (
            "Les données soumises ne sont pas valides, ou la qualification "
            "n'est pas admise par le rôle de l'astronaute modifié."
        ),
        "content": {
            "application/json": {
                "examples": {
                    "validation": {
                        "summary": "Corps invalide",
                        "value": EXEMPLE_ERREUR_VALIDATION,
                    },
                    "coherence": {
                        "summary": "Qualification incohérente avec le rôle",
                        "value": {
                            "erreur": "un astronaute pilote doit avoir une "
                            "qualification parmi : pilote"
                        },
                    },
                }
            }
        },
    }
}

REPONSE_401 = {
    401: {
        "model": Erreur,
        "description": "Jeton absent ou invalide : en-tête `Authorization: Bearer <jeton>` requis.",
        "content": {"application/json": {"example": {"erreur": "Authentification requise"}}},
    }
}

# Une liste refuse ses paramètres de deux façons : Pydantic les valide
# (format {"detail": [...]}), puis la pagination compare la limite au maximum
# de la configuration (format {"erreur": ...}).
REPONSE_422_PAGINATION = {
    422: {
        "model": ErreurValidation | Erreur,
        "description": (
            "Les paramètres ne sont pas valides, ou la limite dépasse le "
            "maximum autorisé."
        ),
        "content": {
            "application/json": {
                "examples": {
                    "validation": {
                        "summary": "Paramètre invalide",
                        "value": {
                            "detail": [
                                {
                                    "type": "greater_than_equal",
                                    "loc": ["query", "limite"],
                                    "msg": "Input should be greater than or equal to 1",
                                    "input": "0",
                                    "ctx": {"ge": 1},
                                }
                            ]
                        },
                    },
                    "limite": {
                        "summary": "Limite au-delà du maximum",
                        "value": {"erreur": "la limite ne peut pas dépasser 100 (reçu : 101)"},
                    },
                }
            }
        },
    }
}
