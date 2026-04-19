"""
auth.py — SpeakAgain v2.1 authentication
-----------------------------------------
Two authentication pathways:
1. Google OAuth (via Streamlit 1.42+ native st.login())
2. Username + password (for users without Google accounts)

Family members do NOT create accounts. They use the invite code
emailed to them. This matches the requirement that "members retain
only the key sent to them via email".
"""

import hashlib
import json
import os
import secrets
import streamlit as st
from datetime import datetime
from typing import Optional

USER_STORE_PATH = os.environ.get(
    "SPEAKAGAIN_USER_STORE",
    os.path.join(os.path.dirname(__file__), ".users.json")
)

INVITE_STORE_PATH = os.environ.get(
    "SPEAKAGAIN_INVITE_STORE",
    os.path.join(os.path.dirname(__file__), ".invites.json")
)


def _load_users() -> dict:
    try:
        if os.path.exists(USER_STORE_PATH):
            with open(USER_STORE_PATH, "r") as f:
                return json.load(f)
    except (OSError, json.JSONDecodeError):
        pass
    return {}


def _save_users(users: dict) -> bool:
    """Best-effort save. If filesystem is read-only (some cloud hosts),
    fall back to session state so account survives current session."""
    try:
        os.makedirs(os.path.dirname(USER_STORE_PATH) or ".", exist_ok=True)
        with open(USER_STORE_PATH, "w") as f:
            json.dump(users, f, indent=2)
        return True
    except OSError:
        if "user_store_fallback" not in st.session_state:
            st.session_state.user_store_fallback = {}
        st.session_state.user_store_fallback = users
        return False


def _users_combined() -> dict:
    users = _load_users()
    fallback = st.session_state.get("user_store_fallback", {})
    users.update(fallback)
    return users


def _hash_password(password: str, salt: str) -> str:
    """PBKDF2-SHA256, 100k iterations. Swap to Argon2id in production."""
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    ).hex()


def signup(username: str, password: str, email: str = "") -> tuple[bool, str]:
    username = username.strip().lower()
    if not username or len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    if not username.replace("_", "").replace("-", "").isalnum():
        return False, "Username can only contain letters, numbers, _ and -."

    users = _users_combined()
    if username in users:
        return False, "That username is already taken."

    salt = secrets.token_hex(16)
    users[username] = {
        "auth_method": "password",
        "salt": salt,
        "password_hash": _hash_password(password, salt),
        "email": email.strip(),
        "created_at": datetime.utcnow().isoformat(),
        "profile": None,
    }
    _save_users(users)
    return True, f"Account created. Welcome, {username}!"


def login(username: str, password: str) -> tuple[bool, str, Optional[dict]]:
    username = username.strip().lower()
    users = _users_combined()
    user = users.get(username)

    if not user:
        return False, "No account with that username.", None
    if user.get("auth_method") != "password":
        return False, f"This account uses {user.get('auth_method')}.", None

    expected = _hash_password(password, user["salt"])
    if expected != user["password_hash"]:
        return False, "Wrong password.", None

    return True, f"Welcome back, {username}!", user


def login_with_google(google_email: str, google_name: str = "",
                      google_sub: str = "") -> tuple[bool, str, dict]:
    google_email = google_email.strip().lower()
    if not google_email or "@" not in google_email:
        return False, "Invalid Google email.", {}

    username = f"google:{google_email}"
    users = _users_combined()

    if username not in users:
        users[username] = {
            "auth_method": "google",
            "email": google_email,
            "display_name": google_name or google_email.split("@")[0],
            "google_sub": google_sub,
            "created_at": datetime.utcnow().isoformat(),
            "profile": None,
        }
        _save_users(users)
        msg = f"Welcome, {google_name or google_email}!"
    else:
        msg = f"Signed in as {google_name or google_email}"

    return True, msg, users[username]


def update_user_profile(username: str, profile: dict) -> bool:
    users = _users_combined()
    if username in users:
        users[username]["profile"] = profile
        _save_users(users)
        return True
    return False


def get_user_profile(username: str) -> Optional[dict]:
    users = _users_combined()
    user = users.get(username)
    return user.get("profile") if user else None


def set_logged_in(username: str, user_record: dict):
    st.session_state.auth_user = username
    st.session_state.auth_record = user_record
    st.session_state.is_authenticated = True


def logout():
    """Clear all session state — full logout."""
    keys_to_clear = list(st.session_state.keys())
    for k in keys_to_clear:
        del st.session_state[k]


def is_authenticated() -> bool:
    return st.session_state.get("is_authenticated", False)


def current_username() -> Optional[str]:
    return st.session_state.get("auth_user")


def current_user() -> Optional[dict]:
    return st.session_state.get("auth_record")


# ==========================================================
# FAMILY INVITE FLOW
# ==========================================================
def _load_invites() -> dict:
    try:
        if os.path.exists(INVITE_STORE_PATH):
            with open(INVITE_STORE_PATH, "r") as f:
                return json.load(f)
    except (OSError, json.JSONDecodeError):
        pass
    return st.session_state.get("invite_store_fallback", {})


def _save_invites(invites: dict) -> bool:
    try:
        os.makedirs(os.path.dirname(INVITE_STORE_PATH) or ".", exist_ok=True)
        with open(INVITE_STORE_PATH, "w") as f:
            json.dump(invites, f, indent=2)
        return True
    except OSError:
        st.session_state.invite_store_fallback = invites
        return False


def create_invite_code(patient_username: str, family_name: str,
                       family_email: str, relationship: str) -> str:
    """Generate an 8-char invite code bound to this patient + family member."""
    raw = secrets.token_urlsafe(8).upper()
    code = "".join(c for c in raw if c.isalnum())[:8]
    invites = _load_invites()
    invites[code] = {
        "patient_username": patient_username,
        "family_name": family_name,
        "family_email": family_email,
        "relationship": relationship,
        "created_at": datetime.utcnow().isoformat(),
        "used": False,
    }
    _save_invites(invites)
    return code


def validate_invite_code(code: str) -> Optional[dict]:
    code = code.strip().upper()
    invites = _load_invites()
    return invites.get(code)


def consume_invite_code(code: str):
    code = code.strip().upper()
    invites = _load_invites()
    if code in invites:
        invites[code]["used"] = True
        invites[code]["used_at"] = datetime.utcnow().isoformat()
        _save_invites(invites)


# ==========================================================
# GOOGLE OAUTH — STREAMLIT NATIVE INTEGRATION
# ==========================================================
def google_oauth_available() -> bool:
    """True if Streamlit's built-in auth is configured in secrets."""
    try:
        return hasattr(st, "user") and hasattr(st, "login")
    except Exception:
        return False


def trigger_google_login():
    """Kick off Streamlit's native Google OAuth flow."""
    if google_oauth_available():
        try:
            st.login("google")
            return True
        except Exception:
            return False
    return False


def handle_google_callback() -> Optional[dict]:
    """After st.login() returns, st.user holds OAuth claims."""
    if not google_oauth_available():
        return None
    try:
        if st.user.is_logged_in:
            return {
                "email": st.user.email,
                "name": getattr(st.user, "name", st.user.email),
                "sub": getattr(st.user, "sub", ""),
            }
    except Exception:
        return None
    return None
