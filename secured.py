import argon2

def hashPassword(password: str) -> str:
    ph = argon2.PasswordHasher()
    return ph.hash(
        password
    )

def verify(hash_: str, password: str) -> bool:
    ph = argon2.PasswordHasher()
    return ph.verify(
        hash_,
        password
    )