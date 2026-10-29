"""Fixtures partagées par tous les fichiers de tests.

Les astronautes vivent dans le dictionnaire `ASTRONAUTES`, partagé par toute
l'application : sans remise à zéro, un test qui supprime Neil Armstrong le
supprimerait aussi pour les tests suivants.
"""

import copy

import pytest
from fastapi.testclient import TestClient

from annuaire import creer_app
from annuaire.dependances import authentification_requise
from annuaire.donnees import demonstration
from annuaire.donnees.demonstration import ASTRONAUTES, MISSIONS


@pytest.fixture(autouse=True)
def astronautes_neufs():
    """Restaure le jeu de démonstration après chaque test.

    La restauration se fait en place (`clear` puis `update`) : les routes ont
    importé l'objet dictionnaire lui-même, en réassigner un nouveau ne les
    atteindrait pas. La copie est profonde car PATCH et PUT modifient les
    dictionnaires des astronautes eux-mêmes.

    Le compteur d'identifiants est restauré lui aussi : sans cela, l'id
    attribué par une création dépendrait du nombre de créations faites par
    les tests précédents.
    """

    sauvegarde = copy.deepcopy(ASTRONAUTES)
    id_courant = demonstration.id_astronaute_courant
    yield
    ASTRONAUTES.clear()
    ASTRONAUTES.update(sauvegarde)
    # Un entier se réassigne : il faut passer par le module, que
    # demande_prochain_id relit à chaque appel.
    demonstration.id_astronaute_courant = id_courant


@pytest.fixture(autouse=True)
def missions_neuves():
    """Restaure les missions de démonstration après chaque test.

    Même raisonnement que pour les astronautes : restauration en place du
    dictionnaire, copie profonde, et compteur d'identifiants remis à sa valeur.
    """

    sauvegarde = copy.deepcopy(MISSIONS)
    id_courant = demonstration.id_mission_courant
    yield
    MISSIONS.clear()
    MISSIONS.update(sauvegarde)
    demonstration.id_mission_courant = id_courant


@pytest.fixture
def app():
    """L'application de test, partagée par les clients d'un même test.

    Un test peut ainsi y remplacer une dépendance (`app.dependency_overrides`)
    avant d'interroger `client` : le remplacement s'applique, et disparaît
    avec l'application à la fin du test.
    """
    return creer_app("test")


@pytest.fixture
def client_authentifie(app):
    """Un client dispensé d'en-tête Authorization, pour tester les écritures.

    Attention : `client` utilise la même application, il est donc lui aussi
    authentifié dans un test qui demande les deux fixtures.
    """
    app.dependency_overrides[authentification_requise] = lambda: None
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def client(app):
    return TestClient(app)
