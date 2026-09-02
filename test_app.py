import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import bdd
from app import app
from modeles import Astronaute, Base


@pytest.fixture
def client(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/test.db")
    bdd.FabriqueSession = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    with bdd.FabriqueSession() as session:
        session.add_all([
            Astronaute(nom="Neil Armstrong", role="commandant", mission="Apollo 11", nationalite="Etats-Unis", programme="Apollo"),
            Astronaute(nom="Alan Bean", role="pilote", mission="Apollo 12", nationalite="Etats-Unis", programme="Apollo"),
            Astronaute(nom="Peter Conrad", role="commandant", mission="Apollo 12", nationalite="Etats-Unis", programme="Apollo"),
        ])
        session.commit()

    return app.test_client()

# Url inexistante
def test_url_inexistante_renvoie_du_json(client):
    reponse = client.get("/api/nexistepas")
    assert reponse.status_code == 404
    assert reponse.get_json() is not None


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
    reponse = client.get("/api/astronautes?mission=Apollo 11")
    assert reponse.status_code == 200
    assert len(reponse.get_json()) == 1
    assert reponse.get_json()[0]["mission"] == "Apollo 11"


# Deux filtres combinés
def test_liste_filtres_combines(client):
    reponse = client.get("/api/astronautes?role=commandant&mission=Apollo 12")
    assert reponse.status_code == 200
    assert len(reponse.get_json()) == 1
    assert reponse.get_json()[0]["role"] == "commandant"
    assert reponse.get_json()[0]["mission"] == "Apollo 12"


# Filtre sans résultat : 200 et tableau vide
def test_liste_filtre_sans_resultat(client):
    reponse = client.get("/api/astronautes?mission=Apollo 99")
    assert reponse.status_code == 200
    assert len(reponse.get_json()) == 0


# Création valide : 201, en-tête Location présent, et relecture pour confirmer
def test_creation_valide(client):
    reponse = client.post(
        "/api/astronautes",
        json={"nom": "Edgar Mitchell", "role": "pilote", "mission": "Apollo 14", "nationalite": "Etats-Unis"},
    )
    assert reponse.status_code == 201
    assert "Location" in reponse.headers
    relecture = client.get(reponse.headers["Location"])
    assert relecture.status_code == 200
    assert relecture.get_json()["nom"] == "Edgar Mitchell"


# Création valide sans programme : 201
def test_creation_valide_sans_programme(client):
    reponse = client.post(
        "/api/astronautes",
        json={"nom": "Edgar Mitchell", "role": "pilote", "mission": "Apollo 14", "nationalite": "Etats-Unis"},
    )
    assert reponse.status_code == 201
    assert "Location" in reponse.headers
    relecture = client.get(reponse.headers["Location"])
    assert relecture.status_code == 200
    assert relecture.get_json()["programme"] == "Apollo"


# Champ manquant : 400
def test_creation_avec_champ_manquant(client):
    reponse = client.post(
        "/api/astronautes", json={"nom": "Edgar Mitchell", "mission": "Apollo 14", "nationalite": "Etats-Unis"}
    )
    assert reponse.status_code == 400


# Rôle invalide : 400
def test_creation_avec_role_invalide(client):
    reponse = client.post(
        "/api/astronautes",
        json={"nom": "Edgar Mitchell", "role": "cosmonaute", "mission": "Apollo 14", "nationalite": "Etats-Unis"},
    )
    assert reponse.status_code == 400


# Champ inconnu : 400
def test_creation_avec_champ_inconnu(client):
    reponse = client.post(
        "/api/astronautes",
        json={
            "nom": "Edgar Mitchell",
            "role": "pilote",
            "mission": "Apollo 14",
            "nationalite": "Etats-Unis",
            "salaire": "100000",
        },
    )
    assert reponse.status_code == 400


# Corps vide : 400
def test_creation_avec_corps_vide(client):
    reponse = client.post("/api/astronautes", json={})
    assert reponse.status_code == 400


# JSON mal formé
def test_corps_json_malforme(client):
    reponse = client.post(
        "/api/astronautes",
        data="{invalide}",
        content_type="application/json",
    )
    assert reponse.status_code == 400
    assert reponse.get_json() is not None


# Modification d'un astronaute existant
def test_put_remplace_reellement(client):
    reponse = client.put(
        "/api/astronautes/1",
        json={"nom": "Youri Gagarine", "role": "pilote", "mission": "Soyouz 1", "nationalite": "Russe"},
    )
    assert reponse.status_code == 200
    relecture = client.get("/api/astronautes/1")
    assert relecture.get_json()["nom"] == "Youri Gagarine"
    assert relecture.get_json()["programme"] == "Soyouz"


# PUT incomplet : 400
def test_put_modifie_avec_champs_incomplets(client):
    reponse = client.put(
        "/api/astronautes/1", json={"nom": "Youri Gagarine", "mission": "Soyouz 1", "nationalite": "Russe"}
    )
    assert reponse.status_code == 400


# PATCH partiel : seul le champ envoyé change, les autres sont intacts
def test_patch_ne_touche_que_les_champs_envoyes(client):
    reponse = client.patch(
        "/api/astronautes/1", json={"nom": "Youri Gagarine", "mission": "Soyouz 1", "nationalite": "Russe"}
    )
    assert reponse.status_code == 200
    relecture = client.get("/api/astronautes/1")
    assert relecture.get_json()["nom"] == "Youri Gagarine"
    assert relecture.get_json()["role"] == "commandant"
    assert relecture.get_json()["mission"] == "Soyouz 1"
    assert relecture.get_json()["nationalite"] == "Russe"
    assert relecture.get_json()["programme"] == "Soyouz"

# PATCH complet : tous les champs envoyés changent
def test_patch_modifie_avec_tous_les_champs(client):
    reponse = client.patch(
        "/api/astronautes/1",
        json={"nom": "Youri Gagarine", "role": "commandant", "mission": "Soyouz 1", "nationalite": "Russe"},
    )
    assert reponse.status_code == 200
    relecture = client.get("/api/astronautes/1")
    assert relecture.get_json()["nom"] == "Youri Gagarine"
    assert relecture.get_json()["role"] == "commandant"
    assert relecture.get_json()["mission"] == "Soyouz 1"
    assert relecture.get_json()["nationalite"] == "Russe"
    assert relecture.get_json()["programme"] == "Soyouz"

# PATCH avec rôle invalide : 400
def test_patch_modifie_avec_role_invalide(client):
    reponse = client.patch(
        "/api/astronautes/1", json={"nom": "Modifié", "role": "cosmonaute"}
    )
    assert reponse.status_code == 400


# PATCH avec corps vide : 400
def test_patch_corps_vide_renvoie_400(client):
    reponse = client.patch("/api/astronautes/1", json={})
    assert reponse.status_code == 400


# Suppression : 204, puis un GET qui renvoie 404
def test_suppression_astronaute(client):
    reponse = client.delete("/api/astronautes/1")
    assert reponse.status_code == 204
    relecture = client.get("/api/astronautes/1")
    assert relecture.status_code == 404


# Suppression d'un inexistant : 404
def test_suppression_inexistant(client):
    reponse = client.delete("/api/astronautes/100")
    assert reponse.status_code == 404


# Decalage apres une suppression
def test_suppression_ne_decale_pas_les_identifiants(client):
    client.delete("/api/astronautes/1")
    reponse = client.get("/api/astronautes/2")
    assert reponse.get_json()["nom"] == "Alan Bean"
