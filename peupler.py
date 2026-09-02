#!/usr/bin/env python3
from bdd import FabriqueSession, creer_tables
from modeles import Astronaute

creer_tables()

with FabriqueSession() as session:
    session.add_all([
        Astronaute(nom="Neil Armstrong", role="commandant", mission="Apollo 11"),
        Astronaute(nom="Alan Bean", role="pilote", mission="Apollo 12"),
        Astronaute(nom="Peter Conrad", role="commandant", mission="Apollo 12"),
        Astronaute(nom="Edgar Mitchell", role="pilote", mission="Apollo 14"),
        Astronaute(nom="Alan Shepard", role="commandant", mission="Apollo 14"),
    ])
    session.commit()
    print("Base peuplée.")