from passlib.context import CryptContext

CRIPTO = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verification_password(password: str, hash_password: str) -> bool:
    """
    Verifies whether the plain-text password matches the stored hash.

    Parameters
    ----------
    password : str
        Plain-text password provided by the user.
    hash_password : str
        Hashed password stored in the database.

    Returns
    -------
    bool
    """

    return CRIPTO.verify(password, hash_password)


def generator_hash_password(password: str):
    """Generates and returns the bcrypt hash of the given password."""
    return CRIPTO.hash(password)
