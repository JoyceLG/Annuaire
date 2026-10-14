"""Données de démonstration pour l'annuaire des astronautes"""

ASTRONAUTES: dict[int, dict] = {
    1: {
        "id": 1,
        "nom": "Neil Armstrong",
        "role": "commandant",
        "nationalite": "Etats-Unis",
        "note_interne": "CONFIDENTIEL",
    },
    2: {
        "id": 2,
        "nom": "Alan Bean",
        "role": "pilote",
        "nationalite": "Etats-Unis",
        "note_interne": "CONFIDENTIEL",
    },
}

id_courant: int = 2


def demande_prochain_id() -> int:
    """Retourne le prochain identifiant pour un astronaute."""
    global id_courant
    id_courant += 1
    return id_courant
