"""Erreurs métier pour l'API."""

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


class MissionIntrouvable(ErreurApi):
    def __init__(self, mission):
        self.mission = mission
        super().__init__(f"La mission {mission} n'existe pas")


class MissionDejaExistante(ErreurApi):
    def __init__(self, id_mission: int):
        self.id_mission = id_mission
        super().__init__(f"La mission {id_mission} existe déjà")
        

class MissionUtilisee(ErreurApi):
    def __init__(self, id_mission: int):
        self.id_mission = id_mission
        super().__init__(f"La mission {id_mission} est utilisée par des astronautes et ne peut pas être supprimée")


class EmailDejaUtilise(ErreurApi):
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"L'email {email} est déjà utilisé")
    

class IdentifiantsInvalides(ErreurApi):
    def __init__(self):
        super().__init__("Identifiants invalides")


class UtilisateurIntrouvable(ErreurApi):
    def __init__(self, id_utilisateur: int):
        self.id_utilisateur = id_utilisateur
        super().__init__(f"L'utilisateur {id_utilisateur} n'existe pas")


class JetonManquant(ErreurApi):
    def __init__(self):
        super().__init__("Le jeton est manquant")


class JetonExpire(ErreurApi):
    def __init__(self):
        super().__init__("Le jeton a expiré")


class JetonInvalide(ErreurApi):
    def __init__(self):
        super().__init__("Le jeton est invalide")


class PermissionRefusee(ErreurApi):
    def __init__(self, permission: str):
        self.permission = permission
        super().__init__(f"Permission refusée pour {permission}")