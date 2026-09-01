from erreurs import AstronauteIntrouvable

ASTRONAUTES = [
    {"id": 1, "nom": "Neil Armstrong", "role": "commandant", "mission": "Apollo 11"},
    {"id": 2, "nom": "Alan Bean", "role": "pilote", "mission": "Apollo 12"},
    {"id": 3, "nom": "Peter Conrad", "role": "commandant", "mission": "Apollo 12"},
    {"id": 4, "nom": "Edgar Mitchell", "role": "pilote", "mission": "Apollo 14"},
    {"id": 5, "nom": "Alan Shepard", "role": "commandant", "mission": "Apollo 14"},
]

prochain_id = 6

def trouver_astronaute(id_astronaute: int):
    """
    Trouve un astronaute par son identifiant.

    Parameters
    ----------
    id_astronaute : int
        Identifiant de l'astronaute à rechercher.

    Returns
    -------
    dict
        Dictionnaire représentant l'astronaute trouvé.

    Raises
    ------
    AstronauteIntrouvable
        Si aucun astronaute avec l'identifiant donné n'est trouvé.
    """
    for astronaute in ASTRONAUTES:
        if astronaute["id"] == id_astronaute:
            return astronaute
    raise AstronauteIntrouvable(id_astronaute)
