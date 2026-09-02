# donnees.py
from sqlalchemy import select

from erreurs import AstronauteIntrouvable
from modeles import Astronaute


def trouver_astronaute(bdd, id_astronaute: int) -> Astronaute:
    astronaute = bdd.get(Astronaute, id_astronaute)
    if astronaute is None:
        raise AstronauteIntrouvable(id_astronaute)
    return astronaute


def lister_astronautes(bdd, role=None, mission=None) -> list[Astronaute]:
    requete = select(Astronaute)
    if role:
        requete = requete.where(Astronaute.role.ilike(f"%{role}%"))
    if mission:
        requete = requete.where(Astronaute.mission.ilike(f"%{mission}%"))
    return list(bdd.scalars(requete).all())


def creer_astronaute(bdd, champs: dict) -> Astronaute:
    astronaute = Astronaute(**champs)
    bdd.add(astronaute)
    return astronaute


def supprimer_astronaute(bdd, astronaute: Astronaute) -> None:
    bdd.delete(astronaute)