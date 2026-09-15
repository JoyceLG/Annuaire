"""Validation des corps de requête : les champs envoyés sont vérifiés un à un."""


# Url inexistante
def test_url_inexistante_renvoie_du_json(client):
    reponse = client.get("/api/nexistepas")
    assert reponse.status_code == 404
    assert reponse.get_json() is not None


# Nom vide : 400 (et l'astronaute n'est pas modifié)
def test_patch_nom_vide_renvoie_400(client, entetes_auth):
    reponse = client.patch("/api/astronautes/1", json={"nom": ""}, headers=entetes_auth)
    assert reponse.status_code == 400
    assert "nom" in reponse.get_json()["details"]
    assert client.get("/api/astronautes/1").get_json()["nom"] == "Neil Armstrong"


# Nom composé uniquement d'espaces : 400 (le nettoyage laisse une chaîne vide)
def test_patch_nom_espaces_renvoie_400(client, entetes_auth):
    reponse = client.patch(
        "/api/astronautes/1", json={"nom": "   "}, headers=entetes_auth
    )
    assert reponse.status_code == 400
    assert "nom" in reponse.get_json()["details"]
    assert client.get("/api/astronautes/1").get_json()["nom"] == "Neil Armstrong"


# Nationalité vide : 400 (et l'astronaute n'est pas modifié)
def test_patch_nationalite_vide_renvoie_400(client, entetes_auth):
    reponse = client.patch(
        "/api/astronautes/1", json={"nationalite": ""}, headers=entetes_auth
    )
    assert reponse.status_code == 400
    assert "nationalite" in reponse.get_json()["details"]
    assert client.get("/api/astronautes/1").get_json()["nationalite"] == "Etats-Unis"


# mission_id à 0 : 400, refusé par la validation (un identifiant vaut au moins 1)
def test_patch_mission_id_zero_renvoie_400(client, entetes_auth):
    reponse = client.patch(
        "/api/astronautes/1", json={"mission_id": 0}, headers=entetes_auth
    )
    assert reponse.status_code == 400
    assert "mission_id" in reponse.get_json()["details"]
    assert client.get("/api/astronautes/1").get_json()["mission_id"] == 1


# mission_id valide mais inexistant : 404, pas un rattachement silencieux
def test_patch_mission_id_inexistant_renvoie_404(client, entetes_auth):
    reponse = client.patch(
        "/api/astronautes/1", json={"mission_id": 999}, headers=entetes_auth
    )
    assert reponse.status_code == 404
    assert "erreur" in reponse.get_json()
    assert client.get("/api/astronautes/1").get_json()["mission_id"] == 1


# Même garde-fou côté PUT
def test_put_mission_id_inexistant_renvoie_404(client, entetes_auth):
    reponse = client.put(
        "/api/astronautes/1",
        json={
            "nom": "Neil Armstrong",
            "role": "commandant",
            "mission_id": 999,
            "nationalite": "Etats-Unis",
        },
        headers=entetes_auth,
    )
    assert reponse.status_code == 404
    assert client.get("/api/astronautes/1").get_json()["mission_id"] == 1


# Année antérieure à 1900 : 400 (et la mission n'est pas modifiée)
def test_patch_mission_annee_trop_ancienne_renvoie_400(client, entetes_auth):
    reponse = client.patch(
        "/api/missions/1", json={"annee": 1500}, headers=entetes_auth
    )
    assert reponse.status_code == 400
    assert "annee" in reponse.get_json()["details"]
    assert client.get("/api/missions/1").get_json()["annee"] == 1969


# Nom de mission vide : 400 (même règle qu'à la création)
def test_patch_mission_nom_vide_renvoie_400(client, entetes_auth):
    reponse = client.patch("/api/missions/1", json={"nom": "   "}, headers=entetes_auth)
    assert reponse.status_code == 400
    assert "nom" in reponse.get_json()["details"]
    assert client.get("/api/missions/1").get_json()["nom"] == "Apollo 11"
