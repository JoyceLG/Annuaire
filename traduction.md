# Traduction Flask → FastAPI

> Une ligne par concept. La colonne **Pourquoi c'est différent** est la plus
> importante : sans elle, je mémorise deux syntaxes au lieu de comprendre deux
> modèles. Je ne remplis une ligne que quand je l'ai réellement écrite en
> FastAPI — pas avant.

**Légende de l'état :** ⬜ pas encore vu · 🟡 vu en théorie · ✅ écrit et compris

---

## 1 — Protocole et serveur

*Rempli en session 22.*

| Concept | En Flask | En FastAPI | Pourquoi c'est différent | État |
|---|---|---|---|---|
| Protocole entre serveur et application | WSGI. L'application est un appelable qui reçoit `environ` et **retourne** la réponse. | ASGI. L'application est une coroutine qui reçoit `scope`, `receive`, `send` et **émet** des événements | WSGI n'a pas de mot pour dire « attends-moi » : le contrat exige les octets tout de suite, il n'existe pas de point de suspension. ASGI est un flux d'événements, donc la coroutine peut rendre la main pendant une attente. | 🟡 |
| Serveur de production | Gunicorn | Uvicorn (seul, ou comme workers de Gunicorn) | Gunicorn est un serveur WSGI synchrone, adapté à Flask. Uvicorn est un serveur ASGI, adapté à FastAPI. Starlette n'est pas un serveur : c'est la couche web ASGI sur laquelle FastAPI est construit. | 🟡 |
| Modèle de concurrence | Modèle pre-fork synchrone : chaque worker traite une requête à la fois | Modèle asynchrone : un worker peut gérer plusieurs requêtes simultanément grâce aux coroutines | Le modèle WSGI bloque le worker sur chaque requête, limitant le débit. ASGI permet de libérer le worker pendant les opérations d'attente, augmentant le nombre de requêtes traitées simultanément. | 🟡 |
| Ce qui limite le débit | Le nombre de processus que l'infrastructure supporte. Le débit vaut workers ÷ durée de la requête : 8 requêtes/s mesurées avec 4 workers sur une route à 500 ms, et pas plus de 5 workers à cause de `max_connections` de PostgreSQL. | Ce qui est en aval de l'application : le nombre de connexions que PostgreSQL accepte, le débit de l'API externe interrogée, la bande passante. | Le goulot d'étranglement se déplace. En WSGI, une requête qui attend immobilise un processus entier : le plafond, c'est le nombre de processus. En ASGI, une requête qui attend n'est qu'une coroutine de quelques kilooctets : ce plafond disparaît, et la limite devient la capacité des ressources partagées derrière l'application. | 🟡 |
| Cycle de vie de l'application : où ouvrir et fermer le pool de connexions | Aucun point d'accroche prévu. Le moteur SQLAlchemy est créé dans `creer_app`, et `teardown_appcontext` ferme la session à chaque requête : c'est un mécanisme par requête, pas par application. Les extensions s'arrangent avec `init_app` et des variables de module. | Le scope `lifespan` d'ASGI, que FastAPI expose comme un gestionnaire de contexte : `@asynccontextmanager async def lifespan(app):` ouvre le pool et le client HTTP partagé avant le `yield`, et les ferme après. | Flask n'a de point d'accroche qu'au niveau de la requête, pas de l'application : le démarrage et l'arrêt sont laissés à l'initiative du code. ASGI en fait un type de scope du protocole : le serveur l'ouvre avant d'accepter la moindre requête, attend `startup.complete`, sert le trafic, puis envoie `shutdown` à l'arrêt. Il garantit donc que ce code s'exécute avant la première requête et après la dernière. | 🟡 |
| WebSocket | Compensé par des bibliothèques tierces comme Flask-SocketIO | Supporté nativement via ASGI | WSGI ne gère pas les connexions persistantes comme WebSocket. ASGI permet de gérer les connexions WebSocket de manière asynchrone et bidirectionnelle. | 🟡 |

---

## 2 — Routage et réponses

*Rempli en session 23.*

| Concept | En Flask | En FastAPI | Pourquoi c'est différent | État |
|---|---|---|---|---|
| Déclarer une route | `@bp.get("/astronautes/<int(min=1):id_astronaute>")` sur un Blueprint ; la fonction lit elle-même ce dont elle a besoin (`request.args`, `lire_corps`). | `@router.get("/api/astronautes/{id_astronaute}", response_model=AstronauteSortie)` ; la signature déclare les entrées : `def lire_astronaute(id_astronaute: int)`. | En Flask, le décorateur ne donne que le chemin et la méthode. En FastAPI, la route porte son contrat : la signature décrit ce qui entre, le décorateur ce qui sort (`response_model`, `status_code`). FastAPI lit les annotations pour valider avant d'appeler la fonction. | ✅ |
| Grouper des routes | `Blueprint("astronautes", __name__, url_prefix=PREFIXE_API)`, enregistré par `app.register_blueprint` dans `creer_app`. | `router = APIRouter()` dans chaque module de `routes/`, ajouté par `app.include_router(astronautes.router)` dans `main.py`. | Même idée : un module par ressource, branché sur l'application. Le Blueprint a un nom, qui sert à `url_for("astronautes.lire")` ; l'APIRouter n'est qu'une liste de routes recopiées dans l'application. Ici le préfixe `/api` est écrit dans chaque chemin, alors que Flask le met une fois dans `url_prefix`. | ✅ |
| Paramètre d'URL typé | Convertisseur dans le chemin : `<int(min=1):id_astronaute>`. Une valeur qui ne convient pas ne correspond à aucune route : **404**. | Accolades dans le chemin, type dans la signature : `{id_astronaute}` et `id_astronaute: int`. `/api/astronautes/armstrong` donne **422**. | Flask choisit la route avec le convertisseur : une valeur invalide, c'est une route qui n'existe pas. FastAPI trouve la route d'abord, puis valide le paramètre avec Pydantic : c'est une donnée invalide, donc une erreur de validation. | ✅ |
| Paramètre de query string | `request.args.get("role")` : toujours une chaîne ou `None`, la conversion et le contrôle sont à faire à la main. | Un paramètre de la signature absent du chemin : `role: Role \| None = None`. `?role=cosmonaute` donne **422**. | FastAPI déduit l'origine du paramètre de sa place : dans le chemin, c'est un paramètre d'URL ; sinon, c'est la query string. Le type annoncé est vérifié, et la valeur par défaut le rend facultatif. | ✅ |
| Accéder à l'objet requête | Le global `request`, importé de `flask` : un proxy vers la requête en cours (contexte de requête). | Un paramètre typé `request: Request`, que FastAPI fournit : c'est ce que reçoit `gerer_astronaute_introuvable`. | Flask range la requête dans un contexte attaché au thread qui la traite. FastAPI la passe explicitement à qui la demande : rien de caché, et rien qui dépende du thread, ce qui convient aux coroutines. | ✅ |
| Renvoyer du JSON | Renvoyer un dict ou une liste : Flask le convertit en JSON. Le filtrage se fait à la main, avec `en_dict()`. | Renvoyer un dict : FastAPI le valide contre `response_model`, puis le sérialise. `note_interne` disparaît de la réponse sans code supplémentaire. | En Flask, ce que la fonction renvoie part tel quel. En FastAPI, `response_model` est un contrat de sortie : un champ qu'il ne déclare pas est retiré, et un champ obligatoire manquant fait échouer la réponse (500) au lieu de partir incomplet. | ✅ |
| Choisir le code de statut | Deuxième élément du tuple renvoyé : `return astronaute.en_dict(), 201, {...}`. | Dans le décorateur : `@router.post(..., status_code=201)`, `@router.delete(..., status_code=204)`. | En FastAPI, le code d'une route qui réussit est fixé à sa déclaration, au même endroit que le reste de son contrat. Flask le décide au moment du `return`, ce qui le rend plus libre mais moins visible. | ✅ |
| Ajouter un en-tête de réponse | Troisième élément du tuple : `{"Location": url_for("astronautes.lire", id_astronaute=...)}`. | Demander `response: Response` dans la signature, puis `response.headers["Location"] = f"/api/astronautes/{prochain_id}"`. | En FastAPI, la valeur renvoyée n'est que le corps : pour toucher aux en-têtes, il faut demander l'objet réponse, que FastAPI fusionne ensuite avec le corps sérialisé. C'est le même mécanisme d'injection par le type que pour `Request`. | ✅ |
| Lever une erreur HTTP |  |  |  |  |
| Gestionnaire d'erreur centralisé | `@app.errorhandler(AstronauteIntrouvable)` dans `enregistrer_gestionnaires(app)` ; la fonction reçoit l'exception et renvoie `({"erreur": ...}, 404)`. | `@app.exception_handler(AstronauteIntrouvable)` dans `enregistrer_gestionnaires(app)` ; la fonction reçoit `(request, erreur)` et renvoie `JSONResponse(status_code=404, content={"erreur": ...})`. | Même organisation : la route lève une exception métier, un gestionnaire la traduit en HTTP. Le gestionnaire FastAPI construit lui-même la réponse (pas de tuple converti), et reçoit la requête en paramètre au lieu de la lire dans un global. | ✅ |
| Créer l'application | Une fabrique : `creer_app(config, **surcharges)` crée `Flask(__name__)`, lit la configuration, enregistre blueprints et gestionnaires. | Une instance au niveau du module, dans `main.py` : `app = FastAPI(title="Annuaire des astronautes", version="0.1.0")`, puis `include_router` et `enregistrer_gestionnaires(app)`. | La fabrique Flask existe pour choisir la configuration à la création (environnement, base des tests). Le projet FastAPI n'a encore ni configuration ni base : une instance de module suffit, et les tests remettent les données à zéro par une fixture plutôt que de créer une application neuve. | ✅ |
| Lancer le serveur de développement | `flask run --debug`, avec `FLASK_APP="annuaire:creer_app"` dans `.env` ; serveur de développement de Werkzeug. | `fastapi dev main.py`, qui trouve `app` dans `main.py` ; port 8000. | `fastapi dev` lance Uvicorn, le serveur ASGI, avec rechargement automatique : c'est le même serveur qu'en production, alors que celui de Flask n'est fait que pour le développement. | ✅ |

---

## 3 — Validation et sérialisation

*Rempli en session 24.*

| Concept | En Flask | En FastAPI | Pourquoi c'est différent | État |
|---|---|---|---|---|
| Lire et valider le corps JSON | `champs = lire_corps(schemas.AstronauteEntree)` : `request.get_json(silent=True)`, refus d'un corps qui n'est pas un objet, puis `model_validate` dans un `try/except ValidationError`. | Un paramètre annoté par le modèle : `def creer_astronaute(entree: AstronauteEntree, ...)`. La route reçoit un objet déjà validé. | Pydantic est le même des deux côtés : seul change qui l'appelle. En Flask, c'est mon code (`lire_corps`, une trentaine de lignes) ; en FastAPI, c'est le framework, avant même d'appeler la route. Un paramètre typé par un `BaseModel` est lu dans le corps, comme un `int` hors du chemin est lu dans la query string. | ✅ |
| Champs obligatoires | Un champ sans valeur par défaut dans le modèle : `nom: Nom`. | Identique : `nom: Nom`. Un champ absent donne 422 et rien n'est créé. | Aucune différence de déclaration : c'est Pydantic qui décide. La différence est dans la réponse (400 contre 422, voir plus bas). | ✅ |
| Contraintes sur un champ | Types réutilisables avec `Annotated` : `Nom = Annotated[str, StringConstraints(...), AfterValidator(_non_vide)]`. | Les mêmes types `Annotated`, partagés par l'entrée et le PATCH : `Nom = Annotated[str, BeforeValidator(nettoyer), StringConstraints(min_length=1, max_length=LONGUEUR_NOM)]`. | Même Pydantic, donc mêmes outils. L'ordre change : en Flask, `AfterValidator(_non_vide)` contrôle après coup que la valeur nettoyée n'est pas vide ; ici, `BeforeValidator` nettoie la valeur brute avant le contrôle de longueur, donc `"   "` devient `""`, que `min_length=1` refuse sans validateur supplémentaire. | ✅ |
| Valeurs autorisées (énumération) | `RoleAstronaute = Literal["commandant", "pilote", "specialiste"]` dans `contraintes.py`. | Le même `Literal`, utilisé à la fois dans le schéma et comme type du paramètre de query `role`. `?role=cosmonaute` et `{"role": "cosmonaute"}` donnent 422. | Un `Literal` n'est pas une `Enum` : il n'y a pas d'attribut `RoleAstronaute.PILOTE`, on compare à la chaîne `"pilote"`. En FastAPI, le même type valide le corps et la query string, alors qu'en Flask la query string se contrôle à la main. | ✅ |
| Refuser les champs inconnus | `model_config = ConfigDict(extra="forbid", strict=True)`. | Identique. `{"salaire": ...}` donne 422 ; `strict=True` refuse `"1971"` pour une année et `42` pour un nom. | Configuration du modèle, donc identique. Sans `strict`, Pydantic convertirait `"1971"` en `1971` sans le dire. | ✅ |
| Modification partielle (PATCH) | `lire_corps(schemas.AstronautePatch, partiel=True)`, qui fait `model_dump(exclude_unset=partiel)` une fois pour toutes les routes. Corps vide refusé dans `lire_corps`. | Champs `X \| None = None`, `@model_validator(mode="after")` qui refuse un corps vide (`model_fields_set`) et un `null` envoyé, puis `entree.model_dump(exclude_unset=True)` **dans chaque route**. | `model_fields_set` distingue « absent » de « envoyé à `null` », que la valeur par défaut `None` confond. En Flask, `exclude_unset` vivait dans un seul helper ; en FastAPI, chaque route PATCH doit y penser : l'oublier écrase les champs absents par `None` et la réponse plante (piège rencontré sur les missions). | ✅ |
| Validation qui croise plusieurs champs | Pas de cas dans le projet Flask. | `@model_validator(mode="after")` sur `AstronauteEntree` : la qualification doit être admise par le rôle (`QUALIFICATIONS_PAR_ROLE`, `verifier_qualification`). En PATCH, la vérification se fait dans la route, sur `{**astronaute, **modifications}`. | Un schéma ne voit que le corps de la requête. Quand le PATCH n'envoie que le rôle, la qualification à comparer est celle qui est enregistrée : seule la route y a accès. `QualificationIncoherente` hérite de `ValueError` pour servir aux deux endroits : Pydantic la convertit en erreur de validation, et dans la route son gestionnaire répond 422. | ✅ |
| Champ dont la forme dépend d'un type (union discriminée) | Pas de cas dans le projet Flask. | `Qualification = Annotated[QualificationPilote \| QualificationScientifique \| QualificationIngenieur, Field(discriminator="type")]`, chaque classe ayant son `type: Literal["pilote"]`, `Literal["scientifique"]` ou `Literal["ingenieur"]`. | Le discriminateur lit `type` et ne valide que contre la classe correspondante : les erreurs portent sur le bon modèle, et un type inconnu (`"cuisinier"`) donne 422. Il valide la forme de la qualification, pas son adéquation au rôle (ligne précédente). | ✅ |
| Filtrer les champs de sortie | `en_dict()` sur le modèle SQLAlchemy, écrit à la main, champ par champ. | `response_model=AstronauteSortie` : `qualification` et `note_interne` sont retirées sans code. | Le contrat de sortie est un modèle séparé du modèle d'entrée : l'API accepte une qualification sans la renvoyer. En Flask, un champ ajouté au modèle n'apparaît que si je pense à l'ajouter dans `en_dict`. | ✅ |
| Champ calculé en sortie | `programme` calculé par `calculer_programme(nom)` dans `donnees/missions.py`, puis stocké en base. | `@computed_field` sur le modèle de sortie : `initiales` (astronautes), `programme` (missions). Rien n'est stocké. | Calculé à la sortie, le champ ne peut pas diverger de ce dont il dépend : un PATCH du nom change le programme sans autre code. En Flask, stocker la valeur permet de filtrer dessus en SQL, au prix de la recalculer à chaque modification. | ✅ |
| Format des erreurs de validation | `{"erreur": "Validation échouée", "details": {"nom": "..."}}`, construit par `convertir_erreurs`. | `{"detail": [{"type", "loc", "msg", "input", ...}]}` : la liste de `erreur.errors()` telle quelle. Les erreurs levées dans une route (`QualificationIncoherente`) répondent `{"erreur": "..."}`. | FastAPI expose le format de Pydantic sans le transformer : plus détaillé (type d'erreur, chemin complet, valeur reçue), mais il n'a pas la forme du reste de mon API. Le projet a donc deux formats d'erreur 422, selon que l'erreur vient du schéma ou de la route. | ✅ |
| Code de statut d'une erreur de validation | 400, par le gestionnaire de `DonneesInvalides`. | 422 Unprocessable Entity, y compris pour un JSON mal formé ou un paramètre d'URL invalide. | 400 dit « requête mal formée » ; 422 dit « requête bien formée mais contenu refusé ». FastAPI fait ce choix pour toute erreur de validation, donc les clients et les tests attendent 422. | ✅ |
| Traduire les erreurs vers mon format | `convertir_erreurs(erreur)` appelé dans `lire_corps`, avant de lever `DonneesInvalides`. | `@app.exception_handler(RequestValidationError)` dans `enregistrer_gestionnaires`. Pour l'instant, il renvoie `{"detail": jsonable_encoder(erreur.errors())}`, le format d'origine. | La validation se fait avant la route : impossible de l'entourer d'un `try/except`. Le seul point d'accroche est le gestionnaire de `RequestValidationError`. `jsonable_encoder` est nécessaire car `errors()` peut contenir des objets non sérialisables (l'exception dans `ctx`). | ✅ |

---

## 4 — Documentation

*Rempli en session 25.*

| Concept | En Flask | En FastAPI | Pourquoi c'est différent | État |
|---|---|---|---|---|
| Schéma OpenAPI | Aucun. Le contrat de l'API n'existe que dans le README et dans `annuaire.http`, écrits à la main. | Généré par `app.openapi()` à partir des routes, des annotations et des modèles Pydantic, servi sur `/openapi.json`. `FastAPI(title=..., description=..., version=..., openapi_tags=[...])` en remplit l'en-tête et décrit les groupes. | FastAPI connaît déjà le contrat de chaque route pour la valider (signature, `response_model`, `status_code`) : le publier ne coûte rien. Flask ne sait pas ce qu'une vue lit ou renvoie : `lire_corps` est appelé dans le corps de la fonction, hors de vue du framework. | ✅ |
| Interface de test interactive | `annuaire.http` : des requêtes recopiées à la main, à tenir à jour à chaque nouvelle route. | Swagger UI sur `/docs` et ReDoc sur `/redoc`, construits tous les deux à partir de `/openapi.json`. « Try it out » envoie une vraie requête à l'application. | Les deux interfaces lisent le schéma : une route ajoutée y apparaît sans rien écrire. Le fichier `.http` ne connaît que ce que j'y ai recopié. | ✅ |
| Décrire une route | Une docstring, lue seulement par qui ouvre le code. | `summary=` dans le décorateur, la docstring pour la description ; `APIRouter(tags=["Astronautes"], prefix="/api/astronautes")` range toutes les routes du module dans un groupe. | La docstring devient de la documentation publique. `description=` dans le décorateur l'emporterait sur elle : écrire les deux, c'est maintenir deux fois le même texte, d'où la docstring seule. Le `prefix` de l'`APIRouter` joue le rôle de l'`url_prefix` du Blueprint. | ✅ |
| Décrire un champ | Rien n'est exposé : les modèles de `schemas.py` ne servent qu'à valider. | `Field(description=..., examples=[...])` dans les types `Annotated` (`Nom`, `Role`, `Nationalite`, `Qualification`) ; `Query(description=...)` et `Path(description=...)` pour les paramètres. | Pydantic produit le JSON Schema de chaque modèle, que FastAPI recopie dans `components/schemas` : les contraintes (`minLength`, `enum`, discriminateur) y figurent sans les écrire. `description` et `examples` sont du texte libre : rien ne vérifie qu'un exemple passe la validation. Et ce qui est du code n'apparaît pas : le schéma ignore `BeforeValidator(nettoyer)` et la règle rôle ↔ qualification. | ✅ |
| Documenter les réponses d'erreur | Les codes d'erreur ne sont visibles que dans `gestionnaires.py` et le README. | `responses={**REPONSE_404_ASTRONAUTE, **REPONSE_422}` sur chaque route, avec des fragments réutilisables dans `documentation.py` : un modèle Pydantic du corps d'erreur (`"model": Erreur`), une description et un exemple. Le PATCH d'un astronaute déclare ses deux formats de 422 : `ErreurValidation \| Erreur`. | FastAPI ne documente seul que le code de succès et un 422 au format de `RequestValidationError` (`HTTPValidationError`). Une erreur levée par exception (`AstronauteIntrouvable` → 404) passe par un gestionnaire que FastAPI ne relie pas à la route : il faut la déclarer. Ce qui est déclaré n'est pas vérifié, et déclarer un 422 remplace le schéma `HTTPValidationError` généré : sans `model`, la réponse n'a plus de schéma, seulement un exemple que personne ne contrôle. | ✅ |
| Garder la doc synchronisée avec le code | Discipline : relire le README et `annuaire.http` à chaque changement. | La partie générée suit le code. La partie écrite à la main est vérifiée par des tests : `test_documentation.py` (exemples valides, exemples d'erreur conformes aux vraies réponses). | Le schéma est dérivé du code, pas recopié : chemins, paramètres, modèles et codes de succès ne peuvent pas diverger. Restent les déclarations à la main (`responses=`, `examples`), que seuls des tests confrontent à l'application. Et le schéma ne voit pas les règles écrites en code : un corps conforme peut être refusé à juste titre (`"   "`), et un corps non conforme accepté (espace en tête retiré avant le contrôle de longueur). | 🟡 |
| Exposition de la doc en production | Pas de documentation à protéger. Même réflexe pour les routes de débogage : le blueprint `debogage` n'est enregistré que si `DEBUG` est actif. | `DOCUMENTATION_PUBLIQUE` vrai (développement, test) : FastAPI sert `/docs`, `/redoc` et `/openapi.json`. Faux (production) : `docs_url`, `redoc_url` et `openapi_url` à `None`, et `routes/documentation.py` sert les trois routes derrière une connexion. Un formulaire envoie le jeton à `POST /docs/connexion`, qui pose un cookie `httponly`, `secure`, `samesite=lax` ; `/openapi.json` accepte ce cookie ou l'en-tête `Authorization`. | Un navigateur qui ouvre `/docs` n'envoie pas d'en-tête `Authorization`, et Swagger UI charge ensuite `/openapi.json` par une requête séparée, sans en-tête non plus : protégée par l'en-tête seul, l'interface reste vide. Seuls les cookies du site partent d'eux-mêmes, d'où la connexion par cookie. Les routes de l'API, elles, n'acceptent que l'en-tête : un cookie part avec toute requête vers le site, même déclenchée par une page tierce, et les exposerait aux attaques CSRF. Sans `ENVIRONNEMENT`, c'est le développement qui est choisi, documentation ouverte : en production, la variable doit être exportée. | ✅ |

---

## 5 — Dépendances et configuration

*Rempli en session 26.*

| Concept | En Flask | En FastAPI | Pourquoi c'est différent | État |
|---|---|---|---|---|
| Fournir la session de base de données | `session_bdd()` dans `bdd.py`, appelée par la vue : crée la session à la demande et la range dans `g.bdd`. | Pas encore de base : `depot_astronautes()` et `depot_missions()` fournissent le dictionnaire de données, et chaque route le demande dans sa signature (`depot_astronautes: DepotAstronautesInjecte`). | En Flask, la vue va chercher la ressource dans un global. En FastAPI, la route déclare ce dont elle a besoin et le framework le lui passe : la dépendance se voit dans la signature, et un test peut la remplacer. Les routes ne lisent plus `ASTRONAUTES` directement. | 🟡 |
| Libérer une ressource en fin de requête | `app.teardown_appcontext(fermer_session)` : une fonction séparée, enregistrée sur l'application, qui retrouve la session dans `g` pour la fermer. | Une dépendance générateur : `yield` fournit la ressource, le code après le `yield`, dans un `finally`, la libère une fois la réponse prête. | L'ouverture et la fermeture vivent dans la même fonction, comme un gestionnaire de contexte : impossible d'ouvrir sans prévoir la fermeture. Le `finally` s'exécute même quand la route lève une exception (vérifié par un test sur un 404). | ✅ |
| Accéder à la configuration | `current_app.config["DUREE_JETON"]`, lu au moment de l'appel, n'importe où dans le code. | Une dépendance `configuration(request)` qui renvoie `request.app.state.config`, rangée là par `creer_app`. `pagination` la demande : `config: Annotated[type[Config], Depends(configuration)]`. | `current_app` est un proxy vers l'application de la requête en cours. FastAPI n'a pas de proxy : on passe par l'objet `Request`, injecté, et `request.app`. Relire `ENVIRONNEMENT` dans la dépendance aurait ignoré la classe passée à `creer_app(ConfigProduction)` : piège rencontré, corrigé et couvert par un test. | ✅ |
| État partagé par requête | `g` : `g.bdd`, `g.utilisateur`, `g.requete_id`, rempli par une fonction et lu par une autre pendant la même requête. | Le cache des dépendances : une dépendance demandée par plusieurs autres n'est exécutée qu'une fois par requête, et toutes reçoivent le même résultat (`Depends(..., use_cache=False)` pour l'appeler à chaque fois). | Pas de sac global où chacun range et reprend : la valeur circule par les paramètres, d'une dépendance à l'autre. Ce qu'une route utilise se lit dans sa signature, alors qu'un attribut de `g` peut avoir été posé n'importe où, ou pas du tout. | 🟡 |
| Remplacer une dépendance en test | Pas de mécanisme dédié : la fabrique reçoit des surcharges (`creer_app(ConfigTest, URL_BASE=...)`), et les fixtures préparent les données ou les en-têtes (`entetes_editeur`). | `app.dependency_overrides[authentification_requise] = lambda: None` dans la fixture `client_authentifie`, puis `app.dependency_overrides.clear()`. Même chose pour remplacer un dépôt par un faux jeu de données. | La clé est la fonction elle-même : il faut importer exactement celle qu'utilisent les routes (un import par un autre chemin de module donne une autre fonction, et le remplacement ne se fait pas). Le code de l'application ne change pas : seule la table de remplacement de l'instance de test est modifiée. | ✅ |
| Ressource partagée par l'application | `app.extensions["bdd"]` (moteur et fabrique de sessions), `app.extensions["hacheur"]`, remplis dans `creer_app` et relus par `current_app.extensions[...]`. | `app.state.config = config` dans `creer_app`, relu par `request.app.state.config` dans une dépendance. | Même idée, un espace de rangement attaché à l'application et non au module : deux applications (les tests en créent une par test) ne partagent rien. `app.state` est un simple objet à attributs ; on y accède par la requête, pas par un proxy global. | ✅ |
| Appliquer un traitement à toutes les routes | `app.before_request(refuser_par_defaut)` : exécuté avant chaque vue, il refuse toute vue sans `@publique` ni décorateur d'accès. | `APIRouter(dependencies=[Depends(authentification_requise)])` : les routes d'écriture vont dans le routeur `ecriture`, celles de lecture dans `lecture`. `FastAPI(dependencies=[...])` ferait de même pour toute l'application. | `before_request` voit toutes les requêtes et décide d'après `request.endpoint` : c'est ce qui permet le refus par défaut. La dépendance de routeur ne s'applique qu'aux routes de ce routeur : une écriture déclarée par erreur sur `lecture` serait ouverte. D'où `test_toutes_les_ecritures_exigent_un_jeton`, qui parcourt le schéma OpenAPI (`app.routes` ne liste plus les routes des routeurs inclus depuis FastAPI 0.141). En échange, la dépendance apparaît dans le schéma : l'en-tête `authorization` est documenté sur chaque écriture. | ✅ |

---

## 6 — Base de données et sécurité

*À remplir en session 27.*

| Concept | En Flask | En FastAPI | Pourquoi c'est différent | État |
|---|---|---|---|---|
| Session SQLAlchemy | | | | |
| Chargement des relations | | | | |
| Exiger une authentification | | | | |
| Récupérer l'utilisateur courant | | | | |
| Vérifier une permission | | | | |
| Refus par défaut (fail-closed) | | | | |
| Lire l'en-tête Authorization | | | | |

---

## 7 — Asynchrone

*À remplir en session 28.*

| Concept | En Flask | En FastAPI | Pourquoi c'est différent | État |
|---|---|---|---|---|
| Déclarer une route | | | | |
| Appeler un service externe | | | | |
| Effet d'un appel bloquant | | | | |
| Exécuter du code bloquant sans risque | | | | |
| Plusieurs appels en parallèle | | | | |
| Tâche après la réponse | | | | |

---

## 8 — Tests

*À remplir au fil des sessions.*

| Concept | En Flask | En FastAPI | Pourquoi c'est différent | État |
|---|---|---|---|---|
| Client de test | | | | |
| Tester une route async | | | | |
| Isoler la base de données | | | | |
| Remplacer une dépendance | | | | |
| Fixtures | | | | |

---

## Pièges rencontrés

> Un piège par ligne, à remplir **au moment où je le rencontre**, pas après
> coup. Formulation : le symptôme d'abord, la cause ensuite — c'est le
> symptôme que je reverrai en premier la prochaine fois.

| Symptôme observé | Cause réelle | Comment l'éviter |
|---|---|---|
| L'application ne démarre plus : `TypeError` à l'import de `contraintes.py`. | `Dict["commandant": "commandant", ...]` est une annotation de type mal écrite, pas un dictionnaire. | Une valeur s'écrit `{...}` ; le type se met en annotation : `QUALIFICATIONS_PAR_ROLE: dict[str, frozenset[str]] = {...}`. |
| `RoleAstronaute.PILOTE` lève `AttributeError`. | `RoleAstronaute` est un `Literal`, pas une `Enum`. | Comparer à la chaîne : `self.role == "pilote"`. |
| Un validateur du PATCH lit `self.qualification` et lève `AttributeError`. | Le validateur était sur `AstronautePatch`, qui n'avait pas ce champ. | Mettre un validateur sur le modèle qui porte tous les champs qu'il compare. |
| PATCH de `{"role": "specialiste"}` accepté alors que la qualification enregistrée est celle d'un pilote. | Le schéma ne voit que le corps envoyé, pas l'état stocké. | Vérifier dans la route, sur l'objet fusionné `{**stocke, **modifications}`, avant de l'enregistrer. |
| PATCH d'une mission avec le seul `nom` : `ResponseValidationError`, `annee` vaut `None`. | `entree.model_dump()` sans `exclude_unset=True` : les champs absents sont écrits avec leur défaut `None`. | Toujours `model_dump(exclude_unset=True)` en PATCH. |
| `DELETE` répond 200 avec un corps `null`. | Pas de `status_code=204` dans le décorateur : FastAPI sérialise le `None` renvoyé. | Déclarer `status_code=204` sur toute route qui ne renvoie rien. |

---

## Réflexes Flask à désapprendre

> Les automatismes qui produisent du code faux ou inutile en FastAPI.
> Je remplis quand je me surprends à le faire.

| Le réflexe | Ce qu'il faut faire à la place |
|---|---|
| Lire le corps à la main puis l'envoyer à `model_validate` dans un `try/except ValidationError`. | Annoter le paramètre de la route avec le modèle : FastAPI valide avant l'appel. |
| Compter sur un helper (`lire_corps(..., partiel=True)`) pour exclure les champs absents d'un PATCH. | Écrire `model_dump(exclude_unset=True)` dans chaque route PATCH. |
| Attendre 400 sur une donnée invalide. | Attendre 422. |

---

## Ce que Flask fait mieux

> À remplir honnêtement. Si cette section reste vide à la fin du programme,
> c'est que je n'ai pas cherché.

| Sujet | Pourquoi Flask s'en sort mieux |
|---|---|
| Un format d'erreur unique | Toutes les erreurs de validation passent par `lire_corps` et `DonneesInvalides` : un seul format, `{"erreur", "details"}`. En FastAPI, les erreurs du schéma (`{"detail": [...]}`) et celles levées dans une route (`{"erreur": ...}`) ont deux formes, sauf à réécrire le gestionnaire de `RequestValidationError`. |

---

## Note de décision — migrerais-je cette API ?

*Rédigée en session 22, relue et corrigée en fin de programme.*

**Mesures dont je dispose**

| Mesure | Valeur | Source |
|---|---|---|
| Débit sur une route d'attente (500 ms) | 8 requêtes/s avec 4 workers (4 / 0,5 s) | TD 22 |
| Débit sur une lecture rapide | 1476 requêtes/s | TD 21 |
| Coût d'une connexion (Argon2) | 170ms | session 15 |
| Plafond de workers (connexions PostgreSQL) | 5 | TD 21 |
| Lignes de plomberie de validation | 30 lignes | TD 22 |

**Ce que mon application passe son temps à faire**

<!-- Quelle proportion attend, quelle proportion calcule ? -->
Elle passe son temps à attendre les réponses des services externes et à gérer les connexions à la base de données.

**Ce que je gagnerais**

<!-- Chiffré quand c'est possible. -->
- Gain potentiel sur les routes d'attente : aujourd'hui 8 requêtes/s avec 4 workers, soit 2 par worker. Ce plafond vient du nombre de workers, pas de la machine : un worker asynchrone n'y serait pas tenu
- Gain potentiel sur les lectures rapides : jusqu'à 1476 requêtes/s (actuellement limité par le débit observé)

**Ce que ça coûterait**

<!-- Effort de migration, risques, ce qui est à retraduire. -->
- Effort de migration : réécriture des routes existantes pour qu'elles soient asynchrones, adaptation des tests et de la configuration du serveur.
- Risques : bugs liés à l'asynchronisme, incompatibilités avec certaines bibliothèques synchrones.
- Ce qui est à retraduire : toutes les routes et la logique de gestion des connexions à la base de données.

**Ma conclusion**

<!-- Il n'y a pas de bonne réponse attendue : c'est le raisonnement qui compte.
     Une réponse nuancée (migrer une partie seulement) est recevable si elle
     est argumentée. -->

Après avoir pesé les gains potentiels et les coûts, ma conclusion est nuancée : la migration complète vers FastAPI ne se justifie pas d'emblée, mais elle serait clairement bénéfique sur une partie ciblée de l'application. Le facteur déterminant est le profil des routes. Pour les routes d'attente (appels aux services externes, requêtes de 500 ms), le modèle synchrone de Flask bloque un worker entier pendant toute la durée de l'attente : le débit plafonne mécaniquement à 2 requêtes/s par worker (8 mesurées avec 4 workers), et je ne peux pas simplement multiplier les workers puisque PostgreSQL me limite à 5 connexions. C'est exactement le scénario où ASGI change la donne, car un worker peut libérer la main pendant l'attente et traiter d'autres requêtes en parallèle. Le gain y est donc structurel, pas cosmétique.

À l'inverse, sur les lectures rapides (1476 requêtes/s) et sur les opérations dominées par le calcul comme le hachage Argon2 (170 ms de CPU pur), l'asynchronisme n'apporte rien : un calcul bloquant reste bloquant, et l'exécuter dans une coroutine gèlerait même la boucle d'événements si je ne le déportais pas explicitement dans un thread. Pour ces routes, la migration serait un coût sans contrepartie. Il faut aussi mettre en face le prix réel du changement : réécriture des routes en `async`, adaptation des tests et de la configuration du serveur, et surtout le risque de mélanger du code bloquant avec des bibliothèques synchrones — une erreur silencieuse qui annule tous les bénéfices attendus.

Ma décision serait donc de migrer de façon incrémentale plutôt que d'un bloc : isoler les routes réellement dominées par l'attente et les basculer en premier, en gardant le reste inchangé tant que rien ne le justifie. Cette approche capture l'essentiel du gain là où il existe, limite la surface de risque, et me permet de mesurer un débit réel après migration avant de m'engager plus loin. Les 30 lignes de plomberie de validation économisées grâce à Pydantic sont un bonus appréciable, mais elles ne pèsent pas assez lourd à elles seules pour motiver une réécriture : c'est bien le comportement sous charge des routes d'attente qui porte la décision.



*Relecture en fin de programme :*

<!-- Est-ce que je répondrais pareil maintenant que je connais FastAPI ? -->
