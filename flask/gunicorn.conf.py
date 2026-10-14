"""Configuration Gunicorn. Lue au démarrage du maître, avant le fork."""

import multiprocessing
import os

# --- Réseau -----------------------------------------------------------------
# 0.0.0.0 : écoute sur toutes les interfaces DU CONTENEUR. C'est l'équivalent
# du --host 0.0.0.0 de `flask run` : sans lui, le serveur
# n'écouterait que la boucle locale du conteneur, injoignable depuis l'hôte.
# La restriction d'exposition se fait dans compose (127.0.0.1:5000:5000).
bind = "0.0.0.0:5000"

# --- Workers ----------------------------------------------------------------
# cpu_count() renvoie les cœurs de l'HÔTE, pas le quota du conteneur.
# La variable d'environnement permet de corriger sans reconstruire l'image.
workers = int(os.environ.get("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))

# sync : un worker traite une requête à la fois. Le plus simple et le plus
# prévisible ; aucune contrainte sur le code applicatif.
worker_class = "sync"

# --- Délais -----------------------------------------------------------------
# Un worker qui n'a pas répondu en 30 s est considéré bloqué et tué.
timeout = 30
# Délai laissé aux requêtes en cours lors d'un arrêt (SIGTERM).
graceful_timeout = 30
# Durée de maintien d'une connexion inactive.
keepalive = 5

# --- Recyclage --------------------------------------------------------------
# Redémarre un worker après N requêtes : pansement sur les fuites mémoire.
max_requests = 1000
# Aléa sur ce seuil, sinon tous les workers redémarrent en même temps.
max_requests_jitter = 100

# --- Journal ----------------------------------------------------------------
# Le journal d'accès de l'application est plus riche (identifiant de
# corrélation, utilisateur) : on désactive celui de Gunicorn pour ne pas
# avoir deux lignes par requête.
accesslog = None
# "-" = sortie standard, comme le journal de l'application : c'est elle que
# `docker compose logs` recueille.
errorlog = "-"
loglevel = "info"