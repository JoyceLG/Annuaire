"""Documentation interactive servie derrière une authentification.

Un navigateur qui ouvre `/docs` ne peut pas joindre d'en-tête Authorization,
et Swagger UI charge ensuite `/openapi.json` par une requête séparée, sans
en-tête non plus. Seuls les cookies du site partent d'eux-mêmes : la
connexion pose donc un cookie, que `documentation_autorisee` accepte.
"""

from html import escape
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import HTMLResponse, RedirectResponse

from annuaire.dependances import (
    NOM_COOKIE_DOCUMENTATION,
    documentation_autorisee,
    documentation_requise,
    jeton_valide,
)

router = APIRouter(include_in_schema=False)

DocumentationAutorisee = Annotated[bool, Depends(documentation_autorisee)]

# Les seules pages vers lesquelles la connexion redirige : une adresse libre
# dans `suite` permettrait d'envoyer l'utilisateur sur un site tiers.
PAGES_DOCUMENTATION = ("/docs", "/redoc")


def page_de_connexion(suite: str, erreur: bool = False) -> HTMLResponse:
    """Formulaire de connexion, renvoyé avec un 401 à qui n'est pas connecté."""
    message = "<p>Jeton refusé.</p>" if erreur else ""
    return HTMLResponse(
        status_code=401,
        content=f"""<!doctype html>
<html lang="fr">
<head><meta charset="utf-8"><title>Documentation — connexion</title></head>
<body>
  <h1>Documentation de l'annuaire</h1>
  {message}
  <form method="post" action="/docs/connexion">
    <label>Jeton <input type="password" name="jeton" required></label>
    <input type="hidden" name="suite" value="{escape(suite)}">
    <button type="submit">Se connecter</button>
  </form>
</body>
</html>""",
    )


@router.get("/openapi.json", dependencies=[Depends(documentation_requise)])
def schema(request: Request):
    """Le schéma OpenAPI, que Swagger UI et ReDoc chargent depuis le navigateur."""
    return request.app.openapi()


@router.get("/docs")
def swagger(request: Request, autorisee: DocumentationAutorisee):
    """Swagger UI, ou le formulaire de connexion."""
    if not autorisee:
        return page_de_connexion("/docs")
    return get_swagger_ui_html(
        openapi_url="/openapi.json", title=f"{request.app.title} — Swagger UI"
    )


@router.get("/redoc")
def redoc(request: Request, autorisee: DocumentationAutorisee):
    """ReDoc, ou le formulaire de connexion."""
    if not autorisee:
        return page_de_connexion("/redoc")
    return get_redoc_html(openapi_url="/openapi.json", title=f"{request.app.title} — ReDoc")


@router.post("/docs/connexion")
def connexion(
    jeton: Annotated[str, Form()],
    suite: Annotated[str, Form()] = "/docs",
):
    """Pose le cookie de la documentation, puis renvoie vers la page demandée."""
    if suite not in PAGES_DOCUMENTATION:
        suite = "/docs"
    if not jeton_valide(jeton):
        return page_de_connexion(suite, erreur=True)

    # 303 : le navigateur suit la redirection par un GET, pas un nouveau POST.
    reponse = RedirectResponse(suite, status_code=303)
    reponse.set_cookie(
        NOM_COOKIE_DOCUMENTATION,
        jeton,
        # Invisible du JavaScript de la page : une faille XSS ne le lit pas.
        httponly=True,
        # Jamais envoyé en clair. Chrome et Firefox l'acceptent quand même sur
        # http://localhost et http://127.0.0.1, ce qui permet d'essayer en local.
        secure=True,
        # Joint aux seules navigations venues d'un autre site (lien suivi),
        # jamais à ses requêtes en arrière-plan ni à ses formulaires POST.
        # "strict" le retiendrait aussi sur un lien : arrivé depuis un ticket
        # ou un wiki, on retrouverait le formulaire alors qu'on est connecté.
        # Le cookie ne donne qu'à lire la documentation, et une page tierce
        # qui y envoie le navigateur ne peut pas lire la réponse.
        samesite="lax",
    )
    return reponse
