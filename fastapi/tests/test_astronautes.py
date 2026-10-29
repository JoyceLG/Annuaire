"""Tests de l'API des astronautes.

FastAPI répond 422 quand le corps ou les
paramètres ne passent pas la validation Pydantic.
"""

import re

import pytest

# Les champs d'identité, communs à l'entrée et à la sortie.
EDGAR_MITCHELL_IDENTITE = {
    "nom": "Edgar Mitchell",
    "role": "pilote",
    "nationalite": "Etats-Unis",
}
QUALIFICATION_PILOTE = {"type": "pilote", "heures_vol": 1500, "appareil": "T-38"}
QUALIFICATION_SCIENTIFIQUE = {
    "type": "scientifique",
    "discipline": "Astronomie",
    "doctorat": True,
}
QUALIFICATION_INGENIEUR = {
    "type": "ingenieur",
    "specialite": "Propulsion",
    "experience": 10,
}
# Corps d'une création ou d'un PUT : l'identité plus une qualification
# cohérente avec le rôle.
EDGAR_MITCHELL = {**EDGAR_MITCHELL_IDENTITE, "qualification": QUALIFICATION_PILOTE}
# Ce que l'API renvoie pour EDGAR_MITCHELL, hors identifiant : AstronauteSortie
# n'expose pas la qualification, mais ajoute les initiales.
EDGAR_MITCHELL_SORTIE = {**EDGAR_MITCHELL_IDENTITE, "initiales": "EM"}


# Liste complète : les trois astronautes du jeu de démonstration
def test_liste_renvoie_tous_les_astronautes(client):
    reponse = client.get("/api/astronautes")
    assert reponse.status_code == 200
    assert [a["nom"] for a in reponse.json()] == [
        "Neil Armstrong",
        "Alan Bean",
        "Sophie Adenot",
    ]


# La qualification est enregistrée mais ne sort jamais dans la réponse
def test_liste_n_expose_pas_la_qualification(client):
    reponse = client.get("/api/astronautes")
    assert all("qualification" not in a for a in reponse.json())


# Lecture d'un astronaute existant
def test_lire_astronaute_existant(client):
    reponse = client.get("/api/astronautes/1")
    assert reponse.status_code == 200
    assert reponse.json() == {
        "id": 1,
        "nom": "Neil Armstrong",
        "role": "commandant",
        "nationalite": "Etats-Unis",
        "initiales": "NA",
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
def test_liste_filtre_sans_resultat(client_authentifie):
    # Le jeu de démonstration couvre tous les rôles : on retire la seule
    # spécialiste pour obtenir un filtre qui ne trouve rien.
    client_authentifie.delete("/api/astronautes/3")
    reponse = client_authentifie.get("/api/astronautes?role=specialiste")
    assert reponse.status_code == 200
    assert reponse.json() == []


# Création valide : 201, en-tête Location présent, et relecture pour confirmer
def test_creation_valide(client_authentifie):
    reponse = client_authentifie.post("/api/astronautes", json=EDGAR_MITCHELL)
    assert reponse.status_code == 201
    assert reponse.json() == {"id": 4, **EDGAR_MITCHELL_SORTIE}
    relecture = client_authentifie.get(reponse.headers["Location"])
    assert relecture.status_code == 200
    assert relecture.json()["nom"] == "Edgar Mitchell"


# Deux créations successives reçoivent deux identifiants distincts
def test_creations_successives_ont_des_identifiants_distincts(client_authentifie):
    premier = client_authentifie.post("/api/astronautes", json=EDGAR_MITCHELL)
    second = client_authentifie.post(
        "/api/astronautes", json={**EDGAR_MITCHELL, "nom": "Alan Shepard"}
    )
    assert premier.json()["id"] != second.json()["id"]
    assert len(client_authentifie.get("/api/astronautes").json()) == 5


# Un créé ne reçoit pas l'identifiant déjà utilisé par un supprimé
def test_creation_apres_suppression(client_authentifie):
    client_authentifie.delete("/api/astronautes/2")
    reponse = client_authentifie.post("/api/astronautes", json=EDGAR_MITCHELL)
    assert reponse.json()["id"] != 2


# Créer, supprimer, recréer : le recréé a un nouvel id, l'ancien reste introuvable
def test_creer_supprimer_recreer(client_authentifie):
    cree = client_authentifie.post("/api/astronautes", json=EDGAR_MITCHELL).json()["id"]
    assert client_authentifie.delete(f"/api/astronautes/{cree}").status_code == 204

    recree = client_authentifie.post("/api/astronautes", json=EDGAR_MITCHELL).json()["id"]
    assert recree != cree
    assert client_authentifie.get(f"/api/astronautes/{cree}").status_code == 404
    assert client_authentifie.get(f"/api/astronautes/{recree}").status_code == 200


# Champ manquant : 422, et rien n'est créé
def test_creation_avec_champ_manquant(client_authentifie):
    reponse = client_authentifie.post(
        "/api/astronautes",
        json={"nom": "Edgar Mitchell", "nationalite": "Etats-Unis"},
    )
    assert reponse.status_code == 422
    assert len(client_authentifie.get("/api/astronautes").json()) == 3


# Rôle invalide : 422
def test_creation_avec_role_invalide(client_authentifie):
    reponse = client_authentifie.post(
        "/api/astronautes",
        json={**EDGAR_MITCHELL, "role": "cosmonaute"},
    )
    assert reponse.status_code == 422


# Chaque rôle accepte les qualifications que lui attribue QUALIFICATIONS_PAR_ROLE
@pytest.mark.parametrize(
    "role, qualification",
    [
        ("commandant", QUALIFICATION_PILOTE),
        ("commandant", QUALIFICATION_SCIENTIFIQUE),
        ("commandant", QUALIFICATION_INGENIEUR),
        ("pilote", QUALIFICATION_PILOTE),
        ("specialiste", QUALIFICATION_SCIENTIFIQUE),
        ("specialiste", QUALIFICATION_INGENIEUR),
    ],
)
def test_creation_avec_qualification_coherente(client_authentifie, role, qualification):
    reponse = client_authentifie.post(
        "/api/astronautes",
        json={**EDGAR_MITCHELL, "role": role, "qualification": qualification},
    )
    assert reponse.status_code == 201


# Qualification incohérente avec le rôle : 422, et rien n'est créé
@pytest.mark.parametrize(
    "role, qualification",
    [
        ("pilote", QUALIFICATION_SCIENTIFIQUE),
        ("pilote", QUALIFICATION_INGENIEUR),
        ("specialiste", QUALIFICATION_PILOTE),
    ],
)
def test_creation_avec_qualification_incoherente(client_authentifie, role, qualification):
    reponse = client_authentifie.post(
        "/api/astronautes",
        json={**EDGAR_MITCHELL, "role": role, "qualification": qualification},
    )
    assert reponse.status_code == 422
    assert len(client_authentifie.get("/api/astronautes").json()) == 3


# Type de qualification inconnu du discriminateur : 422
def test_creation_avec_type_de_qualification_inconnu(client_authentifie):
    reponse = client_authentifie.post(
        "/api/astronautes",
        json={**EDGAR_MITCHELL, "qualification": {"type": "cuisinier"}},
    )
    assert reponse.status_code == 422


# Qualification mal typée ou avec un champ inconnu : 422, rien n'est créé.
# Le mode strict d'AstronauteEntree ne s'étend pas aux modèles qu'il contient :
# sans leur propre configuration, `false` devenait 0 heure de vol.
@pytest.mark.parametrize(
    "qualification",
    [
        {**QUALIFICATION_PILOTE, "heures_vol": False},
        {**QUALIFICATION_PILOTE, "heures_vol": "1500"},
        {**QUALIFICATION_PILOTE, "salaire": 10000},
    ],
)
def test_creation_avec_qualification_mal_formee(client_authentifie, qualification):
    reponse = client_authentifie.post(
        "/api/astronautes",
        json={**EDGAR_MITCHELL, "qualification": qualification},
    )
    assert reponse.status_code == 422
    assert len(client_authentifie.get("/api/astronautes").json()) == 3


# Champ inconnu : 422
def test_creation_avec_champ_inconnu(client_authentifie):
    reponse = client_authentifie.post(
        "/api/astronautes",
        json={**EDGAR_MITCHELL, "salaire": "100000"},
    )
    assert reponse.status_code == 422


# Mode strict : un nombre n'est pas converti en texte
def test_creation_avec_nom_numerique(client_authentifie):
    reponse = client_authentifie.post("/api/astronautes", json={**EDGAR_MITCHELL, "nom": 42})
    assert reponse.status_code == 422


# Nom fait uniquement d'espaces : 422
def test_creation_avec_nom_vide(client_authentifie):
    reponse = client_authentifie.post("/api/astronautes", json={**EDGAR_MITCHELL, "nom": "   "})
    assert reponse.status_code == 422


# Corps vide : 422
def test_creation_avec_corps_vide(client_authentifie):
    reponse = client_authentifie.post("/api/astronautes", json={})
    assert reponse.status_code == 422


# JSON mal formé : 422 avec un corps JSON
def test_corps_json_malforme(client_authentifie):
    reponse = client_authentifie.post(
        "/api/astronautes",
        content="{invalide}",
        headers={"Content-Type": "application/json"},
    )
    assert reponse.status_code == 422
    assert "detail" in reponse.json()


# Modification d'un astronaute existant
def test_put_remplace_reellement(client_authentifie):
    reponse = client_authentifie.put("/api/astronautes/1", json=EDGAR_MITCHELL)
    assert reponse.status_code == 200
    relecture = client_authentifie.get("/api/astronautes/1")
    assert relecture.json() == {"id": 1, **EDGAR_MITCHELL_SORTIE}


# PUT incomplet : 422, et l'astronaute est intact
def test_put_avec_champs_incomplets(client_authentifie):
    reponse = client_authentifie.put(
        "/api/astronautes/1",
        json={"nom": "Modifie", "nationalite": "Etats-Unis"},
    )
    assert reponse.status_code == 422
    assert client_authentifie.get("/api/astronautes/1").json()["nom"] == "Neil Armstrong"


# PUT avec une qualification incohérente : 422, et l'astronaute est intact
def test_put_avec_qualification_incoherente(client_authentifie):
    reponse = client_authentifie.put(
        "/api/astronautes/1",
        json={**EDGAR_MITCHELL, "qualification": QUALIFICATION_SCIENTIFIQUE},
    )
    assert reponse.status_code == 422
    assert client_authentifie.get("/api/astronautes/1").json()["nom"] == "Neil Armstrong"


# PUT sur un inexistant : 404
def test_put_inexistant(client_authentifie):
    reponse = client_authentifie.put("/api/astronautes/999", json=EDGAR_MITCHELL)
    assert reponse.status_code == 404


# PATCH partiel : seul le champ envoyé change, les autres sont intacts
def test_patch_ne_touche_que_les_champs_envoyes(client_authentifie):
    reponse = client_authentifie.patch("/api/astronautes/1", json={"nom": "Modifie"})
    assert reponse.status_code == 200
    attendu = {
        "id": 1,
        "nom": "Modifie",
        "role": "commandant",
        "nationalite": "Etats-Unis",
        "initiales": "M",
    }
    assert reponse.json() == attendu
    assert client_authentifie.get("/api/astronautes/1").json() == attendu


# PATCH complet : tous les champs envoyés changent
def test_patch_modifie_avec_tous_les_champs(client_authentifie):
    reponse = client_authentifie.patch("/api/astronautes/1", json=EDGAR_MITCHELL_IDENTITE)
    assert reponse.status_code == 200
    assert client_authentifie.get("/api/astronautes/1").json() == {"id": 1, **EDGAR_MITCHELL_SORTIE}


# PATCH avec rôle invalide : 422, et l'astronaute est intact
def test_patch_avec_role_invalide(client_authentifie):
    reponse = client_authentifie.patch(
        "/api/astronautes/1",
        json={"nom": "Modifie", "role": "cosmonaute"},
    )
    assert reponse.status_code == 422
    assert client_authentifie.get("/api/astronautes/1").json()["nom"] == "Neil Armstrong"


# PATCH avec corps vide : 422, il n'y a rien à modifier
def test_patch_corps_vide(client_authentifie):
    reponse = client_authentifie.patch("/api/astronautes/1", json={})
    assert reponse.status_code == 422


# PATCH avec un champ à null : 422, et l'astronaute est intact
def test_patch_champ_null(client_authentifie):
    reponse = client_authentifie.patch("/api/astronautes/1", json={"nom": None})
    assert reponse.status_code == 422
    assert client_authentifie.get("/api/astronautes/1").json()["nom"] == "Neil Armstrong"


# PATCH de la seule qualification : 200, et les autres champs sont intacts
def test_patch_de_la_qualification(client_authentifie):
    reponse = client_authentifie.patch(
        "/api/astronautes/1",
        json={"qualification": QUALIFICATION_SCIENTIFIQUE},
    )
    assert reponse.status_code == 200
    assert reponse.json()["nom"] == "Neil Armstrong"


# PATCH du seul rôle, cohérent avec la qualification enregistrée : 200
def test_patch_du_role_coherent_avec_la_qualification_enregistree(client_authentifie):
    # Neil Armstrong, commandant, a une qualification de pilote.
    reponse = client_authentifie.patch("/api/astronautes/1", json={"role": "pilote"})
    assert reponse.status_code == 200
    assert reponse.json()["role"] == "pilote"


# PATCH du seul rôle, incohérent avec la qualification enregistrée : 422, intact
def test_patch_du_role_incoherent_avec_la_qualification_enregistree(client_authentifie):
    # Alan Bean, pilote, a une qualification de pilote.
    reponse = client_authentifie.patch("/api/astronautes/2", json={"role": "specialiste"})
    assert reponse.status_code == 422
    assert "erreur" in reponse.json()
    assert client_authentifie.get("/api/astronautes/2").json()["role"] == "pilote"


# PATCH de la seule qualification, incohérente avec le rôle enregistré : 422
def test_patch_de_la_qualification_incoherente_avec_le_role_enregistre(client_authentifie):
    reponse = client_authentifie.patch(
        "/api/astronautes/2",
        json={"qualification": QUALIFICATION_SCIENTIFIQUE},
    )
    assert reponse.status_code == 422


# PATCH du rôle et de la qualification, incohérents entre eux : 422, intact
def test_patch_du_role_et_de_la_qualification_incoherents(client_authentifie):
    reponse = client_authentifie.patch(
        "/api/astronautes/1",
        json={"role": "pilote", "qualification": QUALIFICATION_SCIENTIFIQUE},
    )
    assert reponse.status_code == 422
    assert client_authentifie.get("/api/astronautes/1").json()["role"] == "commandant"


# PATCH sur un inexistant : 404
def test_patch_inexistant(client_authentifie):
    reponse = client_authentifie.patch("/api/astronautes/999", json={"nom": "Modifie"})
    assert reponse.status_code == 404


# Suppression : 204 sans corps, puis un GET qui renvoie 404
def test_suppression_astronaute(client_authentifie):
    reponse = client_authentifie.delete("/api/astronautes/1")
    assert reponse.status_code == 204
    assert reponse.content == b""
    assert client_authentifie.get("/api/astronautes/1").status_code == 404


# Suppression d'un inexistant : 404
def test_suppression_inexistant(client_authentifie):
    reponse = client_authentifie.delete("/api/astronautes/100")
    assert reponse.status_code == 404


# Une suppression ne décale pas les identifiants des autres
def test_suppression_ne_decale_pas_les_identifiants(client_authentifie):
    client_authentifie.delete("/api/astronautes/1")
    reponse = client_authentifie.get("/api/astronautes/2")
    assert reponse.json()["nom"] == "Alan Bean"


# Sans jeton, chaque route d'écriture des astronautes répond 401. Les routes
# sont lues dans le schéma OpenAPI : depuis FastAPI 0.141, `app.routes` ne
# liste plus les routes des routeurs inclus, la boucle n'y trouverait rien.
def test_toutes_les_ecritures_exigent_un_jeton(client):
    chemins = client.app.openapi()["paths"]
    ecritures = [
        (methode, re.sub(r"\{[^}]+\}", "1", chemin))
        for chemin, operations in chemins.items()
        if chemin.startswith("/api/astronautes")
        for methode in operations
        if methode != "get"
    ]
    # Garde-fou : une liste vide ferait passer le test sans rien vérifier.
    assert len(ecritures) == 4
    for methode, chemin in ecritures:
        reponse = client.request(methode, chemin)
        assert reponse.status_code == 401, f"{methode.upper()} {chemin} non protégée"
