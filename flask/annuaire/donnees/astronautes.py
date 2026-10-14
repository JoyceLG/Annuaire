"""Accès aux données pour les astronautes."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..erreurs import AstronauteIntrouvable, DonneesInvalides
from ..modeles import Astronaute, Mission
from . import missions as donnees_missions


def trouver(bdd: Session, id_astronaute: int) -> Astronaute:
    astronaute = bdd.get(Astronaute, id_astronaute)
    if astronaute is None:
        raise AstronauteIntrouvable(id_astronaute)
    return astronaute


def lister(bdd: Session, role=None, mission_id=None) -> list[Astronaute]:
    # `selectinload` charge les missions en une requête supplémentaire, au lieu
    # d'une par astronaute (N+1).
    requete = (
        select(Astronaute)
        .join(Astronaute.mission)
        .options(selectinload(Astronaute.mission))
        .order_by(Astronaute.id)
    )
    if role:
        requete = requete.where(Astronaute.role.ilike(f"%{role}%"))
    if mission_id:
        try:
            mission_id = int(mission_id)
        except ValueError:
            raise DonneesInvalides({"mission_id": mission_id})
        requete = requete.where(Mission.id == mission_id)
    return list(bdd.scalars(requete).all())


def creer(bdd: Session, champs: dict) -> Astronaute:
    mission = donnees_missions.trouver(bdd, int(champs["mission_id"]))
    astronaute = Astronaute(
        nom=champs["nom"],
        role=champs["role"],
        nationalite=champs["nationalite"],
        mission=mission,
    )
    bdd.add(astronaute)
    return astronaute


def supprimer(bdd: Session, astronaute: Astronaute) -> None:
    bdd.delete(astronaute)
