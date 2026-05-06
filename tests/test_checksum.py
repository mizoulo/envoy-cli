"""Tests for envoy.checksum."""

import json
import pytest
from pathlib import Path

from envoy.checksum import ChecksumStore, ChecksumResult, _compute


@pytest.fixture
def store(tmp_path: Path) -> ChecksumStore:
    return ChecksumStore(tmp_path / "checksums.json")


def test_store_file_created_on_record(store: ChecksumStore, tmp_path: Path):
    store.record("myproject/prod", b"KEY=value")
    assert (tmp_path / "checksums.json").exists()


def test_record_returns_hex_digest(store: ChecksumStore):
    digest = store.record("myproject/prod", b"KEY=value")
    assert len(digest) == 64
    assert all(c in "0123456789abcdef" for c in digest)


def test_verify_returns_matched_true(store: ChecksumStore):
    data = b"API_KEY=secret\nDEBUG=true"
    store.record("proj/dev", data)
    result = store.verify("proj/dev", data)
    assert isinstance(result, ChecksumResult)
    assert result.matched is True
    assert result.expected == result.actual


def test_verify_detects_tampered_data(store: ChecksumStore):
    store.record("proj/dev", b"API_KEY=secret")
    result = store.verify("proj/dev", b"API_KEY=tampered")
    assert result.matched is False
    assert result.expected != result.actual


def test_verify_unknown_key_returns_not_matched(store: ChecksumStore):
    result = store.verify("nonexistent/key", b"some data")
    assert result.matched is False
    assert result.expected is None
    assert result.actual is not None


def test_remove_existing_key(store: ChecksumStore):
    store.record("proj/staging", b"X=1")
    removed = store.remove("proj/staging")
    assert removed is True
    result = store.verify("proj/staging", b"X=1")
    assert result.matched is False


def test_remove_nonexistent_key_returns_false(store: ChecksumStore):
    assert store.remove("ghost/key") is False


def test_all_keys_lists_recorded(store: ChecksumStore):
    store.record("a/b", b"1")
    store.record("c/d", b"2")
    keys = store.all_keys()
    assert set(keys) == {"a/b", "c/d"}


def test_checksums_persisted_across_instances(tmp_path: Path):
    path = tmp_path / "checksums.json"
    data = b"PERSIST=yes"
    s1 = ChecksumStore(path)
    s1.record("proj/prod", data)

    s2 = ChecksumStore(path)
    result = s2.verify("proj/prod", data)
    assert result.matched is True


def test_compute_is_deterministic():
    d1 = _compute(b"hello")
    d2 = _compute(b"hello")
    assert d1 == d2


def test_compute_differs_for_different_inputs():
    assert _compute(b"hello") != _compute(b"world")
