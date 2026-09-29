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

*À remplir en session 23.*

| Concept | En Flask | En FastAPI | Pourquoi c'est différent | État |
|---|---|---|---|---|
| Déclarer une route | | | | |
| Grouper des routes | | | | |
| Paramètre d'URL typé | | | | |
| Paramètre de query string | | | | |
| Accéder à l'objet requête | | | | |
| Renvoyer du JSON | | | | |
| Choisir le code de statut | | | | |
| Ajouter un en-tête de réponse | | | | |
| Lever une erreur HTTP | | | | |
| Gestionnaire d'erreur centralisé | | | | |
| Créer l'application | | | | |
| Lancer le serveur de développement | | | | |

---

## 3 — Validation et sérialisation

*À remplir en session 24.*

| Concept | En Flask | En FastAPI | Pourquoi c'est différent | État |
|---|---|---|---|---|
| Lire et valider le corps JSON | | | | |
| Champs obligatoires | | | | |
| Contraintes sur un champ | | | | |
| Valeurs autorisées (énumération) | | | | |
| Refuser les champs inconnus | | | | |
| Modification partielle (PATCH) | | | | |
| Filtrer les champs de sortie | | | | |
| Format des erreurs de validation | | | | |
| Code de statut d'une erreur de validation | | | | |
| Traduire les erreurs vers mon format | | | | |

---

## 4 — Documentation

*À remplir en session 25.*

| Concept | En Flask | En FastAPI | Pourquoi c'est différent | État |
|---|---|---|---|---|
| Schéma OpenAPI | | | | |
| Interface de test interactive | | | | |
| Décrire une route | | | | |
| Décrire un champ | | | | |
| Documenter les réponses d'erreur | | | | |
| Garder la doc synchronisée avec le code | | | | |

---

## 5 — Dépendances et configuration

*À remplir en session 26.*

| Concept | En Flask | En FastAPI | Pourquoi c'est différent | État |
|---|---|---|---|---|
| Fournir la session de base de données | | | | |
| Libérer une ressource en fin de requête | | | | |
| Accéder à la configuration | | | | |
| État partagé par requête | | | | |
| Remplacer une dépendance en test | | | | |
| Ressource partagée par l'application | | | | |
| Appliquer un traitement à toutes les routes | | | | |

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
| | | |
| | | |

---

## Réflexes Flask à désapprendre

> Les automatismes qui produisent du code faux ou inutile en FastAPI.
> Je remplis quand je me surprends à le faire.

| Le réflexe | Ce qu'il faut faire à la place |
|---|---|
| | |
| | |

---

## Ce que Flask fait mieux

> À remplir honnêtement. Si cette section reste vide à la fin du programme,
> c'est que je n'ai pas cherché.

| Sujet | Pourquoi Flask s'en sort mieux |
|---|---|
| | |

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
