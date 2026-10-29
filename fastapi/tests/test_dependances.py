"""Dépendances injectées : pagination, dépôts, authentification.

Les dépendances se testent à travers les routes qui les utilisent, et en les
remplaçant par `app.dependency_overrides` : c'est le mécanisme que FastAPI
prévoit pour cela, sans toucher aux globales de l'application.
"""

import logging

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from annuaire import creer_app
from annuaire.bdd import session_bdd
from annuaire.config import ConfigTest
from annuaire.dependances import (
    depot_astronautes,
    jeton_de_l_en_tete,
    jeton_valide,
)
from annuaire.modeles import Base, Mission

# Chaque liste paginée, avec les noms de son jeu de démonstration, dans l'ordre.
LISTES = {
    "/api/astronautes": ["Neil Armstrong", "Alan Bean", "Sophie Adenot"],
    "/api/missions": ["Apollo 11", "Apollo 12", "Apollo 13"],
}


class ConfigPetitesPages(ConfigTest):
    """Des limites assez basses pour les observer sur trois éléments."""

    LIMITE_PAGINATION_DEFAUT = 2
    LIMITE_PAGINATION_MAX = 2


@pytest.fixture
def client_petites_pages():
    """Un client sur une application construite avec ConfigPetitesPages.

    `with` : sans lui, le lifespan ne s'exécute pas et /api/missions
    n'aurait pas de base (voir la fixture `client` de conftest).
    """
    with TestClient(creer_app(ConfigPetitesPages)) as client:
        yield client


def noms(reponse):
    return [element["nom"] for element in reponse.json()]


# --- Pagination ----------------------------------------------------------


# Vérifie que sans paramètre, la liste commence au premier élément.
@pytest.mark.parametrize("chemin", LISTES)
def test_pagination_commence_au_debut(client, chemin):
    reponse = client.get(chemin)

    assert reponse.status_code == 200
    assert noms(reponse) == LISTES[chemin]


# Vérifie que le décalage saute les premiers éléments.
@pytest.mark.parametrize("chemin", LISTES)
def test_pagination_decalage(client, chemin):
    reponse = client.get(f"{chemin}?decalage=1")

    assert noms(reponse) == LISTES[chemin][1:]


# Vérifie que limite et décalage se combinent : la deuxième page d'une
# pagination à un élément par page.
@pytest.mark.parametrize("chemin", LISTES)
def test_pagination_limite_et_decalage(client, chemin):
    reponse = client.get(f"{chemin}?limite=1&decalage=1")

    assert noms(reponse) == [LISTES[chemin][1]]


# Vérifie qu'un décalage au-delà de la fin renvoie une liste vide, pas une erreur.
@pytest.mark.parametrize("chemin", LISTES)
def test_pagination_decalage_au_dela_de_la_fin(client, chemin):
    reponse = client.get(f"{chemin}?decalage=10")

    assert reponse.status_code == 200
    assert reponse.json() == []


# Vérifie qu'une limite nulle ou un décalage négatif sont refusés (422).
@pytest.mark.parametrize("chemin", LISTES)
@pytest.mark.parametrize("parametres", ["limite=0", "decalage=-1"])
def test_pagination_valeurs_invalides(client, chemin, parametres):
    assert client.get(f"{chemin}?{parametres}").status_code == 422


# Vérifie que la limite par défaut vient de la configuration.
@pytest.mark.parametrize("chemin", LISTES)
def test_pagination_limite_par_defaut_de_la_configuration(client_petites_pages, chemin):
    reponse = client_petites_pages.get(chemin)

    assert noms(reponse) == LISTES[chemin][:2]


# Vérifie que la limite maximale vient de la configuration : atteinte, elle
# est acceptée ; dépassée, la requête est refusée (422, format {"erreur"}).
@pytest.mark.parametrize("chemin", LISTES)
def test_pagination_limite_maximale_de_la_configuration(client_petites_pages, chemin):
    assert client_petites_pages.get(f"{chemin}?limite=2").status_code == 200

    reponse = client_petites_pages.get(f"{chemin}?limite=3")

    assert reponse.status_code == 422
    assert reponse.json() == {"erreur": "la limite ne peut pas dépasser 2 (reçu : 3)"}


# Vérifie que la pagination suit la configuration passée à creer_app, même
# quand ENVIRONNEMENT désigne un autre environnement.
def test_pagination_suit_la_configuration_de_creer_app(monkeypatch):
    monkeypatch.setenv("ENVIRONNEMENT", "developpement")
    with TestClient(creer_app(ConfigPetitesPages)) as client:
        assert len(client.get("/api/missions").json()) == 2
        assert client.get("/api/missions?limite=3").status_code == 422


# --- Dépôts --------------------------------------------------------------


# Vérifie que les routes lisent les données dans le dépôt injecté, et non
# directement dans le jeu de démonstration.
@pytest.mark.parametrize(
    "chemin, depot, element",
    [
        (
            "/api/astronautes",
            depot_astronautes,
            {"id": 7, "nom": "Thomas Pesquet", "role": "specialiste", "nationalite": "Française"},
        ),
        # Les missions n'ont plus de dépôt : elles lisent la session de base
        # injectée, vérifiée par test_missions_lisent_la_session_injectee.
    ],
)
def test_routes_lisent_le_depot_injecte(app, client, chemin, depot, element):
    app.dependency_overrides[depot] = lambda: {7: element}

    assert noms(client.get(chemin)) == [element["nom"]]
    assert client.get(f"{chemin}/7").json()["nom"] == element["nom"]
    assert client.get(f"{chemin}/1").status_code == 404


async def session_avec_proxima():
    """Une session sur une base distincte, ne contenant que Proxima.

    Le moteur est créé ici, dans la boucle d'événements de la requête :
    une connexion aiosqlite est liée à la boucle qui l'a ouverte, et en
    créer une hors de cette boucle échouerait à l'usage.
    """
    moteur = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with moteur.begin() as connexion:
        await connexion.run_sync(Base.metadata.create_all)
    fabrique = async_sessionmaker(moteur, expire_on_commit=False)
    async with fabrique() as session:
        session.add(Mission(id=7, nom="Proxima", annee=2016))
        await session.commit()
    async with fabrique() as session:
        yield session
    await moteur.dispose()


# Vérifie que les routes des missions lisent la session injectée, et non une
# base fixée en dur : en remplaçant session_bdd, la route ne voit plus que
# Proxima. C'est dependency_overrides appliqué à la base de données.
def test_missions_lisent_la_session_injectee(app, client):
    app.dependency_overrides[session_bdd] = session_avec_proxima

    assert noms(client.get("/api/missions")) == ["Proxima"]
    assert client.get("/api/missions/7").json()["nom"] == "Proxima"
    assert client.get("/api/missions/1").status_code == 404


# Vérifie que le dépôt est refermé après la requête, même quand la route
# lève une exception (ici un 404).
@pytest.mark.parametrize("chemin", ["/api/astronautes/999"])
def test_depot_referme_meme_en_cas_d_erreur(client, caplog, chemin):
    caplog.set_level(logging.DEBUG, logger="annuaire.dependances")

    assert client.get(chemin).status_code == 404

    assert caplog.messages == [
        "ouverture de l'accès aux données",
        "fermeture de l'accès aux données",
    ]


# --- Authentification ----------------------------------------------------


# Vérifie qu'un vrai en-tête Bearer ouvre les écritures, sans remplacer la
# dépendance comme le fait client_authentifie.
@pytest.mark.parametrize(
    "chemin, corps",
    [
        (
            "/api/astronautes",
            {
                "nom": "Edgar Mitchell",
                "role": "pilote",
                "nationalite": "Etats-Unis",
                "qualification": {"type": "pilote", "heures_vol": 1500, "appareil": "T-38"},
            },
        ),
        ("/api/missions", {"nom": "Apollo 14", "annee": 1971}),
    ],
)
def test_en_tete_bearer_ouvre_les_ecritures(client, chemin, corps):
    reponse = client.post(chemin, json=corps, headers={"Authorization": "Bearer abc"})

    assert reponse.status_code == 201


# Vérifie qu'un en-tête mal formé ou sans jeton est refusé (401).
@pytest.mark.parametrize("en_tete", ["abc", "Basic abc", "Bearer ", "Bearer    "])
def test_en_tete_invalide_refuse(client, en_tete):
    reponse = client.delete("/api/missions/1", headers={"Authorization": en_tete})

    assert reponse.status_code == 401
    assert client.get("/api/missions/1").status_code == 200


# Vérifie que le 401 a le format d'erreur du projet et annonce le schéma
# d'authentification attendu (WWW-Authenticate).
def test_refus_au_format_du_projet(client):
    reponse = client.delete("/api/missions/1")

    assert reponse.status_code == 401
    assert reponse.json() == {"erreur": "Authentification requise"}
    assert reponse.headers["WWW-Authenticate"] == "Bearer"


# Vérifie que les lectures restent ouvertes sans jeton.
@pytest.mark.parametrize("chemin", ["/api/astronautes", "/api/astronautes/1", "/api/missions", "/api/missions/1"])
def test_lectures_ouvertes_sans_jeton(client, chemin):
    assert client.get(chemin).status_code == 200


# Vérifie l'extraction du jeton de l'en-tête Authorization.
@pytest.mark.parametrize(
    "en_tete, attendu",
    [
        ("Bearer abc", "abc"),
        ("Bearer ", ""),
        ("Basic abc", None),
        ("bearer abc", None),
        ("", None),
        (None, None),
    ],
)
def test_jeton_de_l_en_tete(en_tete, attendu):
    assert jeton_de_l_en_tete(en_tete) == attendu


# Vérifie qu'un jeton absent, vide ou blanc est refusé.
@pytest.mark.parametrize("jeton, attendu", [("abc", True), ("", False), ("   ", False), (None, False)])
def test_jeton_valide(jeton, attendu):
    assert jeton_valide(jeton) is attendu
