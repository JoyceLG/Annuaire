# session_web.py
from flask import g

import bdd


def session_bdd():
    if "bdd" not in g:
        g.bdd = bdd.FabriqueSession()
    return g.bdd


def fermer_session_bdd(exception=None):
    session = g.pop("bdd", None)
    if session is not None:
        session.close()
