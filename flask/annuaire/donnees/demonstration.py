"""Jeu de données Apollo de démonstration.

Défini une fois ici, inséré par `flask peupler`. Les tests gardent volontairement
leur propre fixture : les y raccorder ferait échouer toute la suite le jour où
l'on ajoute une mission à la démonstration.
"""

from ..modeles import Astronaute, Mission

MISSIONS = (
    {"nom": "Apollo 11", "annee": 1969},
    {"nom": "Apollo 12", "annee": 1969},
    {"nom": "Apollo 14", "annee": 1971},
)

ASTRONAUTES = (
    {"nom": "Neil Armstrong", "role": "commandant", "nationalite": "Etats-Unis", "mission": "Apollo 11"},
    {"nom": "Alan Bean", "role": "pilote", "nationalite": "Etats-Unis", "mission": "Apollo 12"},
    {"nom": "Peter Conrad", "role": "commandant", "nationalite": "Etats-Unis", "mission": "Apollo 12"},
    {"nom": "Edgar Mitchell", "role": "pilote", "nationalite": "Etats-Unis", "mission": "Apollo 14"},
    {"nom": "Alan Shepard", "role": "commandant", "nationalite": "Etats-Unis", "mission": "Apollo 14"},
)


def construire() -> list:
    """Les objets à insérer, astronautes déjà rattachés à leur mission.

    Le rattachement passe par la relation : SQLAlchemy ordonne les INSERT et
    renseigne mission_id, sans qu'on ait à deviner les identifiants.
    """

    from . import missions as donnees_missions

    par_nom = {
        champs["nom"]: Mission(
            nom=champs["nom"],
            programme=donnees_missions.calculer_programme(champs["nom"]),
            annee=champs["annee"],
        )
        for champs in MISSIONS
    }

    astronautes = [
        Astronaute(
            nom=champs["nom"],
            role=champs["role"],
            nationalite=champs["nationalite"],
            mission=par_nom[champs["mission"]],
        )
        for champs in ASTRONAUTES
    ]
    return [*par_nom.values(), *astronautes]
