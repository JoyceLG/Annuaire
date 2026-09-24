"""Route de santé : joignable sans jeton, 503 quand la base ne répond pas."""

import logging

import pytest

from annuaire import creer_app
from annuaire.config import ConfigTest


@pytest.fixture
def client_sans_base(tmp_path):
    """Un client dont la base est injoignable : un fichier dans un dossier absent.

    SQLite ne peut pas créer le dossier : l'ouverture échoue dès la première
    requête, comme un serveur de base éteint.
    """

    url = f"sqlite:///{tmp_path / 'dossier_absent' / 'base.db'}"
    return creer_app(ConfigTest, URL_BASE=url).test_client()


# Base joignable : 200, sans jeton
def test_sante_repond_200_sans_jeton(client):
    reponse = client.get("/api/sante")
    assert reponse.status_code == 200
    assert reponse.get_json() == {"statut": "ok"}


# Base injoignable : 503, et non 500
def test_sante_repond_503_si_la_base_est_injoignable(client_sans_base):
    reponse = client_sans_base.get("/api/sante")
    assert reponse.status_code == 503
    assert reponse.get_json() == {"erreur": "Base de données indisponible"}


# La cause de la panne va au journal, jamais dans la réponse
def test_sante_journalise_la_cause_sans_l_exposer(client_sans_base, caplog):
    with caplog.at_level(logging.ERROR):
        reponse = client_sans_base.get("/api/sante")

    assert "dossier_absent" not in reponse.get_data(as_text=True)
    assert "Base de données indisponible" in caplog.text
    assert "unable to open database file" in caplog.text
