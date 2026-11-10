"""SQL Warehouse connection for the local Streamlit app."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[3]
NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, value = text.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def settings() -> dict[str, str]:
    """Read warehouse settings from .env. The token stays in this dict only."""
    env = load_env(ROOT / ".env")
    host = env.get("DATABRICKS_SERVER_HOSTNAME", "").strip()
    if not host:
        host = env.get("DATABRICKS_HOST", "")
    host = host.replace("https://", "").strip().strip("/")
    catalog = (env.get("UC_CATALOG") or "olist_catalog").strip()
    gold = (env.get("GOLD_SCHEMA") or "gold").strip()
    dss = (env.get("DSS_SCHEMA") or "dss").strip()
    for name, value in (("UC_CATALOG", catalog), ("GOLD_SCHEMA", gold), ("DSS_SCHEMA", dss)):
        if not NAME_RE.match(value):
            raise RuntimeError(f"Invalid {name}")
    return {
        "host": host,
        "http_path": env.get("DATABRICKS_HTTP_PATH", "").strip(),
        "token": env.get("DATABRICKS_TOKEN", "").strip(),
        "catalog": catalog,
        "gold": gold,
        "dss": dss,
    }


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
    from databricks import sql as dbsql

    missing = [name for name in ("host", "http_path", "token") if not cfg.get(name)]
    if missing:
        raise RuntimeError("Missing .env values: " + ", ".join(missing))
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

1. Điền `DATABRICKS_SERVER_HOSTNAME` (hoặc `DATABRICKS_HOST`), `DATABRICKS_HTTP_PATH` và `DATABRICKS_TOKEN` trong `.env`, bật warehouse, rồi bấm **Làm mới**.
2. Dừng tại đây và ghi PROGRESS_LOG. App không đọc CSV.
        """
    )


def refresh_button(page: str) -> None:
    if st.button("Làm mới", key=f"refresh_{page}", width="stretch"):
        st.cache_data.clear()
        st.rerun()
