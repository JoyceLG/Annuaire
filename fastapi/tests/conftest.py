"""Fixtures partagées par tous les fichiers de tests.

Les astronautes vivent encore dans le dictionnaire `ASTRONAUTES`, partagé par
toute l'application : sans remise à zéro, un test qui supprime Neil Armstrong
le supprimerait aussi pour les tests suivants.

Les missions, elles, sont en base. Chaque test construit sa propre
application, donc son propre moteur, donc sa propre base SQLite en mémoire :
l'isolation est obtenue par construction, sans rien restaurer.
"""

import copy

import pytest
from fastapi.testclient import TestClient

from annuaire import creer_app
from annuaire.dependances import authentification_requise
from annuaire.donnees import demonstration
from annuaire.donnees.demonstration import ASTRONAUTES


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
    # `with` est indispensable : voir la fixture `client`.
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def client(app):
    """Un client qui démarre réellement l'application.

    Le `with` n'est pas décoratif : sans lui, TestClient n'exécute PAS le
    lifespan. Le moteur ne serait jamais créé, `app.state.fabrique`
    n'existerait pas, et toute route touchant la base répondrait 500.
    C'est le piège principal de cette session.
    """
    with TestClient(app) as client:
        yield client
