# bdd.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("sqlite:///astronautes.db", echo=True)
FabriqueSession = sessionmaker(bind=engine)
