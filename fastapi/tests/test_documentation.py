"""Documentation OpenAPI : ce qu'elle annonce doit être vrai.

FastAPI génère le schéma à partir du code, mais tout ce qui est écrit à la
main (`summary`, `description`, `examples`, `responses=`) n'est vérifié par
personne : ces tests comparent ce que la documentation promet à ce que
l'application fait réellement.
"""

from typing import Annotated

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter, ValidationError

from annuaire import creer_app
from annuaire.config import ConfigProduction
from annuaire.schemas.astronautes import AstronauteEntree

METHODES_HTTP = {"get", "post", "put", "patch", "delete"}


@pytest.fixture
def schema():
    return creer_app("test").openapi()


def operations(schema):
    """Toutes les opérations du schéma : (méthode, chemin, opération)."""
    for chemin, methodes in schema["paths"].items():
        for methode, operation in methodes.items():
            if methode in METHODES_HTTP:
                yield methode, chemin, operation


def operations_metier(schema):
    """Les opérations sur les astronautes et les missions."""
    for methode, chemin, operation in operations(schema):
        if chemin.startswith(("/api/astronautes", "/api/missions")):
            yield methode, chemin, operation


def exemple_documente(operation, code):
    return operation["responses"][str(code)]["content"]["application/json"]["example"]


# Vérifie que le titre, la description et la version de l'application
# apparaissent dans le schéma.
def test_informations_generales(schema):
    assert schema["info"]["title"] == "Annuaire des astronautes"
    assert schema["info"]["description"]
    assert schema["info"]["version"] == "1.0.0"


# Vérifie que chaque opération porte une seule étiquette, et qu'elle fait
# partie des groupes déclarés dans `openapi_tags` (sinon Swagger UI crée un
# groupe sans description).
def test_chaque_operation_est_rangee_dans_un_groupe_declare(schema):
    declarees = {tag["name"] for tag in schema["tags"]}
    assert declarees == {"Astronautes", "Missions", "Technique"}

    for methode, chemin, operation in operations(schema):
        assert len(operation.get("tags", [])) == 1, (methode, chemin)
        assert operation["tags"][0] in declarees, (methode, chemin)


# Vérifie que chaque route métier a un résumé et une description écrits à la
# main, pas seulement le nom de la fonction que FastAPI met par défaut.
def test_routes_metier_ont_resume_et_description(schema):
    for methode, chemin, operation in operations_metier(schema):
        assert operation.get("summary"), (methode, chemin)
        assert operation.get("description"), (methode, chemin)


# Vérifie que chaque paramètre de chemin (`id_astronaute`, `id_mission`) est
# décrit : c'est ce que lit l'utilisateur de /docs avant de remplir le champ.
def test_parametres_de_chemin_sont_decrits(schema):
    sans_description = [
        (methode, chemin, parametre["name"])
        for methode, chemin, operation in operations(schema)
        for parametre in operation.get("parameters", [])
        if parametre["in"] == "path" and not parametre.get("description")
    ]
    assert sans_description == []


# Vérifie que les champs d'entrée des astronautes sont décrits et ont un exemple.
@pytest.mark.parametrize("champ", ["nom", "role", "nationalite", "qualification"])
def test_champs_astronaute_decrits_avec_exemple(schema, champ):
    propriete = schema["components"]["schemas"]["AstronauteEntree"]["properties"][champ]
    assert propriete.get("description"), champ
    assert propriete.get("examples"), champ


# Vérifie que chaque exemple de champ est accepté par le champ lui-même :
# un exemple que l'API refuserait induit en erreur celui qui le recopie.
# Seul AstronauteEntree porte des exemples : dans les modèles Patch, ils sont
# enfouis dans `Nom | SkipJsonSchema[None]`, hors de portée de `info.examples`.
@pytest.mark.parametrize("modele", [AstronauteEntree])
def test_exemples_des_champs_sont_valides(modele):
    verifies = 0
    invalides = []
    for champ, info in modele.model_fields.items():
        # Annotated[type, FieldInfo] reconstruit le champ avec ses contraintes
        # et ses validateurs, sans le reste du modèle.
        adaptateur = TypeAdapter(Annotated[info.annotation, info])
        for exemple in info.examples or []:
            verifies += 1
            try:
                adaptateur.validate_python(exemple, strict=True)
            except ValidationError:
                invalides.append((champ, exemple))
    # Sans exemple, la boucle ne vérifie rien et le test passerait toujours.
    assert verifies > 0
    assert invalides == []


# Vérifie que l'exemple documenté pour le 422 a la même forme que la réponse
# réelle à un corps invalide.
@pytest.mark.parametrize("chemin", ["/api/astronautes", "/api/missions"])
def test_exemple_422_a_la_forme_de_la_vraie_reponse(schema, client_authentifie, chemin):
    exemple = exemple_documente(schema["paths"][chemin]["post"], 422)

    reponse = client_authentifie.post(chemin, json={})

    assert reponse.status_code == 422
    assert set(reponse.json()) == set(exemple)


# Vérifie que le 400 documenté est bien celui que renvoie FastAPI quand le
# corps n'est pas un texte UTF-8 lisible : même code, même message.
@pytest.mark.parametrize("chemin", ["/api/astronautes", "/api/missions"])
def test_exemple_400_a_la_forme_de_la_vraie_reponse(schema, client_authentifie, chemin):
    exemple = exemple_documente(schema["paths"][chemin]["post"], 400)

    reponse = client_authentifie.post(
        chemin, content=b"\x80", headers={"Content-Type": "application/json"}
    )

    assert reponse.status_code == 400
    assert reponse.json() == exemple


# Vérifie que chaque écriture documente son 401, et que l'exemple est
# exactement la réponse réelle à une requête sans jeton.
@pytest.mark.parametrize(
    "methode, chemin_doc, chemin_reel",
    [
        ("post", "/api/astronautes", "/api/astronautes"),
        ("put", "/api/astronautes/{id_astronaute}", "/api/astronautes/1"),
        ("patch", "/api/astronautes/{id_astronaute}", "/api/astronautes/1"),
        ("delete", "/api/astronautes/{id_astronaute}", "/api/astronautes/1"),
        ("post", "/api/missions", "/api/missions"),
        ("put", "/api/missions/{id_mission}", "/api/missions/1"),
        ("patch", "/api/missions/{id_mission}", "/api/missions/1"),
        ("delete", "/api/missions/{id_mission}", "/api/missions/1"),
    ],
)
def test_exemple_401_est_la_vraie_reponse(schema, client, methode, chemin_doc, chemin_reel):
    exemple = exemple_documente(schema["paths"][chemin_doc][methode], 401)

    reponse = client.request(methode, chemin_reel)

    assert reponse.status_code == 401
    assert reponse.json() == exemple


# Vérifie que les lectures ne documentent pas de 401 : elles restent ouvertes.
def test_lectures_ne_documentent_pas_401(schema):
    for methode, chemin, operation in operations_metier(schema):
        if methode == "get":
            assert "401" not in operation["responses"], chemin


# Vérifie que les listes documentent leurs deux formats de 422, et que chaque
# exemple a la forme de la vraie réponse : paramètre invalide, limite trop grande.
@pytest.mark.parametrize("chemin", ["/api/astronautes", "/api/missions"])
@pytest.mark.parametrize(
    "exemple, parametres", [("validation", "limite=0"), ("limite", "limite=101")]
)
def test_exemples_422_de_pagination(schema, client, chemin, exemple, parametres):
    documente = schema["paths"][chemin]["get"]["responses"]["422"]
    attendu = documente["content"]["application/json"]["examples"][exemple]["value"]

    reponse = client.get(f"{chemin}?{parametres}")

    assert reponse.status_code == 422
    assert set(reponse.json()) == set(attendu)
    if exemple == "limite":
        assert reponse.json() == attendu


# Vérifie que les paramètres de pagination sont décrits dans le schéma.
@pytest.mark.parametrize("chemin", ["/api/astronautes", "/api/missions"])
def test_parametres_de_pagination_decrits(schema, chemin):
    parametres = {p["name"]: p for p in schema["paths"][chemin]["get"]["parameters"]}

    for nom in ("limite", "decalage"):
        assert parametres[nom].get("description"), nom


# Vérifie que l'exemple documenté pour le 404 parle de la bonne ressource :
# même clé et même début de message que la vraie réponse.
@pytest.mark.parametrize(
    "chemin_doc, chemin_reel",
    [
        ("/api/astronautes/{id_astronaute}", "/api/astronautes/999"),
        ("/api/missions/{id_mission}", "/api/missions/999"),
    ],
)
def test_exemple_404_decrit_la_bonne_ressource(schema, client, chemin_doc, chemin_reel):
    exemple = exemple_documente(schema["paths"][chemin_doc]["get"], 404)

    reponse = client.get(chemin_reel)

    assert reponse.status_code == 404
    assert set(reponse.json()) == set(exemple)
    # « L'astronaute 999 n'existe pas » → « L'astronaute »
    debut_reel = reponse.json()["erreur"].split(" 999")[0]
    assert exemple["erreur"].startswith(debut_reel)


# Vérifie que l'exemple documenté pour le 409 de suppression a la forme de la
# vraie réponse, obtenue en supprimant Apollo 11, qui a un équipage.
def test_exemple_409_de_suppression_est_la_vraie_reponse(schema, client_authentifie):
    exemple = exemple_documente(schema["paths"]["/api/missions/{id_mission}"]["delete"], 409)

    reponse = client_authentifie.delete("/api/missions/1")

    assert reponse.status_code == 409
    assert reponse.json() == {"erreur": exemple["erreur"].replace("42", "1")}


# Vérifie qu'une liste ne documente pas de 404 : un filtre sans résultat
# répond 200 et une liste vide. Sophie Adenot, seule spécialiste du jeu de
# démonstration, est supprimée d'abord ; aucune mission ne date de 2100.
@pytest.mark.parametrize(
    "chemin, a_supprimer, filtre",
    [
        ("/api/astronautes", "/api/astronautes/3", "role=specialiste"),
        ("/api/missions", None, "annee=2100"),
    ],
)
def test_liste_ne_documente_pas_404(schema, client_authentifie, chemin, a_supprimer, filtre):
    if a_supprimer:
        assert client_authentifie.delete(a_supprimer).status_code == 204

    reponse = client_authentifie.get(f"{chemin}?{filtre}")
    assert reponse.status_code == 200
    assert reponse.json() == []

    assert "404" not in schema["paths"][chemin]["get"]["responses"]


# Vérifie qu'aucune création ne documente de 409 : rien n'interdit les
# doublons, deux créations identiques réussissent toutes les deux.
@pytest.mark.parametrize(
    "chemin, corps",
    [
        (
            "/api/astronautes",
            {
                "nom": "Edgar Mitchell",
                "role": "pilote",
                "nationalite": "Etats-Unis",
                "qualification": {"type": "pilote", "heures_vol": 1500, "appareil": "T-38"},
            },
        ),
        ("/api/missions", {"nom": "Apollo 18", "annee": 1975}),
    ],
)
def test_aucun_conflit_documente(schema, client_authentifie, chemin, corps):
    assert "409" not in schema["paths"][chemin]["post"]["responses"]

    assert client_authentifie.post(chemin, json=corps).status_code == 201
    assert client_authentifie.post(chemin, json=corps).status_code == 201


# Vérifie que le 422 de cohérence rôle / qualification, levé dans la route
# PATCH, est documenté avec son format {"erreur": ...}.
def test_422_de_coherence_documente_sur_le_patch(schema, client_authentifie):
    reponse = client_authentifie.patch("/api/astronautes/2", json={"role": "specialiste"})
    assert reponse.status_code == 422
    assert set(reponse.json()) == {"erreur"}

    documente = schema["paths"]["/api/astronautes/{id_astronaute}"]["patch"]["responses"]["422"]
    formes = documente["content"]["application/json"]["schema"]["anyOf"]
    assert {"$ref": "#/components/schemas/Erreur"} in formes


# Vérifie que protéger la documentation en production ne protège que la
# documentation : les routes de lecture de l'API répondent toujours.
def test_api_disponible_en_production_sans_documentation():
    client = TestClient(creer_app("production"))

    assert client.get("/docs").status_code == 401
    assert client.get("/api/technique/sante").status_code == 200
    assert client.get("/api/astronautes").status_code == 200


# Vérifie que creer_app accepte directement une classe de configuration, et
# pas seulement un nom d'environnement.
def test_creer_app_accepte_une_classe_de_configuration():
    client = TestClient(creer_app(ConfigProduction))

    assert client.get("/openapi.json").status_code == 401
