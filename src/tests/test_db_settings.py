"""Warehouse connection settings. No live SQL connection and no real token."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

FRONT = Path(__file__).resolve().parents[1] / "frontend"
sys.path.insert(0, str(FRONT))

from lib import db  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
CONN_KEYS = (
    "DATABRICKS_HOST",
    "DATABRICKS_SERVER_HOSTNAME",
    "DATABRICKS_HTTP_PATH",
    "DATABRICKS_TOKEN",
    "UC_CATALOG",
    "GOLD_SCHEMA",
    "DSS_SCHEMA",
)
FAKE_TOKEN = "dapi-test-only"


def _env_text(host: str, token: str = FAKE_TOKEN) -> str:
    return (
        f'DATABRICKS_SERVER_HOSTNAME="{host}"\n'
        "DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/from-file\n"
        f"DATABRICKS_TOKEN={token}\n"
    )


@pytest.fixture
def isolated(monkeypatch, tmp_path):
    """Point the app at a temp root and hide the developer machine's secrets."""
    from streamlit import config as st_config

    previous = list(st_config.get_option("secrets.files"))
    missing = tmp_path / "missing-secrets.toml"
    st_config.set_option("secrets.files", [str(missing)])
    db.st.secrets._reset()
    monkeypatch.setattr(db, "ROOT", tmp_path)
    for key in CONN_KEYS:
        monkeypatch.delenv(key, raising=False)
    try:
        yield tmp_path
    finally:
        reset = getattr(db.st.secrets, "_reset", None)
        if reset is not None:
            reset()
        st_config.set_option("secrets.files", previous)


def test_load_dotenv_skips_missing_file(tmp_path):
    assert db.load_dotenv(tmp_path / ".env") == {}


def test_dotenv_file_only(isolated):
    (isolated / ".env").write_text(
        _env_text("https://file.example/"),
        encoding="utf-8",
    )
    cfg = db.settings()
    assert cfg["host"] == "file.example"
    assert cfg["http_path"] == "/sql/1.0/warehouses/from-file"
    assert cfg["token"] == FAKE_TOKEN
    assert cfg["catalog"] == "olist_catalog"


def test_secrets_toml_beats_env_file(isolated, monkeypatch):
    from streamlit import config as st_config

    secret_file = isolated / ".streamlit" / "secrets.toml"
    secret_file.parent.mkdir()
    secret_file.write_text(
        "\n".join(
            [
                'DATABRICKS_HOST = "https://secrets.example/"',
                'DATABRICKS_HTTP_PATH = "/sql/1.0/warehouses/from-secrets"',
                f'DATABRICKS_TOKEN = "{FAKE_TOKEN}"',
            ]
        ),
        encoding="utf-8",
    )
    (isolated / ".env").write_text(_env_text("https://file.example/"), encoding="utf-8")
    monkeypatch.setenv("DATABRICKS_SERVER_HOSTNAME", "https://env.example/")
    monkeypatch.setenv("DATABRICKS_HTTP_PATH", "/sql/from-env")
    monkeypatch.setenv("DATABRICKS_TOKEN", "dapi-from-env")
    st_config.set_option("secrets.files", [str(secret_file)])
    db.st.secrets._reset()

    cfg = db.settings()

    assert cfg["host"] == "secrets.example"
    assert cfg["http_path"] == "/sql/1.0/warehouses/from-secrets"
    assert cfg["token"] == FAKE_TOKEN
    assert "dapi-from-env" not in cfg["token"]


def test_environ_beats_dotenv_when_secrets_missing(isolated, monkeypatch):
    (isolated / ".env").write_text(_env_text("https://file.example/"), encoding="utf-8")
    monkeypatch.setenv("DATABRICKS_HOST", "https://env.example/")
    monkeypatch.setenv("DATABRICKS_HTTP_PATH", "/sql/from-env")
    monkeypatch.setenv("DATABRICKS_TOKEN", FAKE_TOKEN)
    cfg = db.settings()
    assert cfg["host"] == "env.example"
    assert cfg["http_path"] == "/sql/from-env"


def test_broken_secrets_do_not_crash(isolated, monkeypatch):
    class BrokenSecrets:
        def __iter__(self):
            raise OSError("no secrets.toml")

    (isolated / ".env").write_text(_env_text("https://file.example"), encoding="utf-8")
    monkeypatch.setattr(db.st, "secrets", BrokenSecrets())
    cfg = db.settings()
    assert cfg["host"] == "file.example"
    assert cfg["token"] == FAKE_TOKEN


def test_server_hostname_wins_inside_one_source(isolated, monkeypatch):
    monkeypatch.setenv("DATABRICKS_HOST", "https://host-alias.example/")
    monkeypatch.setenv("DATABRICKS_SERVER_HOSTNAME", "HTTPS://server.example///")
    monkeypatch.setenv("DATABRICKS_HTTP_PATH", "/sql/path")
    monkeypatch.setenv("DATABRICKS_TOKEN", FAKE_TOKEN)
    assert db.settings()["host"] == "server.example"


def test_missing_message_names_variables_and_hides_token(isolated, monkeypatch):
    monkeypatch.setenv("DATABRICKS_TOKEN", FAKE_TOKEN)
    with pytest.raises(RuntimeError) as raised:
        db._connect(db.settings())
    text = str(raised.value)
    assert text == (
        "Thiếu cấu hình kết nối: "
        "DATABRICKS_HOST hoặc DATABRICKS_SERVER_HOSTNAME, DATABRICKS_HTTP_PATH"
    )
    assert FAKE_TOKEN not in text
    assert ".env" not in text


def test_secrets_toml_is_gitignored():
    for relative in (".streamlit/secrets.toml", "src/frontend/.streamlit/secrets.toml"):
        result = subprocess.run(
            ["git", "check-ignore", "-q", "--", relative],
            cwd=REPO,
            check=False,
        )
        assert result.returncode == 0, relative
    tracked = subprocess.run(
        ["git", "check-ignore", "-q", "--", "src/frontend/.streamlit/config.toml"],
        cwd=REPO,
        check=False,
    )
    assert tracked.returncode != 0
