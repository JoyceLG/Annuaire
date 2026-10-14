"""Tests de l'API des astronautes."""

from sqlalchemy import event


# Test pour vérifier l'absence de problème N+1 lors de la récupération de la liste des astronautes
def test_liste_ne_fait_pas_de_n_plus_1(client, moteur):
    requetes = []
    event.listen(moteur, "before_cursor_execute", lambda *a: requetes.append(a[2]))
    client.get("/api/missions/1/astronautes")
    assert len(requetes) <= 2


# Tests de l'API des astronautes
def test_liste_renvoie_tous_les_astronautes(client):
    reponse = client.get("/api/astronautes")
    assert reponse.status_code == 200
    assert len(reponse.get_json()) == 3


# Lecture d'un astronaute existant
def test_lire_astronaute_existant(client):
    reponse = client.get("/api/astronautes/1")
    assert reponse.status_code == 200
    assert reponse.get_json()["nom"] == "Neil Armstrong"


# Lecture d'un astronaute inexistant
def test_lire_astronaute_inexistant(client):
    reponse = client.get("/api/astronautes/999")
    assert reponse.status_code == 404
    assert "erreur" in reponse.get_json()


# Filtre par rôle
def test_liste_filtre_par_role(client):
    reponse = client.get("/api/astronautes?role=commandant")
    assert reponse.status_code == 200
    assert len(reponse.get_json()) == 2
    assert reponse.get_json()[0]["role"] == "commandant"


# Filtre par mission
def test_liste_filtre_par_mission(client):
    reponse = client.get("/api/astronautes?mission_id=1")
    assert reponse.status_code == 200
    assert len(reponse.get_json()) == 1
    assert reponse.get_json()[0]["mission_id"] == 1


# Deux filtres combinés
def test_liste_filtres_combines(client):
    reponse = client.get("/api/astronautes?role=commandant&mission_id=2")
    assert reponse.status_code == 200
    assert len(reponse.get_json()) == 1
    assert reponse.get_json()[0]["role"] == "commandant"
    assert reponse.get_json()[0]["mission_id"] == 2


# Filtre sans résultat : 200 et tableau vide
def test_liste_filtre_sans_resultat(client):
    reponse = client.get("/api/astronautes?mission_id=99")
    assert reponse.status_code == 200
    assert len(reponse.get_json()) == 0


# Filtre avec mission_id en string : 400
def test_liste_filtre_avec_mission_id_en_string(client):
    reponse = client.get("/api/astronautes?mission_id=Apollo 99")
    assert reponse.status_code == 400


# Création valide : 201, en-tête Location présent, et relecture pour confirmer
def test_creation_valide(client, entetes_auth):
    reponse = client.post(
        "/api/astronautes",
        json={
            "nom": "Edgar Mitchell",
            "role": "pilote",
            "mission_id": 1,
            "nationalite": "Etats-Unis",
        },
        headers=entetes_auth,
    )
    assert reponse.status_code == 201
    assert "Location" in reponse.headers
    relecture = client.get(reponse.headers["Location"])
    assert relecture.status_code == 200
    assert relecture.get_json()["nom"] == "Edgar Mitchell"


# Champ manquant : 400
def test_creation_avec_champ_manquant(client, entetes_auth):
    reponse = client.post(
        "/api/astronautes",
        json={
            "nom": "Edgar Mitchell",
            "mission_id": 3,
            "nationalite": "Etats-Unis",
        },
        headers=entetes_auth,
    )
    assert reponse.status_code == 400


# Rôle invalide : 400
def test_creation_avec_role_invalide(client, entetes_auth):
    reponse = client.post(
        "/api/astronautes",
        json={
            "nom": "Edgar Mitchell",
            "role": "cosmonaute",
            "mission_id": 3,
            "nationalite": "Etats-Unis",
        },
        headers=entetes_auth,
    )
    assert reponse.status_code == 400


# Champ inconnu : 400
def test_creation_avec_champ_inconnu(client, entetes_auth):
    reponse = client.post(
        "/api/astronautes",
        json={
            "nom": "Edgar Mitchell",
            "role": "pilote",
            "mission_id": 3,
            "nationalite": "Etats-Unis",
            "salaire": "100000",
        },
        headers=entetes_auth,
    )
    assert reponse.status_code == 400


# Mission inconnue : 404
def test_creation_avec_mission_inconnue(client, entetes_auth):
    reponse = client.post(
        "/api/astronautes",
        json={
            "nom": "Edgar Mitchell",
            "role": "pilote",
            "mission_id": 999,
            "nationalite": "Etats-Unis",
        },
        headers=entetes_auth,
    )
    assert reponse.status_code == 404


# Mission en format complet : 400
def test_creation_avec_mission_mal_formatee(client, entetes_auth):
    reponse = client.post(
        "/api/astronautes",
        json={
            "nom": "Edgar Mitchell",
            "role": "pilote",
            "mission_id": "Apollo 14",
            "nationalite": "Etats-Unis",
        },
        headers=entetes_auth,
    )
    assert reponse.status_code == 400


# Corps vide : 400
def test_creation_avec_corps_vide(client, entetes_auth):
    reponse = client.post("/api/astronautes", json={}, headers=entetes_auth)
    assert reponse.status_code == 400


# JSON mal formé
def test_corps_json_malforme(client, entetes_auth):
    reponse = client.post(
        "/api/astronautes",
        data="{invalide}",
        content_type="application/json",
        headers=entetes_auth,
    )
    assert reponse.status_code == 400
    assert reponse.get_json() is not None


# Modification d'un astronaute existant
def test_put_remplace_reellement(client, entetes_auth):
    reponse = client.put(
        "/api/astronautes/1",
        json={
            "nom": "Modifie",
            "role": "pilote",
            "mission_id": 1,
            "nationalite": "Etats-Unis",
        },
        headers=entetes_auth,
    )
    assert reponse.status_code == 200
    relecture = client.get("/api/astronautes/1")
    assert relecture.get_json()["nom"] == "Modifie"


# PUT incomplet : 400
def test_put_modifie_avec_champs_incomplets(client, entetes_auth):
    reponse = client.put(
        "/api/astronautes/1",
        json={"nom": "Modifie", "mission_id": 1, "nationalite": "Etats-Unis"},
        headers=entetes_auth,
    )
    assert reponse.status_code == 400


# PATCH partiel : seul le champ envoyé change, les autres sont intacts
def test_patch_ne_touche_que_les_champs_envoyes(client, entetes_auth):
    reponse = client.patch(
        "/api/astronautes/1",
        json={"nom": "Modifie", "mission_id": 1, "nationalite": "Etats-Unis"},
        headers=entetes_auth,
    )
    assert reponse.status_code == 200
    relecture = client.get("/api/astronautes/1")
    assert relecture.get_json()["nom"] == "Modifie"
    assert relecture.get_json()["role"] == "commandant"
    assert relecture.get_json()["mission_id"] == 1
    assert relecture.get_json()["nationalite"] == "Etats-Unis"


# PATCH complet : tous les champs envoyés changent
def test_patch_modifie_avec_tous_les_champs(client, entetes_auth):
    reponse = client.patch(
        "/api/astronautes/1",
        json={
            "nom": "Modifie",
            "role": "commandant",
            "mission_id": 1,
            "nationalite": "Etats-Unis",
        },
        headers=entetes_auth,
    )
    assert reponse.status_code == 200
    relecture = client.get("/api/astronautes/1")
    assert relecture.get_json()["nom"] == "Modifie"
    assert relecture.get_json()["role"] == "commandant"
    assert relecture.get_json()["mission_id"] == 1
    assert relecture.get_json()["nationalite"] == "Etats-Unis"


# PATCH avec rôle invalide : 400
def test_patch_modifie_avec_role_invalide(client, entetes_auth):
    reponse = client.patch(
        "/api/astronautes/1",
        json={"nom": "Modifié", "role": "cosmonaute"},
        headers=entetes_auth,
    )
    assert reponse.status_code == 400


# PATCH avec corps vide : 400
def test_patch_corps_vide_renvoie_400(client, entetes_auth):
    reponse = client.patch("/api/astronautes/1", json={}, headers=entetes_auth)
    assert reponse.status_code == 400


# Suppression : 204, puis un GET qui renvoie 404
def test_suppression_astronaute(client, entetes_auth):
    reponse = client.delete("/api/astronautes/1", headers=entetes_auth)
    assert reponse.status_code == 204
    relecture = client.get("/api/astronautes/1", headers=entetes_auth)
    assert relecture.status_code == 404


# Suppression d'un inexistant : 404
def test_suppression_inexistant(client, entetes_auth):
    reponse = client.delete("/api/astronautes/100", headers=entetes_auth)
    assert reponse.status_code == 404


# Decalage apres une suppression
def test_suppression_ne_decale_pas_les_identifiants(client, entetes_auth):
    client.delete("/api/astronautes/1", headers=entetes_auth)
    reponse = client.get("/api/astronautes/2", headers=entetes_auth)
    assert reponse.get_json()["nom"] == "Alan Bean"
