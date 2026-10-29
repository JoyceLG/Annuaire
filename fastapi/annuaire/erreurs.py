"""Exceptions personnalisées pour l'annuaire des astronautes"""


class AstronauteIntrouvable(Exception):
    def __init__(self, id_astronaute: int):
        self.id_astronaute = id_astronaute


class QualificationIncoherente(ValueError):
    # Hérite de ValueError : levée dans un validateur, Pydantic la transforme
    # en erreur de validation ; levée dans une route, son gestionnaire répond 422.
    def __init__(self, role: str, admises: frozenset[str]):
        self.role = role
        self.admises = admises
        super().__init__(
            f"un astronaute {role} doit avoir une qualification "
            f"parmi : {', '.join(sorted(admises))}"
        )


class MissionIntrouvable(Exception):
    def __init__(self, id_mission: int):
        self.id_mission = id_mission


class AuthentificationRequise(Exception):
    """Route protégée appelée sans jeton valide."""


class LimiteTropGrande(Exception):
    def __init__(self, limite: int, maximum: int):
        self.limite = limite
        self.maximum = maximum
        super().__init__(f"la limite ne peut pas dépasser {maximum} (reçu : {limite})")
