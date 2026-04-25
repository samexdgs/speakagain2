"""
auth.py — SpeakAgain v2.2 authentication
-----------------------------------------
Patient authentication via Streamlit-native Google OIDC (preferred) or
username + password (fallback). Family members do NOT create accounts;
they receive a one-shot invite code by email and paste it into the app.

Security:
- PBKDF2-HMAC-SHA256, 200k iterations, per-user 16-byte salt
- constant-time hash comparison
- invite codes are 64-bit random tokens (secrets.token_urlsafe)
- profile auto-restored on login (no forced reassessment on re-login)
- all credentials kept server-side in .users.json; never surfaced to UI
"""
import hashlib
import json
import os
import re
import secrets as stdlib_secrets
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional

# ==========================================================
# CONSTANTS
# ==========================================================
USER_STORE_PATH = os.environ.get(
    "SPEAKAGAIN_USER_STORE",
    os.path.join(os.path.dirname(__file__), ".users.json")
)

INVITE_STORE_PATH = os.environ.get(
    "SPEAKAGAIN_INVITE_STORE",
    os.path.join(os.path.dirname(__file__), ".invites.json")
)

PBKDF2_ITERATIONS = 200_000
SALT_BYTES = 16
INVITE_TTL_HOURS = 24  # codes expire after 24 hours if unused

# Username safety pattern — letters, digits, _, -, :, @, .
_SAFE_USER_RE = re.compile(r"^[a-zA-Z0-9_:\-@.]{3,128}$")


# ==========================================================
# FILE IO HELPERS
# ==========================================================
def _load_json(path: str) -> dict:
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except (OSError, json.JSONDecodeError):
        pass
    return {}


def _save_json(path: str, data: dict) -> bool:
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        # Write via temp file for atomicity
        tmp = f"{path}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        os.replace(tmp, path)
        return True
    except OSError:
        # Fall back to session state
        fallback_key = f"_fs_fallback_{os.path.basename(path)}"
        st.session_state[fallback_key] = data
        return False


def _load_users() -> dict:
    users = _load_json(USER_STORE_PATH)
    # Merge session fallback
    fallback = st.session_state.get(
        f"_fs_fallback_{os.path.basename(USER_STORE_PATH)}", {}
    )
    users.update(fallback)
    return users


def _save_users(users: dict) -> bool:
    return _save_json(USER_STORE_PATH, users)


def _load_invites() -> dict:
    invites = _load_json(INVITE_STORE_PATH)
    fallback = st.session_state.get(
        f"_fs_fallback_{os.path.basename(INVITE_STORE_PATH)}", {}
    )
    invites.update(fallback)
    return invites


def _save_invites(invites: dict) -> bool:
    return _save_json(INVITE_STORE_PATH, invites)


# ==========================================================
# PASSWORD HASHING
# ==========================================================
def _hash_password(password: str, salt: str) -> str:
    """PBKDF2-HMAC-SHA256, salt is hex string."""
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    ).hex()


# ==========================================================
# SIGNUP / LOGIN (USERNAME + PASSWORD)
# ==========================================================
def signup(username: str, password: str, email: str = "") -> tuple[bool, str]:
    """Create a new account. Returns (ok, message)."""
    username = (username or "").strip().lower()
    email_norm = (email or "").strip().lower()

    if not _SAFE_USER_RE.match(username):
        return False, "Username must be 3-128 characters: letters, digits, _, -, ., @."
    if len(password) < 8:
        return False, "Password must be at least 8 characters."

    users = _load_users()
    if username in users:
        return False, "An account with that username already exists."

    # Account linking: if this email is already tied to any account, refuse
    # to create a duplicate. The user should sign in with their existing
    # method (password or Google) instead.
    if email_norm:
        for existing_username, record in users.items():
            if (record.get("email") or "").lower() == email_norm:
                method = record.get("auth_method", "password")
                if method == "google":
                    return False, (
                        "An account with this email already exists via Google. "
                        "Please use 'Sign in with Google' instead."
                    )
                return False, (
                    "An account with this email already exists. "
                    "Please sign in with your existing username and password."
                )

    salt = stdlib_secrets.token_hex(SALT_BYTES)
    users[username] = {
        "auth_method": "password",
        "salt": salt,
        "password_hash": _hash_password(password, salt),
        "email": email_norm,
        "created_at": datetime.utcnow().isoformat(),
    }
    _save_users(users)
    return True, "Account created."


def login(username: str, password: str) -> tuple[bool, str, Optional[dict]]:
    """Validate credentials. Returns (ok, message, user_record)."""
    username = (username or "").strip().lower()
    users = _load_users()
    user = users.get(username)

    if not user:
        return False, "Incorrect username or password.", None
    if user.get("auth_method") != "password":
        return False, "This account uses a different sign-in method.", None

    expected = _hash_password(password, user["salt"])
    actual = user["password_hash"]

    # constant-time comparison
    if not stdlib_secrets.compare_digest(expected, actual):
        return False, "Incorrect username or password.", None

    return True, "Welcome back.", user


# ==========================================================
# GOOGLE OIDC VIA STREAMLIT-NATIVE st.login()
# ==========================================================
def google_oauth_configured() -> bool:
    """True only if Streamlit native auth is configured with a Google client."""
    try:
        # Streamlit requires [auth] block with redirect_uri + client_id
        if "auth" not in st.secrets:
            return False
        auth_section = st.secrets["auth"]
        # Must have client_id either directly or under [auth.google]
        has_flat = "client_id" in auth_section and "client_secret" in auth_section
        has_named = (
            hasattr(auth_section, "get")
            and isinstance(auth_section.get("google", None), dict)
            and "client_id" in auth_section["google"]
        )
        has_redirect = "redirect_uri" in auth_section
        return (has_flat or has_named) and has_redirect
    except Exception:
        return False


def google_current_user() -> Optional[dict]:
    """If a Streamlit Google session is active, return the user claims."""
    try:
        if hasattr(st, "user") and getattr(st.user, "is_logged_in", False):
            return {
                "email": getattr(st.user, "email", ""),
                "name": getattr(st.user, "name", ""),
                "sub": getattr(st.user, "sub", ""),
                "picture": getattr(st.user, "picture", ""),
            }
    except Exception:
        pass
    return None


def register_or_fetch_google_user(claims: dict) -> tuple[str, dict]:
    """Given verified Google claims, return (username, user_record).

    Account linking by email: if a password account or a Google account
    already exists with this email, return that one. Otherwise create a new
    Google account keyed by email (no "google:" prefix), so the same email
    always maps to the same account regardless of which method was used to
    sign in last.

    Legacy migration: earlier versions stored Google accounts under the
    composite key "google:<email>". If such an orphan exists alongside a
    canonical account for the same email, this function merges any patient
    data from the orphan into the canonical account and deletes the orphan
    on the spot.
    """
    email = (claims.get("email") or "").strip().lower()
    if not email or "@" not in email:
        raise ValueError("Invalid Google email in claims.")

    users = _load_users()
    legacy_username = f"google:{email}"

    # Find an existing canonical account for this email (if any), other than
    # the legacy "google:..." key
    canonical_username = None
    canonical_record = None
    for existing_username, record in users.items():
        if existing_username == legacy_username:
            continue
        if (record.get("email") or "").lower() == email:
            canonical_username = existing_username
            canonical_record = record
            break

    # Case A: a legacy orphan exists. Migrate its patient data and delete it.
    if legacy_username in users:
        if canonical_username:
            # Merge patient data from legacy → canonical, then delete the orphan
            try:
                _merge_patient_data(legacy_username, canonical_username)
            except Exception:
                pass
            del users[legacy_username]
            # Stamp the canonical account with the google_sub if we have one
            if canonical_record is not None and not canonical_record.get("google_sub"):
                canonical_record["google_sub"] = claims.get("sub", "")
                users[canonical_username] = canonical_record
            _save_users(users)
            return canonical_username, canonical_record
        else:
            # Promote the legacy account to the canonical key (its email)
            legacy_record = users.pop(legacy_username)
            legacy_record["google_sub"] = (
                legacy_record.get("google_sub") or claims.get("sub", "")
            )
            users[email] = legacy_record
            _save_users(users)
            try:
                _merge_patient_data(legacy_username, email)
            except Exception:
                pass
            return email, users[email]

    # Case B: no legacy orphan. If a canonical account already exists, use it.
    if canonical_username:
        if not canonical_record.get("google_sub"):
            canonical_record["google_sub"] = claims.get("sub", "")
            users[canonical_username] = canonical_record
            _save_users(users)
        return canonical_username, canonical_record

    # Case C: no account at all → create a fresh Google account keyed by email
    users[email] = {
        "auth_method": "google",
        "email": email,
        "display_name": claims.get("name", "") or email.split("@")[0],
        "google_sub": claims.get("sub", ""),
        "created_at": datetime.utcnow().isoformat(),
    }
    _save_users(users)
    return email, users[email]


def _merge_patient_data(source_username: str, target_username: str):
    """Move any patient_store data from source → target.

    If the target has no profile yet, the source's profile, assessment, XP,
    streak, and family list are copied over. Otherwise activity feeds are
    concatenated and the source's data is preserved only where the target
    is empty. The source patient file is then deleted.
    """
    # Local imports to avoid a circular dependency at module load time
    from patient_store import (
        load_patient_state, _save_store, clear_patient,
    )
    src = load_patient_state(source_username)
    tgt = load_patient_state(target_username)

    if not src.get("profile") and not src.get("activity_feed"):
        # Nothing to migrate
        clear_patient(source_username)
        return

    # Profile / assessment: target wins if it has data, otherwise take source
    for key in ("profile", "aphasia_type", "severity", "assessment_complete"):
        if not tgt.get(key) and src.get(key):
            tgt[key] = src[key]

    # Numeric / list fields: take the larger / merged version
    if src.get("xp", 0) > tgt.get("xp", 0):
        tgt["xp"] = src["xp"]
    if src.get("streak_days", 0) > tgt.get("streak_days", 0):
        tgt["streak_days"] = src["streak_days"]

    # Activity feed: prepend source items to target (they're typically older)
    src_feed = src.get("activity_feed") or []
    tgt_feed = tgt.get("activity_feed") or []
    tgt["activity_feed"] = (tgt_feed + src_feed)[:200]

    # Severity history: concat
    src_hist = src.get("severity_history") or []
    tgt_hist = tgt.get("severity_history") or []
    tgt["severity_history"] = tgt_hist + src_hist

    # Recovered words: union
    src_words = set(src.get("recovered_words") or [])
    tgt_words = set(tgt.get("recovered_words") or [])
    tgt["recovered_words"] = sorted(tgt_words | src_words)

    # Exercise log: concat
    src_log = src.get("exercise_log") or []
    tgt_log = tgt.get("exercise_log") or []
    tgt["exercise_log"] = (tgt_log + src_log)[-500:]

    # Family members: target wins if present (avoid duplicates), otherwise take source
    if not tgt.get("family_members") and src.get("family_members"):
        tgt["family_members"] = src["family_members"]

    _save_store(target_username, tgt)
    clear_patient(source_username)


# ==========================================================
# SESSION
# ==========================================================
def set_logged_in(username: str, user_record: dict):
    """Mark this session as authenticated."""
    st.session_state.auth_user = username
    st.session_state.auth_record = user_record
    st.session_state.is_authenticated = True


def logout():
    """Sign out completely. Triggers Streamlit OIDC logout if applicable."""
    # Clear Streamlit session
    keys_to_clear = list(st.session_state.keys())
    for k in keys_to_clear:
        # keep only file-fallback entries (internal store; no user data)
        if not k.startswith("_fs_fallback_") and not k.startswith("_pstore_"):
            del st.session_state[k]
    # Trigger Streamlit-native OIDC logout if we're logged in via OIDC
    try:
        if hasattr(st, "user") and getattr(st.user, "is_logged_in", False):
            st.logout()  # Streamlit-native logout: clears OIDC cookie
    except Exception:
        pass


def is_authenticated() -> bool:
    return bool(st.session_state.get("is_authenticated", False))


def current_username() -> Optional[str]:
    return st.session_state.get("auth_user")


def current_user() -> Optional[dict]:
    return st.session_state.get("auth_record")


# ==========================================================
# INVITE CODES (family viewer access)
# ==========================================================
def create_invite_code(
    patient_username: str,
    family_name: str,
    family_email: str,
    relationship: str,
) -> str:
    """
    Generate a cryptographically random 8-char invite code bound to this
    patient + family member. Expires in INVITE_TTL_HOURS hours if unused.
    """
    # 8 chars of base64url → ~48 bits entropy
    raw = stdlib_secrets.token_urlsafe(9).upper()
    code = "".join(c for c in raw if c.isalnum())[:8]
    if len(code) < 8:
        # Fallback for very rare case where filtering removes too much
        code = stdlib_secrets.token_hex(4).upper()

    invites = _load_invites()
    invites[code] = {
        "patient_username": patient_username,
        "family_name": family_name,
        "family_email": family_email,
        "relationship": relationship,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(hours=INVITE_TTL_HOURS)).isoformat(),
        "used": False,
        "used_at": None,
    }
    _save_invites(invites)
    return code


def validate_invite_code(code: str) -> Optional[dict]:
    """Return invite record if the code is valid and not expired."""
    code = (code or "").strip().upper()
    if not code:
        return None
    invites = _load_invites()
    invite = invites.get(code)
    if not invite:
        return None
    # Expiry check
    try:
        expires_at = datetime.fromisoformat(invite["expires_at"])
        if datetime.utcnow() > expires_at and not invite.get("used"):
            return None
    except (KeyError, ValueError):
        pass
    return invite


def mark_invite_used(code: str):
    """Mark an invite as consumed (first use). Subsequent uses still succeed
    during its session lifetime; this creates an audit trail."""
    code = (code or "").strip().upper()
    invites = _load_invites()
    if code in invites and not invites[code].get("used"):
        invites[code]["used"] = True
        invites[code]["used_at"] = datetime.utcnow().isoformat()
        _save_invites(invites)


def revoke_family_invites_for_patient(patient_username: str, family_email: str):
    """
    When a patient removes a family member, invalidate any active codes
    bound to that family email.
    """
    invites = _load_invites()
    to_delete = [
        code for code, rec in invites.items()
        if rec.get("patient_username") == patient_username
        and (rec.get("family_email") or "").lower() == (family_email or "").lower()
    ]
    for code in to_delete:
        del invites[code]
    if to_delete:
        _save_invites(invites)
