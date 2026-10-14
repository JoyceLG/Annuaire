"""Fonctions utilitaires pour la validation des données."""

def nettoyer(valeur):
    return valeur.strip() if isinstance(valeur, str) else valeur