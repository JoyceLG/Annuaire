"""Données de démonstration pour l'annuaire des astronautes"""

ASTRONAUTES: dict[int, dict] = {
    1: {
        "id": 1,
        "nom": "Neil Armstrong",
        "role": "commandant",
        "nationalite": "Etats-Unis",
        "qualification": {
            "type": "pilote",
            "heures_vol": 100,
            "appareil": "F-16"
        }
    },
    2: {
        "id": 2,
        "nom": "Alan Bean",
        "role": "pilote",
        "nationalite": "Etats-Unis",
        "qualification": {
            "type": "pilote",
            "heures_vol": 200,
            "appareil": "F-16"
        }
    },
    3: {
        "id": 3,
        "nom": "Sophie Adenot",
        "role": "specialiste",
        "nationalite": "Française",
        "qualification": {
            "type": "scientifique",
            "discipline": "Ingénieure",
            "doctorat": False
        }
    },
}

# Insérées au démarrage si la base est vide (voir bdd.cycle_de_vie).
# Les identifiants sont explicites pour que les tests puissent viser
# /api/missions/1 ; la base attribue ensuite la suite (4, 5...).
MISSIONS_DEMONSTRATION: list[dict] = [
    {"id": 1, "nom": "Apollo 11", "annee": 1969},
    {"id": 2, "nom": "Apollo 12", "annee": 1969},
    {"id": 3, "nom": "Apollo 13", "annee": 1970},
]

EQUIPAGE_DEMONSTRATION: list[dict] = [
    {"nom": "Neil Armstrong", "mission_id": 1},
    {"nom": "Buzz Aldrin", "mission_id": 1},
    {"nom": "Alan Bean", "mission_id": 2},
]

id_astronaute_courant: int = max(ASTRONAUTES, default=0)


def demande_prochain_id_astronaute() -> int:
    """Retourne un identifiant d'astronaute jamais attribué."""
    global id_astronaute_courant
    id_astronaute_courant += 1
    return id_astronaute_courant
