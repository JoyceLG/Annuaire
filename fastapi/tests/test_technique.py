"""Routes techniques et exposition de la documentation selon l'environnement."""

import pytest
from fastapi.testclient import TestClient

from annuaire import creer_app

CHEMINS_DOCUMENTATION = ("/docs", "/redoc", "/openapi.json")


# Application démarrée : 200 et statut « ok »
def test_sante_repond_200(client):
    reponse = client.get("/api/technique/sante")
    assert reponse.status_code == 200
    assert reponse.json() == {"statut": "ok"}


# Vérifie que la documentation est publiée hors production, y compris quand
# ENVIRONNEMENT est absent (l'environnement par défaut est le développement).
@pytest.mark.parametrize("environnement", ["developpement", "test", None])
def test_documentation_ouverte_hors_production(monkeypatch, environnement):
    if environnement is None:
        monkeypatch.delenv("ENVIRONNEMENT", raising=False)
    else:
        monkeypatch.setenv("ENVIRONNEMENT", environnement)

    client = TestClient(creer_app())

    for chemin in CHEMINS_DOCUMENTATION:
        assert client.get(chemin).status_code == 200, chemin


# Vérifie qu'en production /docs, /redoc et /openapi.json répondent 404 :
# le schéma de l'API ne fuit pas, même avec une casse ou des espaces inattendus.
@pytest.mark.parametrize("environnement", ["production", " Production "])
def test_documentation_coupee_en_production(monkeypatch, environnement):
    monkeypatch.setenv("ENVIRONNEMENT", environnement)

    client = TestClient(creer_app())

    for chemin in CHEMINS_DOCUMENTATION:
        assert client.get(chemin).status_code == 404, chemin


# Vérifie qu'un environnement inconnu empêche l'application de démarrer.
def test_environnement_inconnu_refuse_de_demarrer(monkeypatch):
    monkeypatch.setenv("ENVIRONNEMENT", "prod")

    with pytest.raises(RuntimeError, match="Environnement inconnu"):
        creer_app()
