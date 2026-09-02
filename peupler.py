#!/usr/bin/env python3
from bdd import FabriqueSession
from modeles import Astronaute, Mission


with FabriqueSession() as session:
    apollo_11 = Mission(nom="Apollo 11", programme="Apollo", annee=1969)
    apollo_12 = Mission(nom="Apollo 12", programme="Apollo", annee=1969)
    apollo_14 = Mission(nom="Apollo 14", programme="Apollo", annee=1971)

    # Les astronautes sont rattachés par la relation : SQLAlchemy ordonne les
    # INSERT et renseigne mission_id, sans qu'on ait à deviner les identifiants.
    session.add_all([
        apollo_11,
        apollo_12,
        apollo_14,
        Astronaute(nom="Neil Armstrong", role="commandant",
                   nationalite="Etats-Unis", mission=apollo_11),
        Astronaute(nom="Alan Bean", role="pilote",
                   nationalite="Etats-Unis", mission=apollo_12),
        Astronaute(nom="Peter Conrad", role="commandant",
                   nationalite="Etats-Unis", mission=apollo_12),
        Astronaute(nom="Edgar Mitchell", role="pilote",
                   nationalite="Etats-Unis", mission=apollo_14),
        Astronaute(nom="Alan Shepard", role="commandant",
                   nationalite="Etats-Unis", mission=apollo_14),
    ])
    session.commit()
    print("Base peuplée : 3 missions, 5 astronautes.")
