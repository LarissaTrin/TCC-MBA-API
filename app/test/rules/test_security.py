"""Tests for app/core/security.py"""
from core.security import generator_hash_password, verification_password


def test_hash_is_not_plaintext():
    hashed = generator_hash_password("secret123")
    assert hashed != "secret123"
    assert len(hashed) > 20


def test_verification_correct_password():
    hashed = generator_hash_password("mypassword")
    assert verification_password("mypassword", hashed) is True


def test_verification_wrong_password():
    hashed = generator_hash_password("mypassword")
    assert verification_password("wrongpassword", hashed) is False


def test_different_hashes_same_password():
    h1 = generator_hash_password("abc")
    h2 = generator_hash_password("abc")
    # bcrypt uses random salt — hashes differ but both verify correctly
    assert h1 != h2
    assert verification_password("abc", h1) is True
    assert verification_password("abc", h2) is True
