class ErreurApi(Exception):
    """Classe de base pour les erreurs métier."""


class AstronauteIntrouvable(ErreurApi):
    def __init__(self, id_astronaute: int):
        self.id_astronaute = id_astronaute
        super().__init__(f"L'astronaute {id_astronaute} n'existe pas")


class DonneesInvalides(ErreurApi):
    def __init__(self, details: dict):
        self.details = details
        super().__init__("Validation échouée")
