"""Tests de l'API des missions.

FastAPI répond 422 quand le corps ou les
paramètres ne passent pas la validation Pydantic.
"""

import re

APOLLO_14 = {"nom": "Apollo 14", "annee": 1971}
# Ce que l'API renvoie pour APOLLO_14, hors identifiant : les champs envoyés,
# plus le programme calculé par MissionSortie.
APOLLO_14_SORTIE = {**APOLLO_14, "programme": "Apollo"}


# Liste complète : les trois missions du jeu de démonstration
def test_liste_renvoie_toutes_les_missions(client):
    reponse = client.get("/api/missions")
    assert reponse.status_code == 200
    assert [m["nom"] for m in reponse.json()] == ["Apollo 11", "Apollo 12", "Apollo 13"]


# Lecture d'une mission existante, avec son programme calculé
def test_lire_mission_existante(client):
    reponse = client.get("/api/missions/1")
    assert reponse.status_code == 200
    assert reponse.json() == {
        "id": 1,
        "nom": "Apollo 11",
        "annee": 1969,
        "programme": "Apollo",
    }


# Lecture d'une mission inexistante : 404 avec un message d'erreur
def test_lire_mission_inexistante(client):
    reponse = client.get("/api/missions/999")
    assert reponse.status_code == 404
    assert "erreur" in reponse.json()


# Identifiant non entier : 422
def test_lire_mission_avec_id_non_entier(client):
    reponse = client.get("/api/missions/apollo")
    assert reponse.status_code == 422


# Filtre par année : seules les missions de cette année ou plus récentes
def test_liste_filtre_par_annee(client):
    reponse = client.get("/api/missions?annee=1970")
    assert reponse.status_code == 200
    assert [m["nom"] for m in reponse.json()] == ["Apollo 13"]


# Filtre sans résultat : 200 et tableau vide
def test_liste_filtre_sans_resultat(client):
    reponse = client.get("/api/missions?annee=2000")
    assert reponse.status_code == 200
    assert reponse.json() == []


# Filtre sur une année antérieure à ANNEE_MINIMALE : 422
def test_liste_filtre_annee_trop_ancienne(client):
    reponse = client.get("/api/missions?annee=1800")
    assert reponse.status_code == 422


# La limite tronque la liste
def test_liste_limite(client):
    reponse = client.get("/api/missions?limite=2")
    assert reponse.status_code == 200
    assert [m["nom"] for m in reponse.json()] == ["Apollo 11", "Apollo 12"]


# Limite hors bornes : 422 sous le minimum (validation du paramètre) comme
# au-delà de LIMITE_PAGINATION_MAX (contrôle fait par la pagination)
def test_liste_limite_hors_bornes(client):
    assert client.get("/api/missions?limite=0").status_code == 422
    assert client.get("/api/missions?limite=100").status_code == 200
    assert client.get("/api/missions?limite=101").status_code == 422


# Création valide : 201, en-tête Location présent, et relecture pour confirmer
def test_creation_valide(client_authentifie):
    reponse = client_authentifie.post("/api/missions", json=APOLLO_14)
    assert reponse.status_code == 201
    assert reponse.json() == {"id": 4, **APOLLO_14_SORTIE}
    relecture = client_authentifie.get(reponse.headers["Location"])
    assert relecture.status_code == 200
    assert relecture.json()["nom"] == "Apollo 14"


# Le programme est le premier mot du nom
def test_creation_calcule_le_programme(client_authentifie):
    reponse = client_authentifie.post("/api/missions", json={"nom": "Gemini 4", "annee": 1965})
    assert reponse.json()["programme"] == "Gemini"


# Un créé ne reçoit pas l'identifiant déjà utilisé par un supprimé
def test_creation_apres_suppression(client_authentifie):
    client_authentifie.delete("/api/missions/3")
    reponse = client_authentifie.post("/api/missions", json=APOLLO_14)
    assert reponse.json()["id"] != 3


# Champ manquant : 422, et rien n'est créé
def test_creation_avec_champ_manquant(client_authentifie):
    reponse = client_authentifie.post("/api/missions", json={"nom": "Apollo 14"})
    assert reponse.status_code == 422
    assert len(client_authentifie.get("/api/missions").json()) == 3


# Année antérieure à ANNEE_MINIMALE : 422
def test_creation_avec_annee_trop_ancienne(client_authentifie):
    reponse = client_authentifie.post("/api/missions", json={**APOLLO_14, "annee": 1899})
    assert reponse.status_code == 422


# Mode strict : une année en texte n'est pas convertie en entier
def test_creation_avec_annee_en_texte(client_authentifie):
    reponse = client_authentifie.post("/api/missions", json={**APOLLO_14, "annee": "1971"})
    assert reponse.status_code == 422


# Nom fait uniquement d'espaces : 422
def test_creation_avec_nom_vide(client_authentifie):
    reponse = client_authentifie.post("/api/missions", json={**APOLLO_14, "nom": "   "})
    assert reponse.status_code == 422


# Champ inconnu : 422
def test_creation_avec_champ_inconnu(client_authentifie):
    reponse = client_authentifie.post("/api/missions", json={**APOLLO_14, "budget": 1000})
    assert reponse.status_code == 422


# Corps vide : 422
def test_creation_avec_corps_vide(client_authentifie):
    reponse = client_authentifie.post("/api/missions", json={})
    assert reponse.status_code == 422


# Modification d'une mission existante
def test_put_remplace_reellement(client_authentifie):
    reponse = client_authentifie.put("/api/missions/1", json=APOLLO_14)
    assert reponse.status_code == 200
    relecture = client_authentifie.get("/api/missions/1")
    assert relecture.json() == {"id": 1, **APOLLO_14_SORTIE}


# PUT incomplet : 422, et la mission est intacte
def test_put_avec_champs_incomplets(client_authentifie):
    reponse = client_authentifie.put("/api/missions/1", json={"nom": "Modifiee"})
    assert reponse.status_code == 422
    assert client_authentifie.get("/api/missions/1").json()["nom"] == "Apollo 11"


# PUT sur une inexistante : 404
def test_put_inexistant(client_authentifie):
    reponse = client_authentifie.put("/api/missions/999", json=APOLLO_14)
    assert reponse.status_code == 404


# PATCH partiel : seul le champ envoyé change, les autres sont intacts
def test_patch_ne_touche_que_les_champs_envoyes(client_authentifie):
    reponse = client_authentifie.patch("/api/missions/1", json={"nom": "Gemini 4"})
    assert reponse.status_code == 200
    attendu = {"id": 1, "nom": "Gemini 4", "annee": 1969, "programme": "Gemini"}
    assert reponse.json() == attendu
    assert client_authentifie.get("/api/missions/1").json() == attendu


# PATCH complet : tous les champs envoyés changent
def test_patch_modifie_avec_tous_les_champs(client_authentifie):
    reponse = client_authentifie.patch("/api/missions/1", json=APOLLO_14)
    assert reponse.status_code == 200
    assert client_authentifie.get("/api/missions/1").json() == {"id": 1, **APOLLO_14_SORTIE}


# PATCH avec une année trop ancienne : 422, et la mission est intacte
def test_patch_avec_annee_trop_ancienne(client_authentifie):
    reponse = client_authentifie.patch("/api/missions/1", json={"annee": 1800})
    assert reponse.status_code == 422
    assert client_authentifie.get("/api/missions/1").json()["annee"] == 1969


# PATCH avec corps vide : 422, il n'y a rien à modifier
def test_patch_corps_vide(client_authentifie):
    reponse = client_authentifie.patch("/api/missions/1", json={})
    assert reponse.status_code == 422


# PATCH avec un champ à null : 422, et la mission est intacte
def test_patch_champ_null(client_authentifie):
    reponse = client_authentifie.patch("/api/missions/1", json={"nom": None})
    assert reponse.status_code == 422
    assert client_authentifie.get("/api/missions/1").json()["nom"] == "Apollo 11"


# PATCH sur une inexistante : 404
def test_patch_inexistant(client_authentifie):
    reponse = client_authentifie.patch("/api/missions/999", json={"nom": "Modifiee"})
    assert reponse.status_code == 404


# Suppression : 204 sans corps, puis un GET qui renvoie 404
def test_suppression_mission(client_authentifie):
    reponse = client_authentifie.delete("/api/missions/1")
    assert reponse.status_code == 204
    assert reponse.content == b""
    assert client_authentifie.get("/api/missions/1").status_code == 404


# Suppression d'une inexistante : 404
def test_suppression_inexistante(client_authentifie):
    reponse = client_authentifie.delete("/api/missions/999")
    assert reponse.status_code == 404


# Une suppression ne décale pas les identifiants des autres
def test_suppression_ne_decale_pas_les_identifiants(client_authentifie):
    client_authentifie.delete("/api/missions/1")
    reponse = client_authentifie.get("/api/missions/2")
    assert reponse.json()["nom"] == "Apollo 12"


# Sans jeton, chaque route d'écriture des missions répond 401. Les routes
# sont lues dans le schéma OpenAPI : depuis FastAPI 0.141, `app.routes` ne
# liste plus les routes des routeurs inclus, la boucle n'y trouverait rien.
def test_toutes_les_ecritures_exigent_un_jeton(client):
    chemins = client.app.openapi()["paths"]
    ecritures = [
        (methode, re.sub(r"\{[^}]+\}", "1", chemin))
        for chemin, operations in chemins.items()
        if chemin.startswith("/api/missions")
        for methode in operations
        if methode != "get"
    ]
    # Garde-fou : une liste vide ferait passer le test sans rien vérifier.
    assert len(ecritures) == 4
    for methode, chemin in ecritures:
        reponse = client.request(methode, chemin)
        assert reponse.status_code == 401, f"{methode.upper()} {chemin} non protégée"


# Un identifiant libéré n'est jamais réattribué (garantie de la session 6).
# Sans AUTOINCREMENT, SQLite réattribuerait 4 à la mission recréée, et un
# client qui avait mémorisé /api/missions/4 pointerait vers une autre mission.
def test_identifiant_supprime_jamais_reattribue(client_authentifie):
    creee = client_authentifie.post("/api/missions", json=APOLLO_14)
    id_supprime = creee.json()["id"]
    assert client_authentifie.delete(f"/api/missions/{id_supprime}").status_code == 204

    recreee = client_authentifie.post("/api/missions", json=APOLLO_14)

    assert recreee.json()["id"] != id_supprime
