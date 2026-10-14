"""Routes pour la santé de l'application"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/api/sante")
def sante():
    return {"statut": "ok"}
