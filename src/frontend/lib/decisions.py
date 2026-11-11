"""Guards around one confirmed insert. No warehouse call lives here."""

from __future__ import annotations


def claim_decision(state: dict, token: str) -> bool:
    """Allow one insert for this token until the caller releases the lock.

    A second call with the same token does not insert again, including after
    the in-flight flag is cleared. A different token can proceed.
    """
    if state.get("decision_inflight"):
        return False
    if state.get("last_decision_token") == token:
        return False
    state["decision_inflight"] = True
    state["last_decision_token"] = token
    return True


def release_decision(state: dict) -> None:
    state["decision_inflight"] = False
