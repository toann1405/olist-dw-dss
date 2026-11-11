"""SQL Warehouse connection for the Streamlit app."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[3]
NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
# Within one source, the server-hostname name wins when both are set.
HOST_KEYS = ("DATABRICKS_SERVER_HOSTNAME", "DATABRICKS_HOST")
MISSING_LABELS = {
    "host": "DATABRICKS_HOST hoặc DATABRICKS_SERVER_HOSTNAME",
    "http_path": "DATABRICKS_HTTP_PATH",
    "token": "DATABRICKS_TOKEN",
}


def load_dotenv(path: Path) -> dict[str, str]:
    """Read KEY=VALUE lines. Returns {} when the file is absent.

    Called only for an existing `.env`. The file is optional. This parser
    does not write `os.environ`, so a variable already in the environment
    stays ahead of the file.
    """
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, value = text.split("=", 1)
        values[key.strip()] = _clean(value)
    return values


def _clean(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip().strip('"').strip("'").strip()


def normalize_host(value: str) -> str:
    """Drop a leading https:// or http:// and any trailing slashes."""
    text = value.strip()
    lowered = text.lower()
    for prefix in ("https://", "http://"):
        if lowered.startswith(prefix):
            text = text[len(prefix) :]
            break
    return text.strip().strip("/")


def _read_secrets() -> dict[str, str]:
    """Read top-level Streamlit secrets. Missing secrets.toml is not an error."""
    try:
        raw = dict(st.secrets)
    except Exception:
        return {}
    found: dict[str, str] = {}
    for key, value in raw.items():
        if isinstance(value, Mapping):
            continue
        text = _clean(value)
        if text:
            found[str(key)] = text
    return found


def _pick(names: tuple[str, ...], *sources: Mapping[str, str]) -> str:
    """First non-empty value. Source order is the priority order."""
    for source in sources:
        for name in names:
            text = _clean(source.get(name, ""))
            if text:
                return text
    return ""


def settings() -> dict[str, str]:
    """Resolve warehouse settings.

    Priority for each variable: ``st.secrets``, then ``os.environ``, then
    `.env` when that file exists. The token stays in this dict only.
    """
    env_path = ROOT / ".env"
    file_values = load_dotenv(env_path) if env_path.is_file() else {}
    sources = (_read_secrets(), os.environ, file_values)
    host = normalize_host(_pick(HOST_KEYS, *sources))
    http_path = _pick(("DATABRICKS_HTTP_PATH",), *sources)
    token = _pick(("DATABRICKS_TOKEN",), *sources)
    catalog = _pick(("UC_CATALOG",), *sources) or "olist_catalog"
    gold = _pick(("GOLD_SCHEMA",), *sources) or "gold"
    dss = _pick(("DSS_SCHEMA",), *sources) or "dss"
    for name, value in (("UC_CATALOG", catalog), ("GOLD_SCHEMA", gold), ("DSS_SCHEMA", dss)):
        if not NAME_RE.match(value):
            raise RuntimeError(f"Invalid {name}")
    return {
        "host": host,
        "http_path": http_path,
        "token": token,
        "catalog": catalog,
        "gold": gold,
        "dss": dss,
    }


def missing_connection(cfg: Mapping[str, str]) -> list[str]:
    """Names of connection variables that are still empty. Values are not included."""
    return [MISSING_LABELS[name] for name in ("host", "http_path", "token") if not _clean(cfg.get(name, ""))]


def marker() -> str:
    """Bind values with `?`.

    The installed connector reports a pyformat paramstyle, then rejects
    unnamed `%s` markers unless inline params are enabled. `?` is the
    form that connector accepts.
    """
    try:
        import databricks.sql  # noqa: F401
    except ImportError as exc:
        raise RuntimeError("Missing package databricks-sql-connector") from exc
    return "?"


def _connect(cfg: dict[str, str]):
    missing = missing_connection(cfg)
    if missing:
        raise RuntimeError("Thiếu cấu hình kết nối: " + ", ".join(missing))
    from databricks import sql as dbsql

    return dbsql.connect(
        server_hostname=cfg["host"],
        http_path=cfg["http_path"],
        access_token=cfg["token"],
    )


def _frame(cursor) -> pd.DataFrame:
    rows = cursor.fetchall()
    columns = [str(item[0]).lower() for item in cursor.description] if cursor.description else []
    return pd.DataFrame(rows, columns=columns)


def query_uncached(sql_text: str, params: tuple = ()) -> pd.DataFrame:
    """Run one read statement and skip the cache. Used before an insert."""
    cfg = settings()
    with _connect(cfg) as conn:
        with conn.cursor() as cursor:
            if params:
                cursor.execute(sql_text, params)
            else:
                cursor.execute(sql_text)
            return _frame(cursor)


@st.cache_data(ttl=60, show_spinner=False)
def query_recent(sql_text: str, params: tuple = ()) -> pd.DataFrame:
    """Short cache for the decision list. Clear this after a successful insert."""
    return query_uncached(sql_text, params)


@st.cache_data(ttl=600, show_spinner=False)
def query(sql_text: str, params: tuple = ()) -> pd.DataFrame:
    """Run one read statement. Results stay cached for 600 seconds."""
    return query_uncached(sql_text, params)


def _statement(sql_text: str) -> str:
    lines = []
    for line in sql_text.strip().splitlines():
        if line.strip().startswith("--"):
            continue
        lines.append(line)
    text = "\n".join(lines).strip()
    if text.endswith(";"):
        text = text[:-1].strip()
    return text


def execute(sql_text: str, params: tuple) -> None:
    """Insert one decision_log row. This function is not cached."""
    text = _statement(sql_text)
    lowered = text.lower()
    if ";" in lowered:
        raise ValueError("Only INSERT into decision_log is allowed.")
    if not lowered.startswith("insert into"):
        raise ValueError("Only INSERT into decision_log is allowed.")
    head = lowered.split("(", 1)[0].strip()
    if not head.endswith("decision_log"):
        raise ValueError("Only INSERT into decision_log is allowed.")
    cfg = settings()
    with _connect(cfg) as conn:
        with conn.cursor() as cursor:
            cursor.execute(text, params)
        conn.commit()


def redact(exc: Exception) -> str:
    text = str(exc)
    try:
        token = settings().get("token", "")
    except Exception:
        token = ""
    if token and token in text:
        text = text.replace(token, "[token]")
    return text


def show_warehouse_error(exc: Exception) -> None:
    st.error("Chưa nối được SQL Warehouse (S2).")
    st.write(redact(exc))
    st.markdown(
        """
Hai phương án:

1. Đặt `DATABRICKS_HOST` (hoặc `DATABRICKS_SERVER_HOSTNAME`), `DATABRICKS_HTTP_PATH` và `DATABRICKS_TOKEN` trong `st.secrets`, biến môi trường, hoặc file `.env` nếu có. Bật warehouse, rồi bấm **Làm mới**.
2. Dừng tại đây và ghi PROGRESS_LOG. App không đọc CSV.
        """
    )


def refresh_button(page: str) -> None:
    if st.button("Làm mới", key=f"refresh_{page}", width="stretch"):
        st.cache_data.clear()
        st.rerun()
