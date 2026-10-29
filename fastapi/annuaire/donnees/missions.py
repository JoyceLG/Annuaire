"""Accès aux missions.

Chaque fonction reçoit la session en paramètre ordinaire : aucun `Depends`,
aucun `import fastapi`. C'est la frontière de la session 10, transposée —
ce module fonctionnerait aussi bien dans un script ou une tâche de fond.

Aucune fonction ne fait `commit()` : c'est la route qui décide quand la
transaction se termine (session 11).
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from annuaire.erreurs import MissionIntrouvable, MissionUtilisee
from annuaire.modeles import Mission


async def lister(
    bdd: AsyncSession,
    *,
    annee: int | None,
    limite: int,
    decalage: int,
) -> list[Mission]:
    """Les missions, éventuellement depuis une année, paginées."""
    requete = select(Mission).options(selectinload(Mission.equipage))
    if annee is not None:
        requete = requete.where(Mission.annee >= annee)
    requete = requete.order_by(Mission.id).offset(decalage).limit(limite)
    resultat = await bdd.scalars(requete)
    return list(resultat.all())


async def trouver(bdd: AsyncSession, id_mission: int) -> Mission:
    requete = (
        select(Mission)
        .options(selectinload(Mission.equipage))
        .where(Mission.id == id_mission)
    )
    mission = (await bdd.scalars(requete)).first()
    if mission is None:
        raise MissionIntrouvable(id_mission)
    return mission


async def creer(bdd: AsyncSession, champs: dict) -> Mission:
    """Ajoute une mission. L'identifiant est attribué par la base au flush."""
    # equipage=[] : une mission neuve n'a pas d'équipage. Sans cette valeur,
    # lire mission.equipage (MissionSortie le fait) lancerait un chargement
    # paresseux, impossible en asynchrone : MissingGreenlet.
    mission = Mission(**champs, equipage=[])
    bdd.add(mission)
    # flush envoie l'INSERT sans terminer la transaction : la base attribue
    # l'identifiant, que la route peut lire pour construire son Location.
    await bdd.flush()
    return mission


def modifier(mission: Mission, champs: dict) -> Mission:
    """Applique des champs à une mission déjà chargée.

    Synchrone : modifier un attribut n'émet aucune requête, la session
    détecte le changement et l'enverra au commit (unité de travail,
    session 11).
    """
    for nom, valeur in champs.items():
        setattr(mission, nom, valeur)
    return mission


async def supprimer(bdd: AsyncSession, mission: Mission) -> None:
    """Marque une mission pour suppression ; effective au commit.

    Refusée (MissionUtilisee) si la mission a un équipage : l'annuaire ne
    perd pas des membres d'équipage par effet de bord. La règle est ici, et
    non dans la route, pour protéger tout appelant. `mission.equipage` est
    déjà chargé par `trouver` (selectinload) : aucune requête implicite.
    """
    if mission.equipage:
        raise MissionUtilisee(mission.id)
    await bdd.delete(mission)
