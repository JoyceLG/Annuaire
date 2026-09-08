import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

import bdd
import donnees
from app import app
from erreurs import MissionDejaExistante
from modeles import Astronaute, Base, Mission


@pytest.fixture
def client(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path}/test.db")
    monkeypatch.setattr(bdd, "engine", engine)
    monkeypatch.setattr(bdd, "FabriqueSession", sessionmaker(bind=engine))
    Base.metadata.create_all(engine)

    with bdd.FabriqueSession() as session:
        apollo_11 = Mission(nom="Apollo 11", programme="Apollo", annee=1969)
        apollo_12 = Mission(nom="Apollo 12", programme="Apollo", annee=1969)
        apollo_17 = Mission(nom="Apollo 17", programme="Apollo", annee=1972)

        session.add_all(
            [
                apollo_11,
                apollo_12,
                apollo_17,
                Astronaute(
                    nom="Neil Armstrong",
                    role="commandant",
                    nationalite="Etats-Unis",
                    mission=apollo_11,
                ),
                Astronaute(
                    nom="Alan Bean",
                    role="pilote",
                    nationalite="Etats-Unis",
                    mission=apollo_12,
                ),
                Astronaute(
                    nom="Peter Conrad",
                    role="commandant",
                    nationalite="Etats-Unis",
                    mission=apollo_12,
                ),
            ]
        )
        session.commit()

    return app.test_client()


# Test pour vérifier l'absence de problème N+1 lors de la récupération de la liste des astronautes
def test_liste_ne_fait_pas_de_n_plus_1(client):
    requetes = []
    event.listen(bdd.engine, "before_cursor_execute", lambda *a: requetes.append(a[2]))
    client.get("/api/missions/1/astronautes")
    assert len(requetes) <= 2


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
def test_creation_valide(client):
    reponse = client.post(
        "/api/astronautes",
        json={
            "nom": "Edgar Mitchell",
            "role": "pilote",
            "mission_id": 1,
            "nationalite": "Etats-Unis",
        },
    )
    assert reponse.status_code == 201
    assert "Location" in reponse.headers
    relecture = client.get(reponse.headers["Location"])
    assert relecture.status_code == 200
    assert relecture.get_json()["nom"] == "Edgar Mitchell"


# Champ manquant : 400
def test_creation_avec_champ_manquant(client):
    reponse = client.post(
        "/api/astronautes",
        json={
            "nom": "Edgar Mitchell",
            "mission_id": 3,
            "nationalite": "Etats-Unis",
        },
    )
    assert reponse.status_code == 400


# Rôle invalide : 400
def test_creation_avec_role_invalide(client):
    reponse = client.post(
        "/api/astronautes",
        json={
            "nom": "Edgar Mitchell",
            "role": "cosmonaute",
            "mission_id": 3,
            "nationalite": "Etats-Unis",
        },
    )
    assert reponse.status_code == 400


# Champ inconnu : 400
def test_creation_avec_champ_inconnu(client):
    reponse = client.post(
        "/api/astronautes",
        json={
            "nom": "Edgar Mitchell",
            "role": "pilote",
            "mission_id": 3,
            "nationalite": "Etats-Unis",
            "salaire": "100000",
        },
    )
    assert reponse.status_code == 400
    

# Mission inconnue : 404
def test_creation_avec_mission_inconnue(client):
    reponse = client.post(
        "/api/astronautes",
        json={
            "nom": "Edgar Mitchell",
            "role": "pilote",
            "mission_id": 999,
            "nationalite": "Etats-Unis",
        },
    )
    assert reponse.status_code == 404
    
# Mission en format complet : 400
def test_creation_avec_mission_mal_formatee(client):
    reponse = client.post(
        "/api/astronautes",
        json={
            "nom": "Edgar Mitchell",
            "role": "pilote",
            "mission_id": "Apollo 14",
            "nationalite": "Etats-Unis",
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
        json={
            "nom": "Modifie",
            "role": "pilote",
            "mission_id": 1,
            "nationalite": "Etats-Unis",
        },
    )
    assert reponse.status_code == 200
    relecture = client.get("/api/astronautes/1")
    assert relecture.get_json()["nom"] == "Modifie"


# PUT incomplet : 400
def test_put_modifie_avec_champs_incomplets(client):
    reponse = client.put(
        "/api/astronautes/1",
        json={"nom": "Modifie", "mission_id": 1, "nationalite": "Etats-Unis"},
    )
    assert reponse.status_code == 400


# PATCH partiel : seul le champ envoyé change, les autres sont intacts
def test_patch_ne_touche_que_les_champs_envoyes(client):
    reponse = client.patch(
        "/api/astronautes/1",
        json={"nom": "Modifie", "mission_id": 1, "nationalite": "Etats-Unis"},
    )
    assert reponse.status_code == 200
    relecture = client.get("/api/astronautes/1")
    assert relecture.get_json()["nom"] == "Modifie"
    assert relecture.get_json()["role"] == "commandant"
    assert relecture.get_json()["mission_id"] == 1
    assert relecture.get_json()["nationalite"] == "Etats-Unis"


# PATCH complet : tous les champs envoyés changent
def test_patch_modifie_avec_tous_les_champs(client):
    reponse = client.patch(
        "/api/astronautes/1",
        json={
            "nom": "Modifie",
            "role": "commandant",
            "mission_id": 1,
            "nationalite": "Etats-Unis",
        },
    )
    assert reponse.status_code == 200
    relecture = client.get("/api/astronautes/1")
    assert relecture.get_json()["nom"] == "Modifie"
    assert relecture.get_json()["role"] == "commandant"
    assert relecture.get_json()["mission_id"] == 1
    assert relecture.get_json()["nationalite"] == "Etats-Unis"


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


# ---------------------------------------------------------------------------
# Tests de l'API des missions
# ---------------------------------------------------------------------------

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
def test_creation_mission_valide(client):
    reponse = client.post("/api/missions", json={"nom": "Apollo 13", "annee": 1970})
    assert reponse.status_code == 201
    assert "Location" in reponse.headers
    relecture = client.get(reponse.headers["Location"])
    assert relecture.status_code == 200
    assert relecture.get_json()["nom"] == "Apollo 13"
    assert relecture.get_json()["annee"] == 1970


# Le programme est déduit du nom, il n'est pas fourni par le client
def test_creation_mission_deduit_le_programme(client):
    reponse = client.post("/api/missions", json={"nom": "Vostok 1", "annee": 1961})
    assert reponse.status_code == 201
    assert reponse.get_json()["programme"] == "Vostok"


# ... et le fournir quand même est donc un champ inconnu : 400
def test_creation_mission_refuse_le_programme_fourni(client):
    reponse = client.post(
        "/api/missions", json={"nom": "Gemini 4", "programme": "Gemini", "annee": 1965}
    )
    assert reponse.status_code == 400
    assert "Extra inputs are not permitted" in reponse.get_json()["details"]["programme"]


# Nom déjà pris : 400 (contrainte unique sur Mission.nom)
def test_creation_mission_nom_deja_existant(client):
    reponse = client.post("/api/missions", json={"nom": "Apollo 11", "annee": 1969})
    assert reponse.status_code == 409


# L'année est un entier, pas une chaîne : 400
def test_creation_mission_annee_non_entiere(client):
    reponse = client.post("/api/missions", json={"nom": "Gemini 4", "annee": "1965"})
    assert reponse.status_code == 400
    assert "annee" in reponse.get_json()["details"]


# L'année est un entier, pas une chaîne : 400
def test_creation_mission_annee_booleen(client):
    reponse = client.post("/api/missions", json={"nom": "Gemini 4", "annee": True})
    assert reponse.status_code == 400
    assert "annee" in reponse.get_json()["details"]



# Champ manquant : 400
def test_creation_mission_avec_champ_manquant(client):
    reponse = client.post("/api/missions", json={"nom": "Gemini 4"})
    assert reponse.status_code == 400
    assert reponse.get_json()["details"]["annee"] == "Field required"


# Nom vide : 400
def test_creation_mission_avec_nom_vide(client):
    reponse = client.post("/api/missions", json={"nom": "   ", "annee": 1965})
    assert reponse.status_code == 400


# Champ inconnu : 400
def test_creation_mission_avec_champ_inconnu(client):
    reponse = client.post(
        "/api/missions", json={"nom": "Gemini 4", "annee": 1965, "cout": 500}
    )
    assert reponse.status_code == 400


# Corps vide : 400
def test_creation_mission_avec_corps_vide(client):
    reponse = client.post("/api/missions", json={})
    assert reponse.status_code == 400


# JSON mal formé : 400 et réponse quand même en JSON
def test_creation_mission_corps_json_malforme(client):
    reponse = client.post(
        "/api/missions", data="{invalide}", content_type="application/json"
    )
    assert reponse.status_code == 400
    assert reponse.get_json() is not None


# Une création est bien visible dans la liste
def test_creation_mission_apparait_dans_la_liste(client):
    client.post("/api/missions", json={"nom": "Apollo 13", "annee": 1970})
    reponse = client.get("/api/missions")
    assert len(reponse.get_json()) == 4


# Suppression d'une mission sans équipage : 204, puis un GET qui renvoie 404
def test_suppression_mission_sans_equipage(client):
    reponse = client.delete("/api/missions/3")
    assert reponse.status_code == 204
    assert reponse.get_data() == b""
    relecture = client.get("/api/missions/3")
    assert relecture.status_code == 404


# Suppression d'une mission inexistante : 404
def test_suppression_mission_inexistante(client):
    reponse = client.delete("/api/missions/999")
    assert reponse.status_code == 404


# Suppression d'une mission avec équipage : 409
def test_suppression_mission_avec_equipage(client):
    reponse = client.delete("/api/missions/2")
    assert reponse.status_code == 409


# Garde-fou base de données : le doublon n'est plus détecté en amont par la
# validation, c'est la contrainte unique sur Mission.nom qui tranche.
def test_creer_mission_doublon_leve_mission_deja_existante(client):
    with bdd.FabriqueSession() as session:
        with pytest.raises(MissionDejaExistante):
            donnees.creer_mission(session, {"nom": "Apollo 11", "annee": 1969})

        # le rollback a bien eu lieu : la session reste utilisable
        assert len(donnees.lister_missions(session)) == 3


# Le flush renseigne l'identifiant avant que la route ne construise Location
def test_creer_mission_renseigne_l_identifiant_avant_le_commit(client):
    with bdd.FabriqueSession() as session:
        mission = donnees.creer_mission(session, {"nom": "Apollo 13", "annee": 1970})
        assert mission.id is not None
        session.commit()


# Test de relecture puis mise à jour d'un astronaute via PUT
def test_relecture_puis_put_fonctionne(client):
    lu = client.get("/api/astronautes/1").get_json()
    renvoi = {k: v for k, v in lu.items() if k != "id"}
    assert client.put("/api/astronautes/1", json=renvoi).status_code == 200

# 
def test_annee_en_chaine_est_refusee(client):
    reponse = client.post("/api/missions", json={"nom": "Apollo 18", "annee": "1973"})
    assert reponse.status_code == 400

#
def test_nom_avec_espaces_est_nettoye(client):
    reponse = client.post("/api/astronautes", json={
        "nom": "  Michael Collins  ", "role": "pilote",
        "nationalite": "Etats-Unis", "mission_id": 1,
    })
    assert reponse.get_json()["nom"] == "Michael Collins"

# ---------------------------------------------------------------------------
# PATCH : les champs envoyés sont validés comme à la création
# ---------------------------------------------------------------------------

# Nom vide : 400 (et l'astronaute n'est pas modifié)
def test_patch_nom_vide_renvoie_400(client):
    reponse = client.patch("/api/astronautes/1", json={"nom": ""})
    assert reponse.status_code == 400
    assert "nom" in reponse.get_json()["details"]
    assert client.get("/api/astronautes/1").get_json()["nom"] == "Neil Armstrong"


# Nom composé uniquement d'espaces : 400 (le nettoyage laisse une chaîne vide)
def test_patch_nom_espaces_renvoie_400(client):
    reponse = client.patch("/api/astronautes/1", json={"nom": "   "})
    assert reponse.status_code == 400
    assert "nom" in reponse.get_json()["details"]
    assert client.get("/api/astronautes/1").get_json()["nom"] == "Neil Armstrong"


# Nationalité vide : 400 (et l'astronaute n'est pas modifié)
def test_patch_nationalite_vide_renvoie_400(client):
    reponse = client.patch("/api/astronautes/1", json={"nationalite": ""})
    assert reponse.status_code == 400
    assert "nationalite" in reponse.get_json()["details"]
    assert client.get("/api/astronautes/1").get_json()["nationalite"] == "Etats-Unis"


# mission_id à 0 : 400, refusé par la validation (un identifiant vaut au moins 1)
def test_patch_mission_id_zero_renvoie_400(client):
    reponse = client.patch("/api/astronautes/1", json={"mission_id": 0})
    assert reponse.status_code == 400
    assert "mission_id" in reponse.get_json()["details"]
    assert client.get("/api/astronautes/1").get_json()["mission_id"] == 1


# mission_id valide mais inexistant : 404, pas un rattachement silencieux
def test_patch_mission_id_inexistant_renvoie_404(client):
    reponse = client.patch("/api/astronautes/1", json={"mission_id": 999})
    assert reponse.status_code == 404
    assert "erreur" in reponse.get_json()
    assert client.get("/api/astronautes/1").get_json()["mission_id"] == 1


# Même garde-fou côté PUT
def test_put_mission_id_inexistant_renvoie_404(client):
    reponse = client.put(
        "/api/astronautes/1",
        json={
            "nom": "Neil Armstrong",
            "role": "commandant",
            "mission_id": 999,
            "nationalite": "Etats-Unis",
        },
    )
    assert reponse.status_code == 404
    assert client.get("/api/astronautes/1").get_json()["mission_id"] == 1


# Année antérieure à 1900 : 400 (et la mission n'est pas modifiée)
def test_patch_mission_annee_trop_ancienne_renvoie_400(client):
    reponse = client.patch("/api/missions/1", json={"annee": 1500})
    assert reponse.status_code == 400
    assert "annee" in reponse.get_json()["details"]
    assert client.get("/api/missions/1").get_json()["annee"] == 1969


# Nom de mission vide : 400 (même règle qu'à la création)
def test_patch_mission_nom_vide_renvoie_400(client):
    reponse = client.patch("/api/missions/1", json={"nom": "   "})
    assert reponse.status_code == 400
    assert "nom" in reponse.get_json()["details"]
    assert client.get("/api/missions/1").get_json()["nom"] == "Apollo 11"
