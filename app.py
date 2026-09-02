from flask import Flask
from session_web import fermer_session_bdd
from gestionnaires import enregistrer_gestionnaires
from routes import bp


app = Flask(__name__)
enregistrer_gestionnaires(app)
app.register_blueprint(bp)
app.teardown_appcontext(fermer_session_bdd)