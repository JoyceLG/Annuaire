#!/bin/sh
# Exécuté par l'image Postgres au tout premier démarrage, quand le volume de
# données est vide (création, ou après `docker compose down -v`). Crée la base
# vidée par les tests : son nom doit se terminer par _tests (tests/conftest.py).
set -e
createdb -U "$POSTGRES_USER" annuaire_tests
