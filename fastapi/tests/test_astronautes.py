"""Tests de l'API des astronautes.

FastAPI répond 422 quand le corps ou les
paramètres ne passent pas la validation Pydantic.
"""

EDGAR_MITCHELL = {
    "nom": "Edgar Mitchell",
    "role": "pilote",
    "nationalite": "Etats-Unis",
}


# Liste complète : les deux astronautes du jeu de démonstration
def test_liste_renvoie_tous_les_astronautes(client):
    reponse = client.get("/api/astronautes")
    assert reponse.status_code == 200
    assert [a["nom"] for a in reponse.json()] == ["Neil Armstrong", "Alan Bean"]


# Le champ interne des données ne sort jamais dans la réponse
def test_liste_n_expose_pas_la_note_interne(client):
    reponse = client.get("/api/astronautes")
    assert all("note_interne" not in a for a in reponse.json())


# Lecture d'un astronaute existant
def test_lire_astronaute_existant(client):
    reponse = client.get("/api/astronautes/1")
    assert reponse.status_code == 200
    assert reponse.json() == {
        "id": 1,
        "nom": "Neil Armstrong",
        "role": "commandant",
        "nationalite": "Etats-Unis",
    }


# Lecture d'un astronaute inexistant : 404 avec un message d'erreur
def test_lire_astronaute_inexistant(client):
    reponse = client.get("/api/astronautes/999")
    assert reponse.status_code == 404
    assert "erreur" in reponse.json()


# Identifiant non entier : 422
def test_lire_astronaute_avec_id_non_entier(client):
    reponse = client.get("/api/astronautes/armstrong")
    assert reponse.status_code == 422


# Filtre par rôle
def test_liste_filtre_par_role(client):
    reponse = client.get("/api/astronautes?role=commandant")
    assert reponse.status_code == 200
    assert [a["nom"] for a in reponse.json()] == ["Neil Armstrong"]


# Filtre sans résultat : 200 et tableau vide
def test_liste_filtre_sans_resultat(client):
    reponse = client.get("/api/astronautes?role=specialiste")
    assert reponse.status_code == 200
    assert reponse.json() == []


# Création valide : 201, en-tête Location présent, et relecture pour confirmer
def test_creation_valide(client):
    reponse = client.post("/api/astronautes", json=EDGAR_MITCHELL)
    assert reponse.status_code == 201
    assert reponse.json() == {"id": 3, **EDGAR_MITCHELL}
    relecture = client.get(reponse.headers["Location"])
    assert relecture.status_code == 200
    assert relecture.json()["nom"] == "Edgar Mitchell"


# Deux créations successives reçoivent deux identifiants distincts
def test_creations_successives_ont_des_identifiants_distincts(client):
    premier = client.post("/api/astronautes", json=EDGAR_MITCHELL)
    second = client.post(
        "/api/astronautes", json={**EDGAR_MITCHELL, "nom": "Alan Shepard"}
    )
    assert premier.json()["id"] != second.json()["id"]
    assert len(client.get("/api/astronautes").json()) == 4


# Un créé ne reçoit pas l'identifiant déjà utilisé par un supprimé
def test_creation_apres_suppression(client):
    client.delete("/api/astronautes/2")
    reponse = client.post("/api/astronautes", json=EDGAR_MITCHELL)
    assert reponse.json()["id"] != 2


# Créer, supprimer, recréer : le recréé a un nouvel id, l'ancien reste introuvable
def test_creer_supprimer_recreer(client):
    cree = client.post("/api/astronautes", json=EDGAR_MITCHELL).json()["id"]
    assert client.delete(f"/api/astronautes/{cree}").status_code == 204

    recree = client.post("/api/astronautes", json=EDGAR_MITCHELL).json()["id"]
    assert recree != cree
    assert client.get(f"/api/astronautes/{cree}").status_code == 404
    assert client.get(f"/api/astronautes/{recree}").status_code == 200


# Champ manquant : 422, et rien n'est créé
def test_creation_avec_champ_manquant(client):
    reponse = client.post(
        "/api/astronautes",
        json={"nom": "Edgar Mitchell", "nationalite": "Etats-Unis"},
    )
    assert reponse.status_code == 422
    assert len(client.get("/api/astronautes").json()) == 2


# Rôle invalide : 422
def test_creation_avec_role_invalide(client):
    reponse = client.post(
        "/api/astronautes",
        json={**EDGAR_MITCHELL, "role": "cosmonaute"},
    )
    assert reponse.status_code == 422


# Champ inconnu : 422
def test_creation_avec_champ_inconnu(client):
    reponse = client.post(
        "/api/astronautes",
        json={**EDGAR_MITCHELL, "salaire": "100000"},
    )
    assert reponse.status_code == 422


# Mode strict : un nombre n'est pas converti en texte
def test_creation_avec_nom_numerique(client):
    reponse = client.post("/api/astronautes", json={**EDGAR_MITCHELL, "nom": 42})
    assert reponse.status_code == 422


# Nom fait uniquement d'espaces : 422
def test_creation_avec_nom_vide(client):
    reponse = client.post("/api/astronautes", json={**EDGAR_MITCHELL, "nom": "   "})
    assert reponse.status_code == 422


# Corps vide : 422
def test_creation_avec_corps_vide(client):
    reponse = client.post("/api/astronautes", json={})
    assert reponse.status_code == 422


# JSON mal formé : 422 avec un corps JSON
def test_corps_json_malforme(client):
    reponse = client.post(
        "/api/astronautes",
        content="{invalide}",
        headers={"Content-Type": "application/json"},
    )
    assert reponse.status_code == 422
    assert "detail" in reponse.json()


# Modification d'un astronaute existant
def test_put_remplace_reellement(client):
    reponse = client.put("/api/astronautes/1", json=EDGAR_MITCHELL)
    assert reponse.status_code == 200
    relecture = client.get("/api/astronautes/1")
    assert relecture.json() == {"id": 1, **EDGAR_MITCHELL}


# PUT incomplet : 422, et l'astronaute est intact
def test_put_avec_champs_incomplets(client):
    reponse = client.put(
        "/api/astronautes/1",
        json={"nom": "Modifie", "nationalite": "Etats-Unis"},
    )
    assert reponse.status_code == 422
    assert client.get("/api/astronautes/1").json()["nom"] == "Neil Armstrong"


# PUT sur un inexistant : 404
def test_put_inexistant(client):
    reponse = client.put("/api/astronautes/999", json=EDGAR_MITCHELL)
    assert reponse.status_code == 404


# PATCH partiel : seul le champ envoyé change, les autres sont intacts
def test_patch_ne_touche_que_les_champs_envoyes(client):
    reponse = client.patch("/api/astronautes/1", json={"nom": "Modifie"})
    assert reponse.status_code == 200
    attendu = {
        "id": 1,
        "nom": "Modifie",
        "role": "commandant",
        "nationalite": "Etats-Unis",
    }
    assert reponse.json() == attendu
    assert client.get("/api/astronautes/1").json() == attendu


# PATCH complet : tous les champs envoyés changent
def test_patch_modifie_avec_tous_les_champs(client):
    reponse = client.patch("/api/astronautes/1", json=EDGAR_MITCHELL)
    assert reponse.status_code == 200
    assert client.get("/api/astronautes/1").json() == {"id": 1, **EDGAR_MITCHELL}


# PATCH avec rôle invalide : 422, et l'astronaute est intact
def test_patch_avec_role_invalide(client):
    reponse = client.patch(
        "/api/astronautes/1",
        json={"nom": "Modifie", "role": "cosmonaute"},
    )
    assert reponse.status_code == 422
    assert client.get("/api/astronautes/1").json()["nom"] == "Neil Armstrong"


# PATCH avec corps vide : 422, il n'y a rien à modifier
def test_patch_corps_vide(client):
    reponse = client.patch("/api/astronautes/1", json={})
    assert reponse.status_code == 422


# PATCH avec un champ à null : 422, et l'astronaute est intact
def test_patch_champ_null(client):
    reponse = client.patch("/api/astronautes/1", json={"nom": None})
    assert reponse.status_code == 422
    assert client.get("/api/astronautes/1").json()["nom"] == "Neil Armstrong"


# PATCH sur un inexistant : 404
def test_patch_inexistant(client):
    reponse = client.patch("/api/astronautes/999", json={"nom": "Modifie"})
    assert reponse.status_code == 404


# Suppression : 204 sans corps, puis un GET qui renvoie 404
def test_suppression_astronaute(client):
    reponse = client.delete("/api/astronautes/1")
    assert reponse.status_code == 204
    assert reponse.content == b""
    assert client.get("/api/astronautes/1").status_code == 404


# Suppression d'un inexistant : 404
def test_suppression_inexistant(client):
    reponse = client.delete("/api/astronautes/100")
    assert reponse.status_code == 404


# Une suppression ne décale pas les identifiants des autres
def test_suppression_ne_decale_pas_les_identifiants(client):
    client.delete("/api/astronautes/1")
    reponse = client.get("/api/astronautes/2")
    assert reponse.json()["nom"] == "Alan Bean"
