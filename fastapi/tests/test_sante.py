"""Route de santé : joignable sans jeton."""


# Application démarrée : 200 et statut « ok »
def test_sante_repond_200(client):
    reponse = client.get("/api/sante")
    assert reponse.status_code == 200
    assert reponse.json() == {"statut": "ok"}
