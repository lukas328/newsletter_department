import os
import pytest

from src.utils.config_loader import get_env_variable, get_api_key


def test_get_env_variable_with_default(monkeypatch):
    monkeypatch.delenv("SOME_VAR", raising=False)
    assert get_env_variable("SOME_VAR", "default") == "default"


def test_get_env_variable_missing_and_none(monkeypatch):
    monkeypatch.delenv("SOME_VAR", raising=False)
    assert get_env_variable("SOME_VAR") is None


def test_get_api_key_raises(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(ValueError):
        get_api_key("SECRET_KEY")
