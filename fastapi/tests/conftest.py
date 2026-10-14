"""Fixtures partagées par tous les fichiers de tests.

Les astronautes vivent dans le dictionnaire `ASTRONAUTES`, partagé par toute
l'application : sans remise à zéro, un test qui supprime Neil Armstrong le
supprimerait aussi pour les tests suivants.
"""

import copy

import pytest
from fastapi.testclient import TestClient

from annuaire.donnees import demonstration
from annuaire.donnees.demonstration import ASTRONAUTES
from main import app


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
    id_courant = demonstration.id_courant
    yield
    ASTRONAUTES.clear()
    ASTRONAUTES.update(sauvegarde)
    # Un entier se réassigne : il faut passer par le module, que
    # demande_prochain_id relit à chaque appel.
    demonstration.id_courant = id_courant


@pytest.fixture
def client():
    return TestClient(app)
