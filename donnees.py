# donnees.py
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from erreurs import (
    AstronauteIntrouvable,
    EmailDejaUtilise,
    IdentifiantsInvalides,
    MissionDejaExistante,
    MissionIntrouvable,
    DonneesInvalides,
    UtilisateurIntrouvable,
)
from modeles import Astronaute, Mission, Utilisateur

hacheur = PasswordHasher()

EMPREINTE_FACTICE = hacheur.hash("mot-de-passe-qui-ne-sera-jamais-utilise")


def trouver_astronaute(bdd, id_astronaute: int) -> Astronaute:
    astronaute = bdd.get(Astronaute, id_astronaute)
    if astronaute is None:
        raise AstronauteIntrouvable(id_astronaute)
    return astronaute


def lister_astronautes(bdd, role=None, mission_id=None) -> list[Astronaute]:
    requete = select(Astronaute).join(Astronaute.mission).options(selectinload(Astronaute.mission))
    if role:
        requete = requete.where(Astronaute.role.ilike(f"%{role}%"))
    if mission_id:
        try :
            mission_id = int(mission_id)
        except ValueError:
            raise DonneesInvalides({ "mission_id": mission_id })
        requete = requete.where(Mission.id == mission_id)
    return list(bdd.scalars(requete).all())


def creer_astronaute(bdd, champs: dict) -> Astronaute:
    mission = trouver_mission(bdd, int(champs["mission_id"]))
    astronaute = Astronaute(nom=champs["nom"], role=champs["role"], mission=mission, nationalite=champs["nationalite"])
    bdd.add(astronaute)
    return astronaute


def supprimer_astronaute(bdd, astronaute: Astronaute) -> None:
    bdd.delete(astronaute)


def calculer_programme(mission: str) -> str:
    return mission.split()[0]   


def trouver_mission(bdd, id_mission: int) -> Mission:
    mission = bdd.get(Mission, id_mission)
    if mission is None:
        raise MissionIntrouvable(id_mission)
    return mission


def trouver_mission_par_nom(bdd, nom: str) -> Mission:
    requete = select(Mission).where(Mission.nom == nom)
    mission = bdd.scalars(requete).first()
    if mission is None:
        raise MissionIntrouvable(nom)
    return mission


def lister_missions(bdd, programme=None) -> list[Mission]:
    requete = select(Mission)
    if programme:
        requete = requete.where(Mission.programme.ilike(f"%{programme}%"))
    return list(bdd.scalars(requete).all())


def creer_mission(bdd, champs: dict) -> Mission:
    mission = Mission(
        nom=champs["nom"],
        programme=calculer_programme(champs["nom"]),
        annee=champs["annee"],
    )
    bdd.add(mission)
    try:
        bdd.flush()
    except IntegrityError:
        bdd.rollback()
        raise MissionDejaExistante(mission.id)
    return mission


def supprimer_mission(bdd, mission: Mission) -> None:
    bdd.delete(mission)


def trouver_utilisateur(bdd, id_utilisateur: int) -> Utilisateur:
    utilisateur = bdd.get(Utilisateur, id_utilisateur)
    if utilisateur is None:
        raise UtilisateurIntrouvable(id_utilisateur)
    return utilisateur


def creer_utilisateur(bdd, email: str, mot_de_passe: str) -> Utilisateur:
    if bdd.scalar(select(Utilisateur).where(Utilisateur.email == email)):
        raise EmailDejaUtilise(email)

    utilisateur = Utilisateur(email=email, empreinte=hacheur.hash(mot_de_passe))
    try:
        with bdd.begin_nested():
            bdd.add(utilisateur)
    except IntegrityError:
        raise EmailDejaUtilise(email)
    return utilisateur


def verifier_identifiants(bdd, email: str, mot_de_passe: str) -> Utilisateur:
    utilisateur = bdd.scalar(select(Utilisateur).where(Utilisateur.email == email))
    if utilisateur is None:
        try:
            hacheur.verify(EMPREINTE_FACTICE, mot_de_passe)  # Simuler le hachage pour éviter les attaques par timing
        except VerifyMismatchError:
            pass
        raise IdentifiantsInvalides()
    try:
        hacheur.verify(utilisateur.empreinte, mot_de_passe)
    except VerifyMismatchError:
        raise IdentifiantsInvalides()
    return utilisateur