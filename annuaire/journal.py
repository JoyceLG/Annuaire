"""Configuration du journal pour l'application Flask."""

from flask import g, has_request_context
import json
import logging
import re

# Séquences ANSI (couleurs, gras...) que werkzeug ajoute à son bandeau de démarrage.
# json.dumps les échapperait en "\\u001b[31m", illisible dans le terminal.
MOTIF_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def nettoyer_ansi(texte: str) -> str:
    return MOTIF_ANSI.sub("", texte)


class FormateurJson(logging.Formatter):
    def format(self, enregistrement: logging.LogRecord) -> str:
        donnees = {
            "horodatage": self.formatTime(enregistrement, "%Y-%m-%dT%H:%M:%S"),
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


def configurer_journal(app) -> None:
    """Configure le journal pour l'application Flask."""
    
    handler = logging.StreamHandler()
    handler.setFormatter(FormateurJson())
    handler.addFilter(FiltreRequeteId())

    racine = logging.getLogger()
    racine.handlers.clear()
    racine.addHandler(handler)
    racine.setLevel(app.config["NIVEAU_LOG"])
    
    # Réduit le niveau de journalisation de werkzeug pour éviter le bruit des requêtes HTTP.
    logging.getLogger("werkzeug").setLevel(logging.WARNING)