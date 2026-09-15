"""Tests de l'API des utilisateurs : inscription, connexion, compte."""


# Inscription valide : 201, et l'empreinte n'apparaît nulle part dans la réponse
def test_inscription_valide_renvoie_201(client, entetes_auth):
    reponse = client.post(
        "/api/inscription",
        json={
            "email": "nouvel.utilisateur@example.com",
            "mot_de_passe": "motdepassevalide",
        },
        headers=entetes_auth,
    )
    assert reponse.status_code == 201
    assert "empreinte" not in reponse.get_json()


# Email déjà utilisé : 409
def test_inscription_email_deja_utilise_renvoie_409(client, entetes_auth):
    client.post(
        "/api/inscription",
        json={
            "email": "nouvel.utilisateur@example.com",
            "mot_de_passe": "motdepassevalide",
        },
        headers=entetes_auth,
    )
    reponse = client.post(
        "/api/inscription",
        json={
            "email": "nouvel.utilisateur@example.com",
            "mot_de_passe": "motdepassevalide",
        },
        headers=entetes_auth,
    )
    assert reponse.status_code == 409
    assert "erreur" in reponse.get_json()


# Email invalide : 400
def test_inscription_email_invalide_renvoie_400(client, entetes_auth):
    reponse = client.post(
        "/api/inscription",
        json={
            "email": "email.invalide",
            "mot_de_passe": "motdepassevalide",
        },
        headers=entetes_auth,
    )
    assert reponse.status_code == 400
    assert "email" in reponse.get_json()["details"]


# Mot de passe trop court : 400 (et l'inscription n'est pas créée)
def test_inscription_mot_de_passe_trop_court_renvoie_400(client, entetes_auth):
    reponse = client.post(
        "/api/inscription",
        json={
            "email": "utilisateur@example.com",
            "mot_de_passe": "123",
        },
        headers=entetes_auth,
    )
    assert reponse.status_code == 400
    assert "mot_de_passe" in reponse.get_json()["details"]


# Connexion correcte : 200
def test_connexion_correcte_renvoie_200(client, entetes_auth):
    client.post(
        "/api/inscription",
        json={
            "email": "nouvel.utilisateur@example.com",
            "mot_de_passe": "motdepassevalide",
        },
        headers=entetes_auth,
    )
    reponse = client.post(
        "/api/connexion",
        json={
            "email": "nouvel.utilisateur@example.com",
            "mot_de_passe": "motdepassevalide",
        },
        headers=entetes_auth,
    )
    assert reponse.status_code == 200


# Mauvais mot de passe : 401
def test_connexion_mauvais_mot_de_passe_renvoie_401(client, entetes_auth):
    client.post(
        "/api/inscription",
        json={
            "email": "nouvel.utilisateur@example.com",
            "mot_de_passe": "motdepassevalide",
        },
        headers=entetes_auth,
    )
    reponse = client.post(
        "/api/connexion",
        json={
            "email": "nouvel.utilisateur@example.com",
            "mot_de_passe": "mauvaismotdepasse",
        },
        headers=entetes_auth,
    )
    assert reponse.status_code == 401
    assert "erreur" in reponse.get_json()


# Email inexistant : 401, avec exactement le même corps de réponse que le cas précédent
def test_connexion_email_inexistant_renvoie_401(client, entetes_auth):
    client.post(
        "/api/inscription",
        json={
            "email": "nouvel.utilisateur@example.com",
            "mot_de_passe": "motdepassevalide",
        },
        headers=entetes_auth,
    )
    reponse = client.post(
        "/api/connexion",
        json={
            "email": "inexistant@example.com",
            "mot_de_passe": "motdepassevalide",
        },
        headers=entetes_auth,
    )
    assert reponse.status_code == 401
    assert "erreur" in reponse.get_json()


# La réponse de connexion ne doit pas révéler si le compte existe ou non : 401
def test_connexion_ne_revele_pas_si_le_compte_existe(client, entetes_auth):
    client.post(
        "/api/inscription",
        json={
            "email": "connu@example.com",
            "mot_de_passe": "motdepassevalide",
        },
        headers=entetes_auth,
    )
    inconnu = client.post(
        "/api/connexion",
        json={"email": "absent@example.com", "mot_de_passe": "motdepassevalide"},
        headers=entetes_auth,
    )
    mauvais = client.post(
        "/api/connexion",
        json={"email": "connu@example.com", "mot_de_passe": "mauvaismotdepasse"},
        headers=entetes_auth,
    )
    assert inconnu.status_code == mauvais.status_code == 401
    assert inconnu.get_json() == mauvais.get_json()


# L'empreinte ne doit jamais être exposée dans la réponse d'inscription
def test_empreinte_jamais_exposee(client, entetes_auth):
    reponse = client.post(
        "/api/inscription",
        json={
            "email": "nouvel.utilisateur@example.com",
            "mot_de_passe": "motdepassevalide",
        },
        headers=entetes_auth,
    )
    corps = reponse.get_data(as_text=True)
    assert "argon2" not in corps
    assert "empreinte" not in corps


# /api/moi renvoie le bon utilisateur : 200
def test_api_moi_renvoie_bon_utilisateur(client, entetes_auth):
    reponse = client.get("/api/moi", headers=entetes_auth)
    assert reponse.status_code == 200


# Un utilisateur qui modifie le compte d'un autre : 403
def test_utilisateur_modifie_compte_autre(client, entetes_lecteur, entetes_editeur):
    reponse = client.patch("/api/utilisateurs/2", headers=entetes_lecteur, json={"email": "test@example.com"})
    assert reponse.status_code == 403


# Un utilisateur qui modifie son propre compte : 200
def test_utilisateur_modifie_son_propre_compte(client, entetes_lecteur):
    reponse = client.patch("/api/utilisateurs/1", headers=entetes_lecteur, json={"email": "test@example.com"})
    assert reponse.status_code == 200


# Un admin qui modifie le compte d'un autre : 200
def test_admin_modifie_compte_autre(client, entetes_admin, entetes_editeur):
    reponse = client.patch("/api/utilisateurs/2", headers=entetes_admin, json={"email": "test@example.com"})
    assert reponse.status_code == 200


# Un utilisateur qui tente {"role": "admin"} dans son PATCH : 400, et surtout, relis-le pour vérifier que le rôle n'a pas changé
def test_utilisateur_tente_changer_role(client, entetes_lecteur):
    reponse = client.patch("/api/utilisateurs/1", headers=entetes_lecteur, json={"role": "admin"})
    assert reponse.status_code == 400

    relecture = client.get("/api/moi", headers=entetes_lecteur)
    assert relecture.get_json()["role"] == "lecteur"      # la relecture est indispensable


# Un test pour vérifier que les codes 404 et 403 ne distinguent pas les comptes
def test_404_et_403_ne_distinguent_pas_les_comptes(client, entetes_lecteur):
    existant = client.patch("/api/utilisateurs/2", json={"email": "z@x.fr"}, headers=entetes_lecteur)
    absent = client.patch("/api/utilisateurs/9999", json={"email": "z@x.fr"}, headers=entetes_lecteur)
    assert existant.status_code == absent.status_code == 403