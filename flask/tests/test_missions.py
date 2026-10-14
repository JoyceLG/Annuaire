"""Tests de l'API des missions."""

import pytest

from annuaire.donnees import missions as donnees_missions
from annuaire.erreurs import MissionDejaExistante


# Liste complète
def test_liste_renvoie_toutes_les_missions(client):
    reponse = client.get("/api/missions")
    assert reponse.status_code == 200
    assert len(reponse.get_json()) == 3


# Filtre par programme
def test_liste_missions_filtre_par_programme(client):
    reponse = client.get("/api/missions?programme=Apollo")
    assert reponse.status_code == 200
    assert len(reponse.get_json()) == 3


# Filtre sans résultat : 200 et tableau vide
def test_liste_missions_filtre_sans_resultat(client):
    reponse = client.get("/api/missions?programme=Gemini")
    assert reponse.status_code == 200
    assert reponse.get_json() == []


# Lecture d'une mission existante
def test_lire_mission_existante(client):
    reponse = client.get("/api/missions/2")
    assert reponse.status_code == 200
    assert reponse.get_json() == {
        "id": 2,
        "nom": "Apollo 12",
        "programme": "Apollo",
        "annee": 1969,
    }


# Lecture d'une mission inexistante
def test_lire_mission_inexistante(client):
    reponse = client.get("/api/missions/999")
    assert reponse.status_code == 404
    assert "erreur" in reponse.get_json()


# L'identifiant 0 est refusé par le convertisseur <int(min=1)> avant la vue
def test_lire_mission_id_zero_renvoie_404(client):
    reponse = client.get("/api/missions/0")
    assert reponse.status_code == 404


# Équipage d'une mission
def test_liste_astronautes_d_une_mission(client):
    reponse = client.get("/api/missions/2/astronautes")
    assert reponse.status_code == 200
    equipage = reponse.get_json()
    assert len(equipage) == 2
    assert {a["nom"] for a in equipage} == {"Alan Bean", "Peter Conrad"}
    assert all(a["mission_id"] == 2 for a in equipage)


# Mission sans équipage : 200 et tableau vide
def test_liste_astronautes_mission_sans_equipage(client):
    reponse = client.get("/api/missions/3/astronautes")
    assert reponse.status_code == 200
    assert reponse.get_json() == []


# Équipage d'une mission inexistante : 404
def test_liste_astronautes_mission_inexistante(client):
    reponse = client.get("/api/missions/999/astronautes")
    assert reponse.status_code == 404
    assert "erreur" in reponse.get_json()


# Création valide : 201, en-tête Location présent, et relecture pour confirmer
def test_creation_mission_valide(client, entetes_auth):
    reponse = client.post(
        "/api/missions", json={"nom": "Apollo 13", "annee": 1970}, headers=entetes_auth
    )
    assert reponse.status_code == 201
    assert "Location" in reponse.headers
    relecture = client.get(reponse.headers["Location"])
    assert relecture.status_code == 200
    assert relecture.get_json()["nom"] == "Apollo 13"
    assert relecture.get_json()["annee"] == 1970


# Le programme est déduit du nom, il n'est pas fourni par le client
def test_creation_mission_deduit_le_programme(client, entetes_auth):
    reponse = client.post(
        "/api/missions", json={"nom": "Vostok 1", "annee": 1961}, headers=entetes_auth
    )
    assert reponse.status_code == 201
    assert reponse.get_json()["programme"] == "Vostok"


# ... et le fournir quand même est donc un champ inconnu : 400
def test_creation_mission_refuse_le_programme_fourni(client, entetes_auth):
    reponse = client.post(
        "/api/missions",
        json={"nom": "Gemini 4", "programme": "Gemini", "annee": 1965},
        headers=entetes_auth,
    )
    assert reponse.status_code == 400
    assert (
        "Extra inputs are not permitted" in reponse.get_json()["details"]["programme"]
    )


# Nom déjà pris : 400 (contrainte unique sur Mission.nom)
def test_creation_mission_nom_deja_existant(client, entetes_auth):
    reponse = client.post(
        "/api/missions", json={"nom": "Apollo 11", "annee": 1969}, headers=entetes_auth
    )
    assert reponse.status_code == 409


# L'année est un entier, pas une chaîne : 400
def test_creation_mission_annee_non_entiere(client, entetes_auth):
    reponse = client.post(
        "/api/missions", json={"nom": "Gemini 4", "annee": "1965"}, headers=entetes_auth
    )
    assert reponse.status_code == 400
    assert "annee" in reponse.get_json()["details"]


# L'année est un entier, pas une chaîne : 400
def test_creation_mission_annee_booleen(client, entetes_auth):
    reponse = client.post(
        "/api/missions", json={"nom": "Gemini 4", "annee": True}, headers=entetes_auth
    )
    assert reponse.status_code == 400
    assert "annee" in reponse.get_json()["details"]


# Champ manquant : 400
def test_creation_mission_avec_champ_manquant(client, entetes_auth):
    reponse = client.post(
        "/api/missions", json={"nom": "Gemini 4"}, headers=entetes_auth
    )
    assert reponse.status_code == 400
    assert reponse.get_json()["details"]["annee"] == "Field required"


# Nom vide : 400
def test_creation_mission_avec_nom_vide(client, entetes_auth):
    reponse = client.post(
        "/api/missions", json={"nom": "   ", "annee": 1965}, headers=entetes_auth
    )
    assert reponse.status_code == 400


# Champ inconnu : 400
def test_creation_mission_avec_champ_inconnu(client, entetes_auth):
    reponse = client.post(
        "/api/missions",
        json={"nom": "Gemini 4", "annee": 1965, "cout": 500},
        headers=entetes_auth,
    )
    assert reponse.status_code == 400


# Corps vide : 400
def test_creation_mission_avec_corps_vide(client, entetes_auth):
    reponse = client.post("/api/missions", json={}, headers=entetes_auth)
    assert reponse.status_code == 400


# JSON mal formé : 400 et réponse quand même en JSON
def test_creation_mission_corps_json_malforme(client, entetes_auth):
    reponse = client.post(
        "/api/missions",
        data="{invalide}",
        content_type="application/json",
        headers=entetes_auth,
    )
    assert reponse.status_code == 400
    assert reponse.get_json() is not None


# Une création est bien visible dans la liste
def test_creation_mission_apparait_dans_la_liste(client, entetes_auth):
    client.post(
        "/api/missions", json={"nom": "Apollo 13", "annee": 1970}, headers=entetes_auth
    )
    reponse = client.get("/api/missions")
    assert len(reponse.get_json()) == 4


# Suppression d'une mission sans équipage : 204, puis un GET qui renvoie 404
def test_suppression_mission_sans_equipage(client, entetes_auth):
    reponse = client.delete("/api/missions/3", headers=entetes_auth)
    assert reponse.status_code == 204
    assert reponse.get_data() == b""
    relecture = client.get("/api/missions/3")
    assert relecture.status_code == 404


# Suppression d'une mission inexistante : 404
def test_suppression_mission_inexistante(client, entetes_auth):
    reponse = client.delete("/api/missions/999", headers=entetes_auth)
    assert reponse.status_code == 404


# Suppression d'une mission avec équipage : 409
def test_suppression_mission_avec_equipage(client, entetes_auth):
    reponse = client.delete("/api/missions/2", headers=entetes_auth)
    assert reponse.status_code == 409


# Garde-fou base de données : le doublon n'est plus détecté en amont par la
# validation, c'est la contrainte unique sur Mission.nom qui tranche.
def test_creer_mission_doublon_leve_mission_deja_existante(session):
    with pytest.raises(MissionDejaExistante):
        donnees_missions.creer(session, {"nom": "Apollo 11", "annee": 1969})

    # le rollback a bien eu lieu : la session reste utilisable
    assert len(donnees_missions.lister(session)) == 3


# Le flush renseigne l'identifiant avant que la route ne construise Location
def test_creer_mission_renseigne_l_identifiant_avant_le_commit(session):
    mission = donnees_missions.creer(session, {"nom": "Apollo 13", "annee": 1970})
    assert mission.id is not None
    session.commit()


# Test de relecture puis mise à jour d'un astronaute via PUT
def test_relecture_puis_put_fonctionne(client, entetes_auth):
    lu = client.get("/api/astronautes/1").get_json()
    renvoi = {k: v for k, v in lu.items() if k != "id"}
    assert (
        client.put("/api/astronautes/1", json=renvoi, headers=entetes_auth).status_code
        == 200
    )


def test_annee_en_chaine_est_refusee(client, entetes_auth):
    reponse = client.post(
        "/api/missions",
        json={"nom": "Apollo 18", "annee": "1973"},
        headers=entetes_auth,
    )
    assert reponse.status_code == 400


def test_nom_avec_espaces_est_nettoye(client, entetes_auth):
    reponse = client.post(
        "/api/astronautes",
        json={
            "nom": "  Michael Collins  ",
            "role": "pilote",
            "nationalite": "Etats-Unis",
            "mission_id": 1,
        },
        headers=entetes_auth,
    )
    assert reponse.get_json()["nom"] == "Michael Collins"
