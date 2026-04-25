"""
patient_store.py — shared persistent store for patient state

Each patient's state is stored on disk keyed by their username, so:
- The family dashboard (a separate browser session) can read real-time updates
- A returning patient can pick up exactly where they left off
- Profile, assessment, activity feed, and progress all survive login/logout

Security design:
- All paths are validated to prevent directory traversal
- Writes are atomic (write to temp + rename) to avoid partial reads
- Only critical events are pushed to email; full activity stays on disk
- No user-visible information is leaked about the storage mechanism
"""
import json
import os
import re
import tempfile
from datetime import datetime
from typing import Optional
import streamlit as st

# Store location — in-container volume when available, session fallback otherwise
_DEFAULT_STORE_DIR = os.environ.get(
    "SPEAKAGAIN_DATA_DIR",
    os.path.join(os.path.dirname(__file__), ".patient_data")
)

# Only letters, digits, underscore, hyphen, colon (for google: prefix)
_SAFE_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_:\-@.]{1,128}$")


def _ensure_store_dir() -> Optional[str]:
    """Try to create the store dir. Return path if usable, None otherwise."""
    try:
        os.makedirs(_DEFAULT_STORE_DIR, exist_ok=True)
        # Confirm writability
        testf = os.path.join(_DEFAULT_STORE_DIR, ".writetest")
        with open(testf, "w") as f:
            f.write("ok")
        os.remove(testf)
        return _DEFAULT_STORE_DIR
    except OSError:
        return None


def _safe_path(username: str) -> Optional[str]:
    """Return a safe path for a username, or None if username is invalid."""
    if not username or not _SAFE_USERNAME_RE.match(username):
        return None
    store_dir = _ensure_store_dir()
    if not store_dir:
        return None
    # Replace filesystem-unsafe chars
    safe_name = username.replace(":", "__").replace("@", "_at_").replace("/", "_")
    return os.path.join(store_dir, f"{safe_name}.json")


def _atomic_write_json(path: str, data: dict) -> bool:
    """Write JSON atomically: write to temp, rename over target."""
    try:
        dir_ = os.path.dirname(path)
        with tempfile.NamedTemporaryFile(
            mode="w", dir=dir_, prefix=".tmp_", suffix=".json",
            delete=False, encoding="utf-8"
        ) as tmp:
            json.dump(data, tmp, indent=2, default=str)
            tmp_path = tmp.name
        os.replace(tmp_path, path)  # atomic on POSIX
        return True
    except OSError:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
        return False


def _load_store(username: str) -> dict:
    """Load patient state from disk. Return empty-structure default if missing."""
    path = _safe_path(username)
    default = {
        "profile": None,
        "assessment_complete": False,
        "aphasia_type": None,
        "severity": None,
        "severity_history": [],
        "activity_feed": [],
        "communicated_today": [],
        "exercise_log": [],
        "emotion_log": [],
        "recovered_words": [],
        "streak_days": 0,
        "last_session_date": None,
        "xp": 0,
        "family_members": [],
        "updated_at": None,
    }
    if not path or not os.path.exists(path):
        # Try session fallback
        return dict(st.session_state.get(f"_pstore_{username}", default))
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Merge with default to handle added fields in new versions
            for k, v in default.items():
                if k not in data:
                    data[k] = v
            return data
    except (OSError, json.JSONDecodeError):
        return default


def _save_store(username: str, data: dict) -> bool:
    """Save patient state. Fall back to session-state when filesystem is read-only."""
    data["updated_at"] = datetime.utcnow().isoformat()
    path = _safe_path(username)
    if path and _atomic_write_json(path, data):
        return True
    # Session fallback
    st.session_state[f"_pstore_{username}"] = data
    return False


def save_profile(username: str, profile: dict) -> bool:
    """Persist profile + assessment state for a user."""
    data = _load_store(username)
    data["profile"] = profile
    return _save_store(username, data)


def save_assessment(username: str, aphasia_type: str, severity: float) -> bool:
    """Persist assessment result."""
    data = _load_store(username)
    data["assessment_complete"] = True
    data["aphasia_type"] = aphasia_type
    data["severity"] = severity
    data.setdefault("severity_history", []).append(
        (datetime.utcnow().isoformat(), severity)
    )
    return _save_store(username, data)


def save_progress(username: str, updates: dict) -> bool:
    """
    Merge caller-provided updates into the patient record.
    `updates` is a dict of keys to overwrite (e.g. xp, streak_days, recovered_words).
    """
    data = _load_store(username)
    for k, v in updates.items():
        data[k] = v
    return _save_store(username, data)


def append_activity(
    username: str,
    action: str,
    is_concern: bool = False,
    is_milestone: bool = False,
    max_items: int = 200,
) -> bool:
    """
    Append an item to the activity feed. Feed is capped at `max_items` and
    deduplicated against the immediately preceding item (so repeated taps of
    the same phrase don't spam the feed).
    """
    data = _load_store(username)
    feed = data.get("activity_feed") or []

    entry = {
        "time": datetime.utcnow().isoformat(),
        "action": action,
        "concern": bool(is_concern),
        "milestone": bool(is_milestone),
    }
    # Dedupe: skip if identical action within 5 seconds of the last one
    if feed:
        last = feed[0]
        try:
            last_time = datetime.fromisoformat(last["time"])
            delta = (datetime.utcnow() - last_time).total_seconds()
            if last.get("action") == action and delta < 5:
                return True
        except (ValueError, KeyError):
            pass

    feed.insert(0, entry)
    data["activity_feed"] = feed[:max_items]
    return _save_store(username, data)


def load_patient_state(username: str) -> dict:
    """Read a patient's state for display. Public read API."""
    return _load_store(username)


def get_activity_feed(username: str, limit: int = 50) -> list:
    """Return recent activity feed entries."""
    data = _load_store(username)
    return (data.get("activity_feed") or [])[:limit]


def clear_patient(username: str) -> bool:
    """Delete a patient's stored record (used by logout-and-reset if needed)."""
    path = _safe_path(username)
    if path and os.path.exists(path):
        try:
            os.remove(path)
            return True
        except OSError:
            pass
    st.session_state.pop(f"_pstore_{username}", None)
    return False
