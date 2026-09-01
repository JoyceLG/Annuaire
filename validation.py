CHAMPS_ASTRONAUTE = ("nom", "role", "mission")
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
        elif not isinstance(donnees_entree[champ], str):
            erreurs[champ] = "doit être une chaîne de caractères"
        elif not donnees_entree[champ].strip():
            erreurs[champ] = "ne doit pas être vide"

    if "role" in donnees_entree and "role" not in erreurs:
        if donnees_entree["role"] not in ROLES_VALIDES:
            erreurs["role"] = f"doit être l'un de : {', '.join(sorted(ROLES_VALIDES))}"

    return erreurs
