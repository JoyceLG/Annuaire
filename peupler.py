#!/usr/bin/env python3
from bdd import FabriqueSession
from modeles import Astronaute


with FabriqueSession() as session:
    session.add_all([
        Astronaute(nom="Neil Armstrong", role="commandant", mission="Apollo 11", nationalite="Etats-Unis"),
        Astronaute(nom="Alan Bean", role="pilote", mission="Apollo 12", nationalite="Etats-Unis"),
        Astronaute(nom="Peter Conrad", role="commandant", mission="Apollo 12", nationalite="Etats-Unis"),
        Astronaute(nom="Edgar Mitchell", role="pilote", mission="Apollo 14", nationalite="Etats-Unis"),
        Astronaute(nom="Alan Shepard", role="commandant", mission="Apollo 14", nationalite="Etats-Unis"),
    ])
    session.commit()
    print("Base peuplée.")