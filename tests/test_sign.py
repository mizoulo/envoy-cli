"""Tests for envoy.sign."""
import pytest
from pathlib import Path
from envoy.sign import SignatureStore, SignResult, _compute_hmac


@pytest.fixture
def store(tmp_path: Path) -> SignatureStore:
    return SignatureStore(tmp_path / "signatures.json")


def test_sign_result_success():
    r = SignResult(action="sign", key="k", ok=True)
    assert r.success() is True


def test_sign_result_failure():
    r = SignResult(action="verify", key="k", ok=False, error="mismatch")
    assert r.success() is False


def test_sign_result_repr_contains_action_and_key():
    r = SignResult(action="sign", key="mykey", ok=True)
    assert "sign" in repr(r)
    assert "mykey" in repr(r)


def test_compute_hmac_returns_hex_string():
    digest = _compute_hmac(b"hello", "secret")
    assert isinstance(digest, str)
    assert len(digest) == 64  # sha256 hex


def test_compute_hmac_deterministic():
    d1 = _compute_hmac(b"data", "secret")
    d2 = _compute_hmac(b"data", "secret")
    assert d1 == d2


def test_compute_hmac_differs_on_different_secret():
    d1 = _compute_hmac(b"data", "secret1")
    d2 = _compute_hmac(b"data", "secret2")
    assert d1 != d2


def test_store_file_created_on_sign(store: SignatureStore, tmp_path: Path):
    store.sign("proj/dev", b"KEY=val", "s3cr3t")
    assert (tmp_path / "signatures.json").exists()


def test_sign_and_verify_success(store: SignatureStore):
    store.sign("proj/dev", b"KEY=val", "s3cr3t")
    result = store.verify("proj/dev", b"KEY=val", "s3cr3t")
    assert result.success()


def test_verify_detects_tampered_data(store: SignatureStore):
    store.sign("proj/dev", b"KEY=val", "s3cr3t")
    result = store.verify("proj/dev", b"KEY=tampered", "s3cr3t")
    assert not result.success()
    assert "mismatch" in result.error


def test_verify_missing_key_returns_error(store: SignatureStore):
    result = store.verify("missing/key", b"data", "secret")
    assert not result.success()
    assert "no signature" in result.error


def test_remove_existing_key(store: SignatureStore):
    store.sign("proj/dev", b"KEY=val", "s3cr3t")
    result = store.remove("proj/dev")
    assert result.success()
    assert "proj/dev" not in store.list_keys()


def test_remove_missing_key_returns_error(store: SignatureStore):
    result = store.remove("nonexistent")
    assert not result.success()


def test_list_keys_returns_all_signed(store: SignatureStore):
    store.sign("a/dev", b"A=1", "secret")
    store.sign("b/prod", b"B=2", "secret")
    keys = store.list_keys()
    assert "a/dev" in keys
    assert "b/prod" in keys


def test_store_persists_across_instances(tmp_path: Path):
    p = tmp_path / "sigs.json"
    s1 = SignatureStore(p)
    s1.sign("proj/dev", b"KEY=val", "secret")
    s2 = SignatureStore(p)
    assert "proj/dev" in s2.list_keys()
