# bdd.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from modeles import Base

engine = create_engine("sqlite:///astronautes.db", echo=False)
FabriqueSession = sessionmaker(bind=engine)
