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


# Vérifie qu'en production /docs, /redoc et /openapi.json répondent 401 sans
# connexion : le schéma de l'API ne fuit pas, même avec une casse ou des
# espaces inattendus.
@pytest.mark.parametrize("environnement", ["production", " Production "])
def test_documentation_protegee_en_production(monkeypatch, environnement):
    monkeypatch.setenv("ENVIRONNEMENT", environnement)

    client = TestClient(creer_app())

    for chemin in CHEMINS_DOCUMENTATION:
        reponse = client.get(chemin)
        assert reponse.status_code == 401, chemin
        assert "openapi" not in reponse.text, chemin


# Le cookie de connexion est `secure` : le client de test doit parler HTTPS
# pour le recevoir et le renvoyer, comme un navigateur.
@pytest.fixture
def client_production():
    return TestClient(creer_app("production"), base_url="https://testserver")


# Vérifie qu'en production, /docs sans connexion affiche le formulaire de
# connexion, et non Swagger UI.
def test_docs_sans_connexion_affiche_le_formulaire(client_production):
    reponse = client_production.get("/docs")

    assert reponse.status_code == 401
    assert 'action="/docs/connexion"' in reponse.text
    assert "swagger-ui" not in reponse.text


# Vérifie que la connexion pose un cookie httponly, secure et samesite=lax,
# puis renvoie vers /docs par un 303.
def test_connexion_pose_le_cookie(client_production):
    reponse = client_production.post(
        "/docs/connexion", data={"jeton": "abc"}, follow_redirects=False
    )

    assert reponse.status_code == 303
    assert reponse.headers["Location"] == "/docs"
    cookie = reponse.headers["set-cookie"].lower()
    assert cookie.startswith("jeton_documentation=abc;")
    for attribut in ("httponly", "secure", "samesite=lax"):
        assert attribut in cookie, attribut


# Vérifie qu'une fois connecté, le navigateur obtient Swagger UI, ReDoc et le
# schéma grâce au seul cookie, sans en-tête Authorization.
def test_cookie_ouvre_la_documentation(client_production):
    client_production.post("/docs/connexion", data={"jeton": "abc"})

    assert "swagger-ui" in client_production.get("/docs").text
    assert "redoc" in client_production.get("/redoc").text
    schema = client_production.get("/openapi.json")
    assert schema.status_code == 200
    assert schema.json()["info"]["title"] == "Annuaire des astronautes"


# Vérifie que l'en-tête Authorization ouvre aussi le schéma : un outil en
# ligne de commande n'a pas besoin de passer par le formulaire.
def test_en_tete_ouvre_le_schema(client_production):
    reponse = client_production.get(
        "/openapi.json", headers={"Authorization": "Bearer abc"}
    )

    assert reponse.status_code == 200


# Vérifie qu'un jeton vide est refusé : pas de cookie, formulaire réaffiché.
def test_connexion_avec_jeton_vide_refusee(client_production):
    reponse = client_production.post("/docs/connexion", data={"jeton": "   "})

    assert reponse.status_code == 401
    assert "set-cookie" not in reponse.headers
    assert client_production.get("/openapi.json").status_code == 401


# Vérifie que la connexion ne redirige que vers une page de documentation :
# une adresse arbitraire dans `suite` enverrait l'utilisateur sur un site tiers.
def test_connexion_ne_redirige_pas_hors_documentation(client_production):
    reponse = client_production.post(
        "/docs/connexion",
        data={"jeton": "abc", "suite": "https://exemple.org"},
        follow_redirects=False,
    )

    assert reponse.headers["Location"] == "/docs"


# Vérifie que le cookie de la documentation n'ouvre pas les routes d'écriture
# de l'API : elles n'acceptent que l'en-tête, à l'abri des attaques CSRF.
def test_cookie_n_ouvre_pas_l_api(client_production):
    client_production.post("/docs/connexion", data={"jeton": "abc"})

    reponse = client_production.delete("/api/astronautes/1")

    assert reponse.status_code == 401


# Vérifie qu'un environnement inconnu empêche l'application de démarrer.
def test_environnement_inconnu_refuse_de_demarrer(monkeypatch):
    monkeypatch.setenv("ENVIRONNEMENT", "prod")

    with pytest.raises(RuntimeError, match="Environnement inconnu"):
        creer_app()
