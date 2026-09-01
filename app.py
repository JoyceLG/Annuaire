from flask import Flask
from gestionnaires import enregistrer_gestionnaires
from routes import bp

app = Flask(__name__)
enregistrer_gestionnaires(app)
app.register_blueprint(bp)