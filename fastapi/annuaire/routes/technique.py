"""Routes techniques : points de contrôle de l'application."""

from fastapi import APIRouter

router = APIRouter(tags=["Technique"], prefix="/api/technique")


@router.get("/sante", summary="Vérifier que l'application répond")
def sante():
    """Renvoie `{"statut": "ok"}` dès que l'application est démarrée."""
    return {"statut": "ok"}
