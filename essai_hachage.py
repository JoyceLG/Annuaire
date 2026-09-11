import time
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import hashlib

hacheur = PasswordHasher()

# Le sel rend chaque empreinte unique
print(hacheur.hash("secret"))
print(hacheur.hash("secret"))      # différente !

# SHA-256 : identique, donc vulnérable aux tables précalculées
print(hashlib.sha256(b"secret").hexdigest())
print(hashlib.sha256(b"secret").hexdigest())

# La différence de coût
debut = time.perf_counter()
for _ in range(1000):
    hashlib.sha256(b"secret").hexdigest()
print(f"1000 SHA-256 : {time.perf_counter() - debut:.4f} s")

debut = time.perf_counter()
hacheur.hash("secret")
print(f"1 Argon2     : {time.perf_counter() - debut:.4f} s")