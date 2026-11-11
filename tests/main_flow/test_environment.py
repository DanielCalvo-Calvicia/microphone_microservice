"""The service reads its own `.env` at start (T-03.1): the process environment wins, a missing file is fine."""

import os
from pathlib import Path

import pytest

from main_flow import http as main_http
from main_flow.http import load_environment


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("DOTENV_TEST_PORT", "DOTENV_TEST_OTHER", "SERVICE_PORT"):
        monkeypatch.delenv(name, raising=False)


def test_a_variable_from_the_file_is_visible(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("DOTENV_TEST_PORT=8123\nDOTENV_TEST_OTHER=dummy value\n", encoding="utf-8")
    try:
        load_environment(env_file)
        assert os.environ["DOTENV_TEST_PORT"] == "8123"
        assert os.environ["DOTENV_TEST_OTHER"] == "dummy value"
    finally:
        os.environ.pop("DOTENV_TEST_PORT", None)
        os.environ.pop("DOTENV_TEST_OTHER", None)


def test_a_variable_already_in_the_environment_is_not_overwritten(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("DOTENV_TEST_PORT=8123\n", encoding="utf-8")
    monkeypatch.setenv("DOTENV_TEST_PORT", "9000")
    load_environment(env_file)
    assert os.environ["DOTENV_TEST_PORT"] == "9000"


def test_a_missing_file_is_not_an_error(tmp_path: Path) -> None:
    before = dict(os.environ)
    load_environment(tmp_path / "does-not-exist.env")
    assert dict(os.environ) == before


def test_the_default_file_is_the_one_next_to_main_py() -> None:
    assert main_http._ENV_FILE == Path(main_http.__file__).resolve().parent.parent / ".env"
    assert main_http._ENV_FILE.name == ".env"


def test_the_file_is_read_before_the_settings_are(monkeypatch: pytest.MonkeyPatch) -> None:
    """`run_http` loads the file first, so SERVICE_PORT written only in the file is the port it uses."""
    import asyncio

    seen: dict[str, int] = {}

    def fake_load(path: Path = main_http._ENV_FILE) -> None:
        monkeypatch.setenv("SERVICE_PORT", "8123")

    class Stop(Exception):
        pass

    def fake_container(server_cfg, microphone_cfg):  # noqa: ANN001, ANN202
        seen["port"] = server_cfg.port
        raise Stop

    monkeypatch.setattr(main_http, "load_environment", fake_load)
    monkeypatch.setattr(main_http, "new_http_container", fake_container)
    with pytest.raises(Stop):
        asyncio.run(main_http.run_http())
    assert seen == {"port": 8123}
