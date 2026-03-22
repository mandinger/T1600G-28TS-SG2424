from webapp.security import decrypt_secret, encrypt_secret, hash_password, role_allows, verify_password


def test_encrypt_decrypt_roundtrip() -> None:
    secret = "SwitchPassword123!"
    encrypted = encrypt_secret(secret)
    assert encrypted != secret
    assert decrypt_secret(encrypted) == secret


def test_password_hashing_and_verification() -> None:
    pw = "very-strong-password"
    digest = hash_password(pw)
    assert verify_password(pw, digest)
    assert not verify_password("wrong", digest)


def test_rbac_role_hierarchy() -> None:
    assert role_allows("admin", "operator")
    assert role_allows("operator", "viewer")
    assert not role_allows("viewer", "operator")
