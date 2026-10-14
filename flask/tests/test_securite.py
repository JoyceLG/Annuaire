"""Tests de sécurité : jetons, rôles, et routes fermées par défaut."""

import secrets
from datetime import UTC, datetime, timedelta

import jwt
import logging
import pytest
from annuaire import creer_app

from flask import Blueprint

from annuaire import config
from annuaire.config import ConfigProduction
from annuaire.routes.commun import publique


# Un jeton expiré doit être refusé : 401
def test_jeton_expire_est_refuse(client, app):
    passe = datetime.now(UTC) - timedelta(hours=1)
    jeton = jwt.encode(
        {"sub": "1", "exp": passe}, app.config["CLE_SECRETE_JWT"], algorithm="HS256"
    )
    reponse = client.delete(
        "/api/astronautes/1", headers={"Authorization": f"Bearer {jeton}"}
    )
    assert reponse.status_code == 401


# Un jeton signé avec une autre clé doit être refusé : 401
def test_jeton_signe_avec_une_autre_cle_est_refuse(client):
    jeton = jwt.encode(
        {"sub": "1", "exp": datetime.now(UTC) + timedelta(minutes=5)},
        secrets.token_urlsafe(32),  # clé assez longue pour HS256, mais pas la bonne
        algorithm="HS256",
    )
    reponse = client.delete(
        "/api/astronautes/1", headers={"Authorization": f"Bearer {jeton}"}
    )
    assert reponse.status_code == 401


# Chaque route protégée sans jeton : 401
def test_route_protegee_sans_jeton(client):
    reponse = client.delete("/api/astronautes/1")
    assert reponse.status_code == 401


# Jeton falsifié : 401
def test_jeton_falsifie_est_refuse(client):
    jeton = "falsifie"
    reponse = client.delete(
        "/api/astronautes/1", headers={"Authorization": f"Bearer {jeton}"}
    )
    assert reponse.status_code == 401


# En-tête sans le préfixe Bearer : 401
def test_en_tete_sans_bearer_est_refuse(client, app):
    jeton = jwt.encode(
        {"sub": "1", "exp": datetime.now(UTC) + timedelta(minutes=5)},
        app.config["CLE_SECRETE_JWT"],
        algorithm="HS256",
    )
    reponse = client.delete(
        "/api/astronautes/1", headers={"Authorization": f"{jeton}"}
    )
    assert reponse.status_code == 401


# Les lectures fonctionnent sans jeton : 200
def test_lecture_sans_jeton(client):
    reponse = client.get("/api/astronautes/1")
    assert reponse.status_code == 200

    reponse = client.get("/api/missions/1")
    assert reponse.status_code == 200


# Chaque écriture avec un jeton lecteur : 403
def test_ecriture_avec_jeton_lecteur_est_refuse(client, entetes_lecteur):
    reponse = client.post("/api/astronautes", headers=entetes_lecteur, json={"nom": "Test"})
    assert reponse.status_code == 403

    reponse = client.put("/api/astronautes/1", headers=entetes_lecteur, json={"nom": "Test"})
    assert reponse.status_code == 403

    reponse = client.patch("/api/astronautes/1", headers=entetes_lecteur, json={"nom": "Test"})
    assert reponse.status_code == 403

    reponse = client.delete("/api/astronautes/1", headers=entetes_lecteur)
    assert reponse.status_code == 403


# Chaque écriture avec un jeton editeur : 201 ou 200, sauf DELETE en 403
def test_ecriture_avec_jeton_editeur(client, entetes_editeur):
    reponse = client.post("/api/astronautes", headers=entetes_editeur, json={"nom": "Michael Collins", "role": "pilote", "mission_id": 1, "nationalite": "Etats-Unis"})
    assert reponse.status_code == 201

    reponse = client.put("/api/astronautes/1", headers=entetes_editeur, json={"nom": "Michel Colin", "role": "pilote", "mission_id": 1, "nationalite": "Etats-Unis"})
    assert reponse.status_code == 200

    reponse = client.patch("/api/astronautes/1", headers=entetes_editeur, json={"nom": "Michael Collins"})
    assert reponse.status_code == 200

    reponse = client.delete("/api/astronautes/1", headers=entetes_editeur)
    assert reponse.status_code == 403


# DELETE avec un jeton admin : 204
def test_delete_avec_jeton_admin(client, entetes_admin):
    reponse = client.delete("/api/astronautes/1", headers=entetes_admin)
    assert reponse.status_code == 204


# Aucune vue n'échappe au garde-fou : chacune se déclare publique ou protégée
def test_toutes_les_vues_sont_declarees(app):
    for regle in app.url_map.iter_rules():
        if regle.endpoint == "static":
            continue
        vue = app.view_functions[regle.endpoint]
        assert getattr(vue, "publique", False) or getattr(vue, "protegee", False), (
            f"{regle.endpoint} n'est ni @publique ni protégée par un décorateur"
        )


# Toutes les écritures exigent un jeton
def test_toutes_les_ecritures_sont_protegees(client, app):
    # Les règles s'écrivent « /api/astronautes/<int:id> » : il faut les
    # construire avec de vraies valeurs, sinon on teste une URL inexistante.
    adaptateur = app.url_map.bind("localhost")

    for regle in app.url_map.iter_rules():
        methodes = regle.methods - {"HEAD", "OPTIONS"}
        if not methodes & {"POST", "PUT", "PATCH", "DELETE"}:
            continue

        vue = app.view_functions[regle.endpoint]
        if getattr(vue, "publique", False):
            continue  # inscription et connexion, par construction

        url = adaptateur.build(regle.endpoint, {nom: 1 for nom in regle.arguments})
        for methode in methodes:
            reponse = client.open(url, method=methode)
            assert reponse.status_code == 401, f"{methode} {url} non protégée"


# Le garde-fou est branché sur l'application (app.before_request), pas sur un
# blueprint : une vue nue ajoutée à n'importe quel blueprint est refusée.
def test_garde_fou_couvre_un_autre_blueprint(app):
    bp_tardif = Blueprint("tardif", __name__, url_prefix="/api")

    @bp_tardif.get("/route-nue")
    def route_nue():  # ni @publique, ni décorateur d'accès
        return {"secret": "ne doit jamais sortir"}, 200

    app.register_blueprint(bp_tardif)

    reponse = app.test_client().get("/api/route-nue")
    assert reponse.status_code == 403, (
        "une vue non déclarée a répondu : le hook doit être posé sur "
        "l'application, pas sur un blueprint en particulier"
    )
    assert "secret" not in reponse.get_data(as_text=True)


# Même refus pour une vue posée directement sur l'application, hors blueprint.
def test_garde_fou_couvre_les_vues_hors_blueprint(app):
    @app.get("/route-nue-hors-blueprint")
    def route_nue():
        return {"secret": "ne doit jamais sortir"}, 200

    reponse = app.test_client().get("/route-nue-hors-blueprint")
    assert reponse.status_code == 403
    assert "secret" not in reponse.get_data(as_text=True)


# Une vue nue déclarée @publique, elle, passe : le refus vient bien du
# marqueur manquant, et non du chemin ou du blueprint utilisé.
def test_garde_fou_laisse_passer_une_vue_publique(app):
    bp_tardif = Blueprint("tardif", __name__, url_prefix="/api")

    @bp_tardif.get("/route-publique")
    @publique
    def route_publique():
        return {"ok": True}, 200

    app.register_blueprint(bp_tardif)

    assert app.test_client().get("/api/route-publique").status_code == 200


# Vérifie que les secrets ne sont pas exposés dans les logs.
def test_aucun_secret_dans_les_logs(client, caplog):
    with caplog.at_level(logging.DEBUG):
        client.post("/api/inscription", json={
            "email": "fuite@x.fr", "mot_de_passe": "motdepassetressecret",
        })
        reponse = client.post("/api/connexion", json={
            "email": "fuite@x.fr", "mot_de_passe": "motdepassetressecret",
        })
        jeton = reponse.get_json()["jeton"]
        client.get("/api/moi", headers={"Authorization": f"Bearer {jeton}"})

    tout = caplog.text
    assert "motdepassetressecret" not in tout
    assert jeton not in tout
    assert "$argon2" not in tout


# Vérifie que l'identifiant de corrélation est présent dans les réponses.
def test_identifiant_de_correlation_present(client):
    reponse = client.get("/api/astronautes")
    assert "X-Request-ID" in reponse.headers


# Vérifie que le mode debug est désactivé en production.
def test_debug_desactive_en_production(app):
    # ConfigProd.DEBUG doit être False
    assert not app.config["DEBUG"]


# Vérifie que la réponse 401 ne divulgue jamais l'email de l'utilisateur.
def test_reponse_401_ne_cite_jamais_l_email(client):
    reponse = client.post("/api/connexion",
        json={"email": "cible@example.com", "mot_de_passe": "mauvais"})
    assert "cible@example.com" not in reponse.get_data(as_text=True)


# Vérifie que l'application refuse de démarrer en production sans clé secrète.
def test_production_refuse_de_demarrer_sans_cle(monkeypatch):
    monkeypatch.delenv("CLE_SECRETE_JWT", raising=False)
    with pytest.raises(RuntimeError, match="CLE_SECRETE_JWT"):
        creer_app(ConfigProduction)


# Vérifie que le mode debug est désactivé dans la configuration de production.
def test_production_a_le_debug_desactive():
    assert ConfigProduction.DEBUG is False


# Vérifie qu'aucun secret n'est codé en dur dans le code.
def test_aucun_secret_en_dur_dans_le_code():
    import pathlib, re
    motifs = [r"CLE_SECRETE.*=\s*['\"][^'\"]{8,}", r"secret\s*=\s*['\"][^'\"]{8,}"]
    for fichier in pathlib.Path("annuaire").rglob("*.py"):
        contenu = fichier.read_text()
        for motif in motifs:
            assert not re.search(motif, contenu, re.I), f"secret potentiel dans {fichier}"


# Vérifie que le fichier .env n'est pas chargé en production.
@pytest.mark.parametrize("environnement", ["production", " Production "])
def test_dotenv_non_charge_en_production(monkeypatch, environnement):
    appels = []
    monkeypatch.setattr(config, "load_dotenv", lambda: appels.append(True))
    monkeypatch.setenv("ENVIRONNEMENT", environnement)

    config.charger_dotenv()

    assert appels == []


# Vérifie que le fichier .env est chargé hors production.
@pytest.mark.parametrize("environnement", ["developpement", "test", None])
def test_dotenv_charge_hors_production(monkeypatch, environnement):
    appels = []
    monkeypatch.setattr(config, "load_dotenv", lambda: appels.append(True))
    if environnement is None:
        monkeypatch.delenv("ENVIRONNEMENT", raising=False)
    else:
        monkeypatch.setenv("ENVIRONNEMENT", environnement)

    config.charger_dotenv()

    assert appels == [True]
