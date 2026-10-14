"""Exceptions personnalisées pour l'annuaire des astronautes"""


class AstronauteIntrouvable(Exception):
    def __init__(self, id_astronaute: int):
        self.id_astronaute = id_astronaute
