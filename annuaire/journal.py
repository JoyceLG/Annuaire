"""Configuration du journal pour l'application Flask.

Tout est réglable par la configuration : le niveau, le format (JSON pour un
collecteur, texte pour un humain), la destination et le bavardage de werkzeug.
"""

import json
import logging
import re

from logging.handlers import RotatingFileHandler

from flask import g, has_request_context

# Séquences ANSI (couleurs, gras...) que werkzeug ajoute à son bandeau de démarrage.
# json.dumps les échapperait en "\\u001b[31m", illisible dans le terminal.
MOTIF_ANSI = re.compile(r"\x1b\[[0-9;]*m")

FORMAT_TEXTE = "%(asctime)s %(levelname)-8s [%(requete_id)s] %(name)s : %(message)s"


def nettoyer_ansi(texte: str) -> str:
    return MOTIF_ANSI.sub("", texte)


class FormateurJson(logging.Formatter):
    def __init__(self, format_horodatage: str):
        super().__init__(datefmt=format_horodatage)

    def format(self, enregistrement: logging.LogRecord) -> str:
        donnees = {
            "horodatage": self.formatTime(enregistrement, self.datefmt),
            "niveau": enregistrement.levelname,
            "logger": enregistrement.name,
            "message": nettoyer_ansi(enregistrement.getMessage()),
            "requete_id": getattr(enregistrement, "requete_id", "-"),
        }
        if enregistrement.exc_info:
            donnees["exception"] = self.formatException(enregistrement.exc_info)
        return json.dumps(donnees, ensure_ascii=False)


class FiltreRequeteId(logging.Filter):
    def filter(self, enregistrement: logging.LogRecord) -> bool:
        enregistrement.requete_id = getattr(g, "requete_id", "-") if has_request_context() else "-"
        return True


def construire_formateur(app) -> logging.Formatter:
    """Le formateur correspondant à `FORMAT_LOG`."""

    horodatage = app.config["FORMAT_HORODATAGE"]
    if app.config["FORMAT_LOG"] == "texte":
        return logging.Formatter(FORMAT_TEXTE, datefmt=horodatage)
    return FormateurJson(horodatage)


def construire_handler(app) -> logging.Handler:
    """Le flux de sortie, ou un fichier tournant si `FICHIER_LOG` est renseigné."""

    fichier = app.config["FICHIER_LOG"]
    if not fichier:
        return logging.StreamHandler()
    return RotatingFileHandler(
        fichier,
        maxBytes=app.config["TAILLE_MAX_LOG"],
        backupCount=app.config["NOMBRE_FICHIERS_LOG"],
        encoding="utf-8",
    )


def configurer_journal(app) -> None:
    """Configure le journal pour l'application Flask."""

    handler = construire_handler(app)
    handler.setFormatter(construire_formateur(app))
    handler.addFilter(FiltreRequeteId())

    racine = logging.getLogger()
    racine.handlers.clear()
    racine.addHandler(handler)
    racine.setLevel(app.config["NIVEAU_LOG"])

    # Werkzeug journalise une ligne par requête HTTP : du bruit en production,
    # mais précisément ce qu'on veut voir en développement. D'où un réglage à
    # part, et non `logging.WARNING` en dur.
    logging.getLogger("werkzeug").setLevel(app.config["NIVEAU_LOG_WERKZEUG"])
