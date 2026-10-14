from fastapi import FastAPI

from annuaire.gestionnaires import enregistrer_gestionnaires
from annuaire.routes import astronautes, missions, sante

app = FastAPI(title="Annuaire des astronautes", version="0.1.0")

app.include_router(astronautes.router)
app.include_router(sante.router)
app.include_router(missions.router)
enregistrer_gestionnaires(app)
