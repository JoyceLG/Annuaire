# bdd.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from modeles import Base

engine = create_engine("sqlite:///astronautes.db", echo=True)
FabriqueSession = sessionmaker(bind=engine)


def creer_tables() -> None:
    Base.metadata.create_all(engine)