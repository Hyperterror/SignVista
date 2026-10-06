"""
Password hashing helpers.

New hashes use bcrypt. Accounts created before the bcrypt switch carry
passlib `sha256_crypt` hashes ("$5$..."); those still verify and are
transparently upgraded to bcrypt on the next successful login.
"""

import logging

import bcrypt
from passlib.hash import sha256_crypt

logger = logging.getLogger(__name__)

# bcrypt only uses the first 72 bytes of a password and bcrypt>=5 rejects longer input
BCRYPT_MAX_BYTES = 72

# Used to spend comparable time when the user does not exist (prevents user enumeration by timing)
_DUMMY_HASH = bcrypt.hashpw(b"signvista-dummy-password", bcrypt.gensalt()).decode("utf-8")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    try:
        if hashed_password.startswith("$5$"):
            return sha256_crypt.verify(plain_password, hashed_password)
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except (ValueError, TypeError) as e:
        logger.warning(f"Password verification error ({type(e).__name__}): unsupported hash format")
        return False


def needs_rehash(hashed_password: str) -> bool:
    """True when the stored hash is not a bcrypt hash."""
    return not hashed_password.startswith(("$2a$", "$2b$", "$2y$"))


def burn_password_check(plain_password: str) -> None:
    """Run a throwaway bcrypt check so missing users take as long as wrong passwords."""
    try:
        bcrypt.checkpw(plain_password.encode("utf-8")[:BCRYPT_MAX_BYTES], _DUMMY_HASH.encode("utf-8"))
    except ValueError:
        pass
