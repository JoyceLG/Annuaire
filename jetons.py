from datetime import UTC, datetime, timedelta
import os
import jwt

from erreurs import JetonExpire, JetonInvalide

CLE_SECRETE = os.environ["CLE_SECRETE_JWT"]

DUREE = timedelta(minutes=30)


def creer_jeton(id_utilisateur: int) -> str:
    maintenant = datetime.now(UTC)
    return jwt.encode(
        {"sub": str(id_utilisateur), "iat": maintenant, "exp": maintenant + DUREE},
        CLE_SECRETE,
        algorithm="HS256",
    )


def lire_jeton(jeton: str) -> int:
    try:
        charge = jwt.decode(jeton, CLE_SECRETE, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise JetonExpire()
    except jwt.InvalidTokenError:
        raise JetonInvalide()
    return int(charge["sub"])