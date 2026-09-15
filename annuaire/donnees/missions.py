"""Accès aux données pour les missions."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..erreurs import MissionDejaExistante, MissionIntrouvable
from ..modeles import Mission


def calculer_programme(nom_mission: str) -> str:
    """Le programme se déduit du nom : « Apollo 11 » → « Apollo »."""

    return nom_mission.split()[0]


def trouver(bdd: Session, id_mission: int) -> Mission:
    mission = bdd.get(Mission, id_mission)
    if mission is None:
        raise MissionIntrouvable(id_mission)
    return mission


def trouver_par_nom(bdd: Session, nom: str) -> Mission:
    mission = bdd.scalars(select(Mission).where(Mission.nom == nom)).first()
    if mission is None:
        raise MissionIntrouvable(nom)
    return mission


def lister(bdd: Session, programme: str | None = None) -> list[Mission]:
    requete = select(Mission)
    if programme:
        requete = requete.where(Mission.programme.ilike(f"%{programme}%"))
    return list(bdd.scalars(requete).all())


def creer(bdd: Session, champs: dict) -> Mission:
    mission = Mission(
        nom=champs["nom"],
        programme=calculer_programme(champs["nom"]),
        annee=champs["annee"],
    )
    bdd.add(mission)
    try:
        # Le flush force l'INSERT : l'identifiant est renseigné, et un nom en
        # double est détecté maintenant plutôt qu'au commit.
        bdd.flush()
    except IntegrityError:
        bdd.rollback()
        raise MissionDejaExistante(mission.id)
    return mission


def supprimer(bdd: Session, mission: Mission) -> None:
    bdd.delete(mission)
