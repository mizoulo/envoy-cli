"""Tests for the Vault high-level interface."""

import pytest

from envoy.vault import Vault


SAMPLE_ENV = "DB_URL=postgres://localhost/db\nSECRET_KEY=abc123\n"
PROJECT = "my-app"
ENV_NAME = "production"
PASSWORD = "s3cur3p@ss"


@pytest.fixture()
def vault(tmp_path):
    return Vault(PASSWORD, store_dir=tmp_path)


def test_push_returns_path(vault, tmp_path):
    path = vault.push(PROJECT, ENV_NAME, SAMPLE_ENV)
    assert path.exists()
    assert path.suffix == ".enc"


def test_pull_round_trip(vault):
    vault.push(PROJECT, ENV_NAME, SAMPLE_ENV)
    result = vault.pull(PROJECT, ENV_NAME)
    assert result == SAMPLE_ENV


def test_list_envs(vault):
    vault.push(PROJECT, "staging", SAMPLE_ENV)
    vault.push(PROJECT, "production", SAMPLE_ENV)
    envs = vault.list_envs(PROJECT)
    assert set(envs) == {"staging", "production"}


def test_list_envs_empty_project(vault):
    """list_envs should return an empty list for a project with no environments."""
    envs = vault.list_envs("unknown-project")
    assert envs == []


def test_delete_removes_env(vault):
    vault.push(PROJECT, ENV_NAME, SAMPLE_ENV)
    vault.delete(PROJECT, ENV_NAME)
    assert ENV_NAME not in vault.list_envs(PROJECT)


def test_pull_missing_raises(vault):
    with pytest.raises(FileNotFoundError):
        vault.pull(PROJECT, "nonexistent")


def test_empty_password_raises(tmp_path):
    with pytest.raises(ValueError):
        Vault("", store_dir=tmp_path)


def test_push_empty_plaintext_raises(vault):
    with pytest.raises(ValueError):
        vault.push(PROJECT, ENV_NAME, "")


def test_rotate_password(vault):
    vault.push(PROJECT, ENV_NAME, SAMPLE_ENV)
    vault.rotate_password("n3wP@ss!", PROJECT, ENV_NAME)
    result = vault.pull(PROJECT, ENV_NAME)
    assert result == SAMPLE_ENV


def test_rotate_password_old_password_no_longer_works(vault):
    """After rotating, the old password should not decrypt the env."""
    vault.push(PROJECT, ENV_NAME, SAMPLE_ENV)
    vault.rotate_password("n3wP@ss!", PROJECT, ENV_NAME)
    old_vault = Vault(PASSWORD, store_dir=vault.store_dir)
    with pytest.raises(Exception):
        old_vault.pull(PROJECT, ENV_NAME)


def test_rotate_to_empty_password_raises(vault):
    vault.push(PROJECT, ENV_NAME, SAMPLE_ENV)
    with pytest.raises(ValueError):
        vault.rotate_password("", PROJECT, ENV_NAME)
