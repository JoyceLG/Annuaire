CHAMPS_ASTRONAUTE = ("nom", "role", "mission_id", "nationalite")
CHAMPS_MISSION = ("nom", "annee")
TYPES_ASTRONAUTE = {"nom": str, "role": str, "mission_id": int, "nationalite": str}
TYPES_MISSION = {"nom": str, "annee": int}
ROLES_VALIDES = {"commandant", "pilote", "specialiste"}


def valider_astronaute(donnees_entree, partiel=False):
    """
    Valide les données d'entrée pour un astronaute.

    Parameters
    ----------
    donnees_entree : dict
        Données de l'astronaute à valider.
    partiel : bool, optional
        Indique si la validation est partielle (par défaut False).

    Returns
    -------
    dict
        Dictionnaire des erreurs de validation, vide si tout est valide.
    """
    erreurs = {}

    inconnus = set(donnees_entree) - set(CHAMPS_ASTRONAUTE)
    if inconnus:
        erreurs["champs_inconnus"] = ", ".join(sorted(inconnus))
        return erreurs  # inutile de valider des champs qu'on refuse

    champs_verification = donnees_entree if partiel else CHAMPS_ASTRONAUTE

    for champ in champs_verification:
        if champ not in donnees_entree:
            erreurs[champ] = "champ obligatoire manquant"
        elif not isinstance(donnees_entree[champ], TYPES_ASTRONAUTE[champ]):
            erreurs[champ] = f"doit être de type {TYPES_ASTRONAUTE[champ].__name__}"
        elif TYPES_ASTRONAUTE[champ] is str and not donnees_entree[champ].strip():
            erreurs[champ] = "ne doit pas être vide"

    if "role" in donnees_entree and "role" not in erreurs:
        if donnees_entree["role"] not in ROLES_VALIDES:
            erreurs["role"] = f"doit être l'un de : {', '.join(sorted(ROLES_VALIDES))}"
        
    if "mission_id" in donnees_entree and "mission_id" not in erreurs:
        if isinstance(donnees_entree["mission_id"], bool):
            erreurs["mission_id"] = "ne doit pas être un booléen"
        else:
            try:
                int(donnees_entree["mission_id"])
            except ValueError:
                erreurs["mission_id"] = "doit être un entier"
            
    return erreurs

def valider_mission(donnees_entree: dict, partiel=False):
    """
    Valide les données d'entrée pour une mission.

    Parameters
    ----------
    donnees_entree : dict
        Données de la mission à valider.
    partiel : bool, optional
        Indique si la validation est partielle (par défaut False).

    Returns
    -------
    dict
        Dictionnaire des erreurs de validation, vide si tout est valide.
    """
    erreurs = {}

    inconnus = set(donnees_entree) - set(CHAMPS_MISSION)
    if inconnus:
        erreurs["champs_inconnus"] = ", ".join(sorted(inconnus))
        return erreurs  # inutile de valider des champs qu'on refuse

    champs_verification = donnees_entree if partiel else CHAMPS_MISSION

    for champ in champs_verification:
        if champ not in donnees_entree:
            erreurs[champ] = "champ obligatoire manquant"
        elif not isinstance(donnees_entree[champ], TYPES_MISSION[champ]):
            erreurs[champ] = f"doit être de type {TYPES_MISSION[champ].__name__}"
        elif isinstance(donnees_entree[champ], str) and not donnees_entree[champ].strip():
            erreurs[champ] = "ne doit pas être vide"
            
    if "annee" in donnees_entree and "annee" not in erreurs:
        if isinstance(donnees_entree["annee"], bool):
            erreurs["annee"] = "ne doit pas être un booléen"

    return erreurs

