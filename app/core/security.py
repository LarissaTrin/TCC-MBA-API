from passlib.context import CryptContext

CRIPTO = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verification_password(password: str, hash_password: str) -> bool:
    """
    Função para verificar se a senha está correta

    Parameters
    ----------
    password : str
        senha texto puro, informada pelo user
    hash_password : str
        senha no banco de dados durante a criação da conta

    Returns
    -------
    bool
    """

    return CRIPTO.verify(password, hash_password)


def generator_hash_password(password: str):
    """Função que gera e retorna o hash da senha"""
    return CRIPTO.hash(password)
