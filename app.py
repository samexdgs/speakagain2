import streamlit as st
# DEBUG — remove after Google login works
if st.query_params.get("error"):
    st.error(f"OAuth error: {st.query_params}")
    st.stop()
try:
    _has_auth = "auth" in st.secrets
    _auth_keys = list(st.secrets.get("auth", {}).keys()) if _has_auth else []
    st.sidebar.caption(f"DEBUG auth section present: {_has_auth}")
    st.sidebar.caption(f"DEBUG auth keys: {_auth_keys}")
except Exception as e:
    st.sidebar.caption(f"DEBUG error: {e}")
    
    """
SpeakAgain — Multilingual AI Aphasia Rehabilitation Platform
============================================================
Samuel Oluwakoya · Lagos, Nigeria
Contact: soluwakoyat@gmail.com · samueloluwakoyat@gmail.com

Main entry point. Orchestrates authentication, state persistence, UI routing,
and real-time family dashboard sync.

Security + privacy posture:
- All patient state lives in a server-side shared store keyed by username
- Profile + assessment survive logout/login (returning user lands where they left)
- Only CRISIS events page family by email; everyday activity stays in-app
- Sender email is never surfaced to the UI
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import random
import io
import base64
import plotly.graph_objects as go
import plotly.express as px

from clinical_data import (
    APHASIA_TYPES, ASSESSMENT_TASKS, classify_aphasia,
    PHRASES_MASTER, get_phrases_for_language,
    LANGUAGES, get_tts_lang_code, get_tts_tld,
    RELATIONSHIPS, expand_with_family, suggest_family_name_phrases,
    get_word_bank, get_exercise_difficulty,
    detect_crisis,
    LEVELS, XP_REWARDS, get_level, get_next_level, progress_to_next_level,
)
from i18n import t
from ai_completion import complete_sentence, predict_next_words
from brevo_mailer import (
    send_daily_summary, send_crisis_alert, send_milestone_email,
    send_family_invite, send_welcome_email,
)
from auth import (
    signup, login, logout, set_logged_in,
    is_authenticated, current_username, current_user,
    google_oauth_configured, google_current_user, register_or_fetch_google_user,
    create_invite_code, validate_invite_code, mark_invite_used,
    revoke_family_invites_for_patient,
)
from games import play_game
from patient_store import (
    save_profile, save_assessment, save_progress,
    append_activity, load_patient_state, get_activity_feed,
)

try:
    from gtts import gTTS
    TTS_AVAILABLE = True
except Exception:
    TTS_AVAILABLE = False


# ==========================================================
# PAGE CONFIG
# ==========================================================
st.set_page_config(
    page_title="SpeakAgain",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_css():
    st.markdown("""
    <style>
    html, body, [class*="css"] { font-size: 16px !important; }
    .phrase-card {
        background: #EBF4FF; border: 1px solid #B5D4F4;
        border-radius: 10px; padding: 14px 18px; margin: 8px 0;
        font-size: 17px; color: #1A3A5C;
    }
    .suggestion {
        background: #FFFFFF; border: 1px solid #D3D1C7;
        border-radius: 10px; padding: 16px; margin: 10px 0;
        font-size: 18px; line-height: 1.5;
    }
    .suggestion-top { border-color: #639922; background: #EAF3DE; }
    .confidence-high { color: #27500A; font-weight: 500; }
    .confidence-med  { color: #854F0B; font-weight: 500; }
    .confidence-low  { color: #5F5E5A; font-weight: 500; }
    .hero {
        background: linear-gradient(135deg, #1A3A5C, #2B6CB0);
        color: white; padding: 24px 28px; border-radius: 14px; margin-bottom: 20px;
    }
    .hero h1 { color: white; margin: 0; font-size: 26px; font-weight: 500; }
    .hero p  { color: #B5D4F4; margin-top: 6px; font-size: 15px; }
    .xp-bar {
        background: #F1EFE8; border-radius: 12px; height: 14px;
        overflow: hidden; margin: 8px 0;
    }
    .xp-fill {
        background: linear-gradient(90deg, #639922, #97C459);
        height: 100%; border-radius: 12px;
    }
    .family-card {
        background: #F7FBFF; border: 0.5px solid #B5D4F4;
        border-radius: 10px; padding: 12px 14px; margin: 6px 0;
    }
    .activity-item {
        padding: 10px 14px; background: white; border-radius: 8px;
        border-left: 3px solid #2B6CB0; margin: 6px 0; font-size: 14px;
    }
    .activity-item.concern { border-left-color: #A32D2D; background: #FDF4F4; }
    .activity-item.milestone { border-left-color: #639922; background: #F4F9EC; }
    .activity-time { color: #888; font-size: 12px; }
    .invite-code-display {
        background: #1A3A5C; color: #FFFFFF;
        font-family: monospace; font-size: 22px; letter-spacing: 3px;
        text-align: center; padding: 14px; border-radius: 8px; margin: 12px 0;
    }
    </style>
    """, unsafe_allow_html=True)


inject_css()


# ==========================================================
# SESSION-STATE INITIALISATION
# ==========================================================
def init_state():
    """Session defaults. Does NOT include persistent data — that's loaded
    separately from the patient store on login."""
    defaults = {
        "profile": None,
        "assessment_complete": False,
        "aphasia_type": None,
        "severity": None,
        "severity_history": [],
        "context_history": [],
        "communicated_today": [],
        "exercise_log": [],
        "emotion_log": [],
        "recovered_words": set(),
        "streak_days": 0,
        "last_session_date": None,
        "daily_target": 5,
        "last_suggestions": [],
        "last_suggestion_source": "",
        "family_members": [],
        "xp": 0,
        "current_exercise": None,
        "exercise_hints_used": 0,
        "game_state": None,
        "auth_mode": "login",           # "login" or "signup"
        "family_viewer": None,          # {"code", "patient_username", ...} when viewing dashboard
        "_profile_loaded": False,       # flag to avoid re-loading on every rerun
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()


# ==========================================================
# STATE SYNC HELPERS
# ==========================================================
def _restore_patient_state(username: str):
    """
    On login, pull this user's persisted state into session_state.
    This is why a returning user does not redo the assessment.
    """
    if not username:
        return
    data = load_patient_state(username)

    if data.get("profile"):
        st.session_state.profile = data["profile"]
    if data.get("assessment_complete"):
        st.session_state.assessment_complete = True
    if data.get("aphasia_type"):
        st.session_state.aphasia_type = data["aphasia_type"]
    if data.get("severity") is not None:
        st.session_state.severity = data["severity"]
    if data.get("severity_history"):
        st.session_state.severity_history = data["severity_history"]
    if data.get("xp") is not None:
        st.session_state.xp = data["xp"]
    if data.get("streak_days") is not None:
        st.session_state.streak_days = data["streak_days"]
    if data.get("last_session_date"):
        try:
            st.session_state.last_session_date = datetime.fromisoformat(
                data["last_session_date"]
            ).date() if isinstance(data["last_session_date"], str) else data["last_session_date"]
        except Exception:
            pass
    if data.get("recovered_words"):
        rw = data["recovered_words"]
        st.session_state.recovered_words = set(rw) if isinstance(rw, list) else rw
    if data.get("exercise_log"):
        st.session_state.exercise_log = data["exercise_log"]
    if data.get("family_members"):
        st.session_state.family_members = data["family_members"]

    st.session_state._profile_loaded = True


def _persist_patient_state():
    """Push critical state back to the shared store."""
    username = current_username()
    if not username:
        return
    updates = {
        "xp": st.session_state.xp,
        "streak_days": st.session_state.streak_days,
        "last_session_date": (
            st.session_state.last_session_date.isoformat()
            if st.session_state.last_session_date else None
        ),
        "recovered_words": sorted(list(st.session_state.recovered_words)),
        "exercise_log": st.session_state.exercise_log[-500:],  # keep last 500
        "family_members": st.session_state.family_members,
        "severity_history": st.session_state.severity_history,
    }
    save_progress(username, updates)


# ==========================================================
# LANGUAGE / TRANSLATION HELPERS
# ==========================================================
def get_lang() -> str:
    if st.session_state.profile:
        return st.session_state.profile.get("language", "English")
    return "English"


def TR(key: str) -> str:
    return t(key, get_lang())


# ==========================================================
# TTS
# ==========================================================
def text_to_speech_html(text: str, lang: str = "en", tld: str = "co.uk") -> str:
    if not TTS_AVAILABLE or not text:
        return ""
    try:
        clean = text.strip()
        if not clean:
            return ""
        tts = gTTS(text=clean, lang=lang, tld=tld, slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        audio_b64 = base64.b64encode(buf.read()).decode()
        return (
            f'<audio autoplay controls style="width:100%;margin-top:6px;">'
            f'<source src="data:audio/mpeg;base64,{audio_b64}" type="audio/mpeg"></audio>'
        )
    except Exception as e:
        return f"<div style='font-size:12px;color:#999'>Voice unavailable: {str(e)[:80]}</div>"


def speak(text: str):
    lang = get_lang()
    html = text_to_speech_html(text, lang=get_tts_lang_code(lang), tld=get_tts_tld(lang))
    if html:
        st.markdown(html, unsafe_allow_html=True)


# ==========================================================
# GAMIFICATION HOOKS
# ==========================================================
def award_xp(amount: int, reason: str = ""):
    before = get_level(st.session_state.xp)["level"]
    st.session_state.xp += amount
    after = get_level(st.session_state.xp)["level"]
    if after > before:
        new_level = get_level(st.session_state.xp)
        st.toast(f"🎉 Level up! {new_level['badge']} {new_level['name']}", icon="🎉")
        # Milestones are shown in the dashboard activity feed and get an email
        _record_activity(
            f"reached level: {new_level['name']}",
            is_milestone=True,
            email_caregiver=True,
        )
    _persist_patient_state()


def update_streak():
    today = datetime.now().date()
    last = st.session_state.last_session_date
    if last is None:
        st.session_state.streak_days = 1
    elif last == today:
        pass
    elif last == today - timedelta(days=1):
        st.session_state.streak_days += 1
        award_xp(XP_REWARDS["streak_day"], "daily streak")
        if st.session_state.streak_days % 7 == 0:
            award_xp(XP_REWARDS["streak_week_bonus"], "weekly streak")
            st.toast(f"🔥 {st.session_state.streak_days}-day streak!", icon="🔥")
    else:
        st.session_state.streak_days = 1
    st.session_state.last_session_date = today
    _persist_patient_state()


# ==========================================================
# CORE EVENT DISPATCH
# ==========================================================
def _record_activity(
    action: str,
    is_concern: bool = False,
    is_milestone: bool = False,
    email_caregiver: bool = False,
    email_detail: str = "",
):
    """
    Single entry point for anything the patient does that family should see.

    Three routing rules:
    1. ALL activities append to the shared store → family dashboard shows them live
    2. is_concern=True → email every registered family member (crisis alert)
    3. is_milestone=True + email_caregiver=True → email ONLY the primary caregiver

    Regular activity (phrase spoken, exercise done) does NOT email anyone.
    This prevents the inbox-spam problem: family sees everything on the
    dashboard; email is reserved for things that actually need attention.
    """
    username = current_username()
    profile = st.session_state.profile
    patient_name = profile["name"] if profile else (username or "Patient")

    # 1) append to shared store (visible on family dashboard)
    if username:
        append_activity(
            username=username,
            action=action,
            is_concern=is_concern,
            is_milestone=is_milestone,
        )

    # 2) crisis: email everyone
    if is_concern:
        for m in st.session_state.family_members:
            if m.get("email"):
                send_crisis_alert(
                    recipient_email=m["email"],
                    recipient_name=m["name"],
                    patient_name=patient_name,
                    concern=action,
                    detail=email_detail,
                )

    # 3) milestone: email primary caregiver (first family member flagged as primary)
    elif is_milestone and email_caregiver:
        primary = None
        for m in st.session_state.family_members:
            if m.get("primary"):
                primary = m
                break
        if not primary and st.session_state.family_members:
            primary = st.session_state.family_members[0]
        if primary and primary.get("email"):
            send_milestone_email(
                recipient_email=primary["email"],
                recipient_name=primary["name"],
                patient_name=patient_name,
                milestone=action,
            )


def register_exercise_result(ex_type: str, correct: bool, word: str = None):
    st.session_state.exercise_log.append({
        "date": datetime.now().isoformat(),
        "type": ex_type, "correct": correct, "word": word,
    })
    if correct and word:
        if word.lower() not in st.session_state.recovered_words:
            st.session_state.recovered_words.add(word.lower())
            award_xp(XP_REWARDS["word_recovered"], f"recovered '{word}'")
    if correct:
        if st.session_state.exercise_hints_used == 0:
            award_xp(XP_REWARDS["hint_free_correct"], "no-hint correct")
        else:
            award_xp(XP_REWARDS["exercise_correct"], "correct")
    else:
        award_xp(XP_REWARDS["exercise_incorrect"], "effort")
    st.session_state.exercise_hints_used = 0
    update_streak()
    _persist_patient_state()


def get_today_stats():
    today = datetime.now().date().isoformat()[:10]
    today_log = [e for e in st.session_state.exercise_log if e["date"][:10] == today]
    return len(today_log), sum(1 for e in today_log if e["correct"]), len(today_log)


# ==========================================================
# AUTH SCREEN
# ==========================================================
def _handle_google_return():
    """If Streamlit has an active OIDC session, sign us in automatically."""
    claims = google_current_user()
    if not claims:
        return False
    try:
        user_record = register_or_fetch_google_user(claims)
        username = f"google:{claims['email'].lower()}"
        set_logged_in(username, user_record)
        _restore_patient_state(username)
        return True
    except Exception:
        return False


def render_auth():
    lang = get_lang()
    st.markdown(f"""
    <div class="hero">
      <h1>💬 {t('auth.welcome_title', lang)}</h1>
      <p>Multilingual AI aphasia rehabilitation</p>
    </div>
    """, unsafe_allow_html=True)

    tab_account, tab_family = st.tabs([
        f"{t('auth.login', lang)} / {t('auth.signup', lang)}",
        t("auth.family_invite", lang),
    ])

    with tab_account:
        col1, col2 = st.columns([1, 1])

        # -------- LEFT: username + password --------
        with col1:
            mode_options = [t("auth.login", lang), t("auth.signup", lang)]
            mode_choice = st.radio(
                " ", mode_options, horizontal=True,
                label_visibility="collapsed", key="auth_mode_radio",
            )
            st.session_state.auth_mode = (
                "signup" if mode_choice == t("auth.signup", lang) else "login"
            )

            if st.session_state.auth_mode == "login":
                with st.form("login_form", clear_on_submit=False):
                    username = st.text_input(t("auth.username", lang))
                    password = st.text_input(t("auth.password", lang), type="password")
                    submitted = st.form_submit_button(
                        t("auth.login", lang),
                        use_container_width=True, type="primary",
                    )
                    if submitted:
                        ok, msg, user = login(username, password)
                        if ok:
                            uname = username.strip().lower()
                            set_logged_in(uname, user)
                            _restore_patient_state(uname)
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
            else:
                with st.form("signup_form", clear_on_submit=False):
                    username = st.text_input(
                        t("auth.username", lang),
                        help="3+ chars: letters, digits, _, -, ., @",
                    )
                    email = st.text_input(
                        f"{t('auth.email', lang)} ({t('optional', lang)})"
                    )
                    password = st.text_input(
                        t("auth.password", lang), type="password",
                        help="At least 8 characters",
                    )
                    submitted = st.form_submit_button(
                        t("auth.signup", lang),
                        use_container_width=True, type="primary",
                    )
                    if submitted:
                        ok, msg = signup(username, password, email)
                        if ok:
                            # Immediate login after signup
                            _, _, user = login(username, password)
                            uname = username.strip().lower()
                            set_logged_in(uname, user)
                            if email.strip():
                                send_welcome_email(email.strip(), uname)
                            st.success("Account created.")
                            st.rerun()
                        else:
                            st.error(msg)

        # -------- RIGHT: Google OAuth --------
        with col2:
            st.markdown(f"#### {t('auth.or', lang)}")

            if google_oauth_configured():
                # Streamlit's st.login() redirects to Google; on return,
                # st.user.is_logged_in becomes True and _handle_google_return()
                # picks it up on the next script execution.
                #
                # IMPORTANT: with a flat [auth] block (no [auth.google] subsection),
                # st.login() MUST be called with NO arguments. Passing a provider
                # name like "google" makes Streamlit look for [auth.google] and
                # produce "missing provider for oauth callback" → internal server
                # error. See: docs.streamlit.io/.../st.login (Example 1).
                if st.button(
                    f"🔑 {t('auth.google', lang)}",
                    use_container_width=True, key="google_login_btn",
                    type="secondary",
                ):
                    st.login()
            else:
                st.info(
                    "Google sign-in is available when the site owner enables it. "
                    "Meanwhile, use username + password — it takes 20 seconds."
                )

    with tab_family:
        st.markdown(f"#### {t('auth.family_invite', lang)}")
        st.caption(
            "Family members: paste the 8-character code from your invite email. "
            "No account needed — just the code."
        )
        code_input = st.text_input(
            t("auth.invite_code", lang), max_chars=8, key="fam_code_in",
        )
        if st.button(t("auth.join_family", lang), type="primary"):
            code = (code_input or "").strip().upper()
            if not code:
                st.error("Please paste the code from your email.")
            else:
                invite = validate_invite_code(code)
                if not invite:
                    st.error(
                        "This code is invalid, expired, or cancelled. "
                        "Ask the person who invited you for a new one."
                    )
                else:
                    mark_invite_used(code)
                    st.session_state.family_viewer = {
                        "code": code,
                        "patient_username": invite["patient_username"],
                        "family_name": invite["family_name"],
                        "relationship": invite["relationship"],
                    }
                    st.success(f"Welcome, {invite['family_name']}!")
                    st.rerun()


# ==========================================================
# ONBOARDING (after auth, if no profile yet)
# ==========================================================
def render_onboarding():
    lang = get_lang()
    st.markdown(f"""
    <div class="hero">
      <h1>{t('auth.welcome_title', lang)}</h1>
      <p>{t('onboard.setup_profile', lang)}</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("profile_form"):
        user = current_user()
        default_name = (
            user.get("display_name")
            if user and user.get("display_name")
            else (current_username() or "")
        )
        default_email = user.get("email", "") if user else ""

        name = st.text_input(t("onboard.your_name", lang), value=default_name)
        email = st.text_input(t("auth.email", lang), value=default_email)
        language = st.selectbox(
            t("onboard.language", lang),
            list(LANGUAGES.keys()),
            help="All app text, voice output, and phrases will use this language.",
        )
        hand = st.radio(
            "Which hand do you write with?", ["Right", "Left"], horizontal=True,
        )

        submitted = st.form_submit_button(
            t("onboard.start_app", lang), use_container_width=True, type="primary",
        )
        if submitted:
            if not name.strip():
                st.error("Please enter your name.")
            else:
                profile = {
                    "name": name.strip(),
                    "email": email.strip(),
                    "language": language,
                    "hand": hand.lower(),
                    "created_at": datetime.now().isoformat(),
                }
                st.session_state.profile = profile
                save_profile(current_username(), profile)
                if email.strip():
                    send_welcome_email(email.strip(), name.strip())
                st.rerun()


# ==========================================================
# ASSESSMENT
# ==========================================================
def render_assessment():
    lang = get_lang()
    st.markdown("## Quick aphasia assessment")
    st.caption("8 questions, 5 minutes. Helps us personalise everything.")

    with st.form("assessment_form"):
        responses = {}
        for task in ASSESSMENT_TASKS:
            st.markdown(f"**{task['prompt']}**")
            option_labels = [opt[0] for opt in task["options"]]
            choice = st.radio(
                "Select one:", option_labels,
                key=f"ass_{task['id']}", label_visibility="collapsed",
            )
            score = next(opt[1] for opt in task["options"] if opt[0] == choice)
            responses[task["id"]] = score
            st.markdown("---")

        if st.form_submit_button(
            t("btn.submit", lang), use_container_width=True, type="primary",
        ):
            aph_type, severity = classify_aphasia(responses)
            st.session_state.aphasia_type = aph_type
            st.session_state.severity = severity
            st.session_state.severity_history.append(
                (datetime.now().isoformat(), severity)
            )
            st.session_state.assessment_complete = True
            # Persist so the user does NOT retake on next login
            save_assessment(current_username(), aph_type, severity)
            save_progress(current_username(), {
                "severity_history": st.session_state.severity_history,
            })
            award_xp(50, "assessment completed")
            st.rerun()


def render_assessment_result():
    lang = get_lang()
    aph = APHASIA_TYPES[st.session_state.aphasia_type]
    sev = st.session_state.severity

    st.markdown(f"""
    <div class="hero" style="background: linear-gradient(135deg, {aph['color']}, #1A3A5C);">
      <h1>{aph['name']}</h1>
      <p>Severity score: <strong>{sev} / 5</strong></p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### What this means")
    st.markdown(aph["description"])
    st.markdown(f"**Recovery focus:** {aph['recovery_focus']}")

    c1, c2, c3 = st.columns(3)
    c1.metric("Severity", f"{sev} / 5")
    c2.metric("Difficulty", f"Level {get_exercise_difficulty(sev)}")
    c3.metric("Type", aph["name"].split(" (")[0])

    if st.button(
        f"{t('btn.continue', lang)} →", use_container_width=True, type="primary",
    ):
        st.rerun()


# ==========================================================
# COMMUNICATION
# ==========================================================
def render_communication():
    lang = get_lang()
    st.markdown(f"## 💬 {t('comm.title', lang)}")
    lang_label = LANGUAGES[lang]["label"]
    st.caption(f"Language: **{lang_label}** — type anything and I'll complete it.")

    fragment = st.text_input(
        t("comm.prompt", lang),
        placeholder="e.g. hungry" if lang == "English" else "...",
        key="comm_fragment",
    )

    col_go, _ = st.columns([1, 3])
    with col_go:
        go_clicked = st.button(
            f"{t('comm.complete', lang)} →",
            use_container_width=True, type="primary",
        )

    # Predictive word buttons — bug-fixed: these just speak, don't overwrite input
    if fragment:
        last_word = fragment.split()[-1] if fragment.split() else ""
        predictions = predict_next_words(last_word, limit=6, language=lang)
        if predictions and last_word:
            st.caption(f"💡 {t('comm.tap_word', lang)}")
            cols = st.columns(len(predictions))
            for i, word in enumerate(predictions):
                with cols[i]:
                    if st.button(word, key=f"pred_{i}_{word}", use_container_width=True):
                        speak(word)

    # Family name suggestions
    if fragment and st.session_state.family_members:
        family_sugg = suggest_family_name_phrases(fragment, st.session_state.family_members)
        if family_sugg:
            st.caption(f"👪 {t('comm.family_suggestions', lang)}")
            for i, sugg in enumerate(family_sugg):
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(
                        f'<div class="phrase-card">{sugg}</div>', unsafe_allow_html=True
                    )
                with c2:
                    if st.button("🔊", key=f"famsug_{i}", use_container_width=True):
                        speak(sugg)
                        award_xp(XP_REWARDS["communication_sent"])
                        # Log to dashboard but DO NOT email (not a crisis)
                        _record_activity(f'said "{sugg}"')

    # AI completion
    if go_clicked and fragment.strip():
        with st.spinner(f"Generating in {lang_label}..."):
            suggestions, source = complete_sentence(
                fragment,
                aphasia_type=st.session_state.aphasia_type or "anomic",
                language=lang,
                context_history=st.session_state.context_history[-5:],
                family_members=st.session_state.family_members,
            )
            if source == "offline":
                suggestions = [
                    (expand_with_family(s, st.session_state.family_members), c)
                    for s, c in suggestions
                ]
            st.session_state.last_suggestions = suggestions
            st.session_state.last_suggestion_source = source

    if st.session_state.last_suggestions:
        source_label = "AI" if st.session_state.last_suggestion_source == "ai" else "Offline"
        st.caption(f"{source_label} suggestions in {lang_label}")
        for i, (sentence, confidence) in enumerate(st.session_state.last_suggestions[:3]):
            is_top = i == 0
            conf_class = (
                "confidence-high" if confidence >= 0.8 else
                "confidence-med" if confidence >= 0.65 else
                "confidence-low"
            )
            css = "suggestion suggestion-top" if is_top else "suggestion"
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"""
                <div class="{css}">
                <strong>{sentence}</strong><br>
                <span class="{conf_class}">{t('comm.confidence', lang)}: {int(confidence * 100)}%</span>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                if st.button(
                    f"🔊 {t('btn.speak', lang)}",
                    key=f"speak_{i}", use_container_width=True,
                ):
                    speak(sentence)
                    st.session_state.communicated_today.append({
                        "date": datetime.now().isoformat(), "sentence": sentence,
                    })
                    st.session_state.context_history.append(sentence)
                    award_xp(XP_REWARDS["communication_sent"])
                    # Crisis check routes to family email; otherwise just log to dashboard
                    concern = detect_crisis(sentence)
                    if concern:
                        _record_activity(
                            concern, is_concern=True, email_detail=sentence,
                        )
                        st.warning(f"⚠️ Family alerted: {concern}")
                    else:
                        _record_activity(f'said "{sentence}"')

    st.markdown("---")
    st.markdown(f"### {t('comm.quick_phrases', lang)} — {lang_label}")

    phrases = get_phrases_for_language(lang)
    category_labels = {
        "Urgent needs": t("cat.urgent", lang),
        "Basic needs": t("cat.basic", lang),
        "Feelings": t("cat.feelings", lang),
        "Requests": t("cat.requests", lang),
        "Family and social": t("cat.family", lang),
        "Food and drink": t("cat.food", lang),
        "Rehabilitation": t("cat.rehab", lang),
    }
    categories = list(phrases.keys())
    labels = [category_labels.get(c, c) for c in categories]
    tabs = st.tabs(labels)
    for tab, category in zip(tabs, categories):
        with tab:
            for i, phrase in enumerate(phrases[category]):
                display_phrase = expand_with_family(phrase, st.session_state.family_members)
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(
                        f'<div class="phrase-card">{display_phrase}</div>',
                        unsafe_allow_html=True,
                    )
                with c2:
                    if st.button("🔊", key=f"ph_{category}_{i}", use_container_width=True):
                        speak(display_phrase)
                        st.session_state.communicated_today.append({
                            "date": datetime.now().isoformat(),
                            "sentence": display_phrase,
                        })
                        award_xp(XP_REWARDS["communication_sent"])
                        concern = detect_crisis(display_phrase)
                        if concern:
                            _record_activity(
                                concern, is_concern=True, email_detail=display_phrase,
                            )
                            st.warning(f"⚠️ {concern}")
                        else:
                            _record_activity(f'said "{display_phrase}"')


# ==========================================================
# EXERCISES
# ==========================================================
def render_exercises():
    lang = get_lang()
    st.markdown(f"## 🧠 {t('ex.title', lang)}")
    severity = st.session_state.severity or 2.5
    difficulty = get_exercise_difficulty(severity)

    completed, correct, _ = get_today_stats()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t("ex.today", lang), f"{completed}/{st.session_state.daily_target}")
    c2.metric(t("ex.accuracy", lang), f"{(correct/completed*100 if completed else 0):.0f}%")
    c3.metric(t("ex.streak", lang), f"{st.session_state.streak_days}d")
    c4.metric(t("ex.difficulty", lang), f"Level {difficulty}")

    st.markdown("---")

    ex_options = {
        t("ex.word_retrieval", lang): "word_retrieval",
        t("ex.sentence_building", lang): "sentence_building",
        t("ex.cloze", lang): "cloze",
        t("ex.reading", lang): "reading",
        t("ex.repetition", lang): "repetition",
    }
    choice_label = st.selectbox("Exercise type", list(ex_options.keys()))
    ex_type = ex_options[choice_label]

    if ex_type == "word_retrieval":
        render_word_retrieval(difficulty, lang)
    elif ex_type == "sentence_building":
        render_sentence_building(difficulty, lang)
    elif ex_type == "cloze":
        render_cloze(difficulty, lang)
    elif ex_type == "reading":
        render_reading(difficulty, lang)
    elif ex_type == "repetition":
        render_repetition(difficulty, lang)


def render_word_retrieval(difficulty: int, lang: str):
    st.markdown(f"### {t('ex.word_retrieval', lang)}")

    if (st.session_state.current_exercise is None
            or st.session_state.current_exercise.get("type") != "word_retrieval"):
        word = random.choice(get_word_bank(lang, difficulty))
        st.session_state.current_exercise = {
            "type": "word_retrieval", "word": word, "hint_level": 0,
        }
        st.session_state.exercise_hints_used = 0

    ex = st.session_state.current_exercise
    word = ex["word"]

    st.markdown(f"A word starting with **{word[0].upper()}** ({len(word)} letters)")

    if ex["hint_level"] >= 1:
        st.info(f"First letters: **{word[:max(1, len(word)//3)]}**")
        st.session_state.exercise_hints_used = 1
    if ex["hint_level"] >= 2:
        partial = word[:len(word)//2] + "_" * (len(word) - len(word)//2)
        st.info(f"Half shown: **{partial}**")
        st.session_state.exercise_hints_used = 2
    if ex["hint_level"] >= 3:
        st.info(f"The word is: **{word}**")
        st.session_state.exercise_hints_used = 3

    answer = st.text_input(t("ex.your_answer", lang), key=f"wr_{word}")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button(t("btn.check", lang), use_container_width=True, type="primary"):
            if answer.strip().lower() == word.lower():
                st.success(f"🎉 {t('ex.correct', lang)} **{word}**")
                register_exercise_result("word_retrieval", correct=True, word=word)
                speak(word)
            else:
                st.error(t("ex.try_hint", lang))
    with c2:
        if st.button(f"🔊 {t('btn.speak', lang)}", use_container_width=True):
            speak(word)
    with c3:
        if st.button(t("btn.hint", lang), use_container_width=True):
            if ex["hint_level"] < 3:
                ex["hint_level"] += 1
                st.rerun()
    with c4:
        if st.button(t("btn.next", lang), use_container_width=True):
            st.session_state.current_exercise = None
            st.rerun()


def render_sentence_building(difficulty: int, lang: str):
    st.markdown(f"### {t('ex.sentence_building', lang)}")
    words = get_word_bank(lang, difficulty)
    if (st.session_state.current_exercise is None
            or st.session_state.current_exercise.get("type") != "sentence_building"):
        sample = random.sample(words, min(4, len(words)))
        templates = {
            "English": f"I want a {sample[0]} and {sample[1]}",
            "Spanish": f"Quiero un {sample[0]} y {sample[1]}",
            "French": f"Je veux un {sample[0]} et {sample[1]}",
            "Portuguese": f"Quero um {sample[0]} e {sample[1]}",
        }
        template = templates.get(lang, " ".join(sample[:3]))
        jumbled = template.split()
        random.shuffle(jumbled)
        st.session_state.current_exercise = {
            "type": "sentence_building", "jumbled": jumbled, "correct": template,
        }

    ex = st.session_state.current_exercise
    st.markdown(f"**Jumbled:** {', '.join(ex['jumbled'])}")
    answer = st.text_input("Arrange them:", key=f"sb_{ex['correct']}")
    c1, c2 = st.columns(2)
    with c1:
        if st.button(t("btn.check", lang), use_container_width=True, type="primary"):
            if answer.strip().lower() == ex["correct"].lower():
                st.success(f"🎉 {t('ex.correct', lang)}")
                register_exercise_result("sentence_building", correct=True)
                speak(ex["correct"])
            else:
                st.warning(f"Correct: **{ex['correct']}**")
                register_exercise_result("sentence_building", correct=False)
    with c2:
        if st.button(t("btn.next", lang), use_container_width=True):
            st.session_state.current_exercise = None
            st.rerun()


def render_cloze(difficulty: int, lang: str):
    st.markdown(f"### {t('ex.cloze', lang)}")
    pools = {
        "English": [
            ("I drink ___", ["water", "chair", "tree"], "water"),
            ("I sleep in the ___", ["bed", "car", "fish"], "bed"),
            ("I brush my ___", ["teeth", "book", "sun"], "teeth"),
        ],
        "Spanish": [
            ("Bebo ___", ["agua", "silla", "árbol"], "agua"),
            ("Duermo en la ___", ["cama", "puerta", "lámpara"], "cama"),
        ],
        "French": [
            ("Je bois de l' ___", ["eau", "chaise", "arbre"], "eau"),
            ("Je dors dans le ___", ["lit", "sac", "jardin"], "lit"),
        ],
        "Portuguese": [
            ("Bebo ___", ["água", "cadeira", "árvore"], "água"),
            ("Durmo na ___", ["cama", "mesa", "porta"], "cama"),
        ],
        "Yoruba": [("Mo mu ___", ["omi", "aga", "igi"], "omi")],
        "Igbo": [("Ana m aṅụ ___", ["mmiri", "akpa", "akwụkwọ"], "mmiri")],
        "Hausa": [("Ina shan ___", ["ruwa", "kujera", "itace"], "ruwa")],
        "Pidgin": [("I dey drink ___", ["water", "chair", "book"], "water")],
        "Arabic": [("أشرب ___", ["ماء", "كرسي", "شجرة"], "ماء")],
    }
    pool = pools.get(lang, pools["English"])

    if (st.session_state.current_exercise is None
            or st.session_state.current_exercise.get("type") != "cloze"):
        s, opts, ans = random.choice(pool)
        st.session_state.current_exercise = {
            "type": "cloze", "sentence": s, "options": opts, "answer": ans,
        }

    ex = st.session_state.current_exercise
    st.markdown(f"### _{ex['sentence']}_")
    choice = st.radio("Which word?", ex["options"], key=f"cz_{ex['sentence']}")
    c1, c2 = st.columns(2)
    with c1:
        if st.button(t("btn.check", lang), use_container_width=True, type="primary"):
            if choice == ex["answer"]:
                st.success(f"🎉 {t('ex.correct', lang)}")
                register_exercise_result("cloze", correct=True)
                speak(ex["sentence"].replace("___", choice))
            else:
                st.error(f"Answer: **{ex['answer']}**")
                register_exercise_result("cloze", correct=False)
    with c2:
        if st.button(t("btn.next", lang), use_container_width=True):
            st.session_state.current_exercise = None
            st.rerun()


def render_reading(difficulty: int, lang: str):
    st.markdown(f"### {t('ex.reading', lang)}")
    passages = {
        "English": [{"text": "James ate lunch. He was hungry.",
                     "q": "Did James eat lunch?", "opts": ["Yes", "No"], "ans": "Yes"}],
        "Spanish": [{"text": "Juan comió. Tenía hambre.",
                     "q": "¿Juan comió?", "opts": ["Sí", "No"], "ans": "Sí"}],
        "French": [{"text": "Pierre a mangé. Il avait faim.",
                    "q": "Pierre a mangé?", "opts": ["Oui", "Non"], "ans": "Oui"}],
        "Portuguese": [{"text": "João comeu. Ele estava com fome.",
                        "q": "João comeu?", "opts": ["Sim", "Não"], "ans": "Sim"}],
    }
    pool = passages.get(lang, passages["English"])

    if (st.session_state.current_exercise is None
            or st.session_state.current_exercise.get("type") != "reading"):
        st.session_state.current_exercise = {"type": "reading", **random.choice(pool)}

    ex = st.session_state.current_exercise
    st.markdown(f'<div class="phrase-card">{ex["text"]}</div>', unsafe_allow_html=True)
    if st.button(f"🔊 {t('btn.speak', lang)}", key="read_speak"):
        speak(ex["text"])

    st.markdown(f"**{ex['q']}**")
    choice = st.radio("Your answer:", ex["opts"], key=f"rd_{ex['text']}")
    c1, c2 = st.columns(2)
    with c1:
        if st.button(t("btn.submit", lang), use_container_width=True, type="primary"):
            if choice == ex["ans"]:
                st.success(f"🎉 {t('ex.correct', lang)}")
                register_exercise_result("reading", correct=True)
            else:
                st.error(f"Answer: **{ex['ans']}**")
                register_exercise_result("reading", correct=False)
    with c2:
        if st.button(t("btn.next", lang), use_container_width=True):
            st.session_state.current_exercise = None
            st.rerun()


def render_repetition(difficulty: int, lang: str):
    st.markdown(f"### {t('ex.repetition', lang)}")
    words = get_word_bank(lang, difficulty)
    if (st.session_state.current_exercise is None
            or st.session_state.current_exercise.get("type") != "repetition"):
        st.session_state.current_exercise = {
            "type": "repetition", "word": random.choice(words),
        }
    ex = st.session_state.current_exercise
    word = ex["word"]
    if st.button(f"🔊 {t('btn.speak', lang)}", type="primary"):
        speak(word)
    answer = st.text_input("Type what you heard:", key=f"rep_{word}")
    c1, c2 = st.columns(2)
    with c1:
        if st.button(t("btn.check", lang), use_container_width=True):
            if answer.strip().lower() == word.lower():
                st.success(f"🎉 {t('ex.correct', lang)} **{word}**")
                register_exercise_result("repetition", correct=True, word=word)
            else:
                st.warning(f"Word: **{word}**")
                register_exercise_result("repetition", correct=False, word=word)
    with c2:
        if st.button(t("btn.next", lang), use_container_width=True):
            st.session_state.current_exercise = None
            st.rerun()


# ==========================================================
# GAMES (delegates to games.py)
# ==========================================================
def render_games():
    lang = get_lang()
    st.markdown(f"## 🎮 {t('games.title', lang)}")
    st.caption(t("games.subtitle", lang))

    # Wrap the notify function so games can report to dashboard (not email)
    def _game_notify(msg: str):
        _record_activity(f"game: {msg}")

    if st.session_state.game_state is None:
        games_list = [
            {"id": "word_match", "name": t("games.word_match", lang),
             "desc": "Match emoji pictures with their word.", "xp": 50, "icon": "🎯"},
            {"id": "category_sort", "name": t("games.category_sort", lang),
             "desc": "Sort words into food, places, and feelings.", "xp": 40, "icon": "🧺"},
            {"id": "sentence_puzzle", "name": t("games.sentence_puzzle", lang),
             "desc": "Rearrange scrambled words into a sentence.", "xp": 50, "icon": "🧩"},
            {"id": "first_letter", "name": t("games.first_letter", lang),
             "desc": "Name words starting with a given letter.", "xp": 60, "icon": "🔤"},
            {"id": "story_builder", "name": t("games.story_builder", lang),
             "desc": "Fill the missing word in each story sentence.", "xp": 70, "icon": "📖"},
        ]
        cols = st.columns(2)
        for i, g in enumerate(games_list):
            with cols[i % 2]:
                st.markdown(f"""
                <div class="phrase-card">
                <strong>{g['icon']} {g['name']}</strong> · +{g['xp']} XP<br>
                <span style="color:#5F5E5A;font-size:13px;">{g['desc']}</span>
                </div>
                """, unsafe_allow_html=True)
                if st.button(
                    f"{t('btn.play', lang)} {g['name']}",
                    key=f"game_{g['id']}", use_container_width=True,
                ):
                    st.session_state.game_state = {"id": g["id"]}
                    st.rerun()
    else:
        game_id = st.session_state.game_state["id"]
        play_game(game_id, lang, award_xp, _game_notify)
        st.markdown("---")
        if st.button(t("btn.close", lang)):
            for key in list(st.session_state.keys()):
                if key in ("picmatch", "cat_sort", "puzzle", "first_letter", "story"):
                    del st.session_state[key]
            st.session_state.game_state = None
            st.rerun()


# ==========================================================
# FAMILY MANAGEMENT
# ==========================================================
def render_family_management():
    lang = get_lang()
    st.markdown(f"## 👪 {t('family.title', lang)}")
    st.caption(
        "Add family members. They receive an 8-character invite code by email — "
        "no account needed. Mark one as 'primary caregiver' to receive the "
        "end-of-day summary email."
    )

    with st.expander(
        f"➕ {t('family.add_member', lang)}",
        expanded=(len(st.session_state.family_members) == 0),
    ):
        with st.form("add_fam"):
            c1, c2 = st.columns(2)
            with c1:
                fname = st.text_input(t("family.name", lang), placeholder="e.g. Samuel")
                frel = st.selectbox(t("family.relationship", lang), RELATIONSHIPS)
            with c2:
                femail = st.text_input("Email (required for invite)")
                fphone = st.text_input("Phone (optional)")
            is_primary = st.checkbox(
                "Primary caregiver (receives daily summary)",
                help="Crisis alerts go to every family member; "
                     "daily summaries go only to the primary caregiver.",
            )

            if st.form_submit_button(t("btn.add", lang), type="primary"):
                if not fname.strip():
                    st.error("Please enter a name.")
                elif not femail.strip():
                    st.error("Email is required so we can send the invite code.")
                else:
                    # If marking as primary, unmark any existing primary
                    if is_primary:
                        for m in st.session_state.family_members:
                            m["primary"] = False

                    code = create_invite_code(
                        patient_username=current_username(),
                        family_name=fname.strip(),
                        family_email=femail.strip(),
                        relationship=frel,
                    )
                    st.session_state.family_members.append({
                        "name": fname.strip(),
                        "relationship": frel,
                        "email": femail.strip(),
                        "phone": fphone.strip(),
                        "invite_code": code,
                        "primary": is_primary,
                        "added": datetime.now().isoformat(),
                    })
                    _persist_patient_state()

                    # Email the invite
                    profile = st.session_state.profile
                    ok, msg = send_family_invite(
                        family_email=femail.strip(),
                        family_name=fname.strip(),
                        patient_name=profile["name"],
                        relationship=frel,
                        invite_code=code,
                    )
                    if ok:
                        st.success(
                            f"✅ Added {fname}. Invite email sent. "
                            f"Code (keep for reference): **{code}**"
                        )
                    else:
                        st.warning(
                            f"Added {fname}. The email could not be sent automatically. "
                            f"Please share this code with them manually: **{code}**"
                        )
                    st.rerun()

    if not st.session_state.family_members:
        st.info("No family members added yet.")
        return

    st.markdown("### Your family")
    for i, m in enumerate(st.session_state.family_members):
        c1, c2 = st.columns([5, 1])
        with c1:
            badges = []
            if m.get("primary"):
                badges.append("★ primary caregiver")
            badge_line = (
                f" <span style='color:#639922;font-size:12px;'>· {' · '.join(badges)}</span>"
                if badges else ""
            )
            st.markdown(f"""
            <div class="family-card">
            <strong>{m['name']}</strong> ({m['relationship']}) · {m.get('email', '')}{badge_line}
            </div>
            """, unsafe_allow_html=True)
        with c2:
            if st.button(t("btn.remove", lang), key=f"rm_{i}", use_container_width=True):
                removed = st.session_state.family_members.pop(i)
                # Revoke any active invite codes tied to this email
                revoke_family_invites_for_patient(
                    current_username(), removed.get("email", "")
                )
                _persist_patient_state()
                st.rerun()


# ==========================================================
# FAMILY DASHBOARD (works for both patient's own view AND family viewer)
# ==========================================================
def render_family_dashboard():
    """
    Two entry paths:
    1. The patient views their own dashboard: reads from live session_state
    2. A family member with an invite code views the patient's activity: reads
       from the shared store keyed by the patient's username.
    Either way, this pulls the activity feed from the shared store so updates
    are visible across sessions.
    """
    lang = get_lang()

    # Determine whose dashboard we're showing
    if st.session_state.family_viewer:
        viewer = st.session_state.family_viewer
        patient_username = viewer["patient_username"]
        state = load_patient_state(patient_username)
        profile = state.get("profile") or {}
        patient_name = profile.get("name", patient_username)
        st.markdown(f"""
        <div class="hero">
          <h1>{patient_name}'s rehabilitation</h1>
          <p>Signed in as {viewer['family_name']} · {viewer['relationship']}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Patient viewing their own recent activity
        patient_username = current_username()
        profile = st.session_state.profile
        if not profile:
            st.info("Set up your profile first.")
            return
        patient_name = profile["name"]
        st.markdown(f"## 📡 Activity feed — {patient_name}")
        state = load_patient_state(patient_username)

    # Summary metrics
    c1, c2, c3, c4 = st.columns(4)

    # Today-only counts (from shared store activity feed)
    activity = get_activity_feed(patient_username, limit=100)
    today_str = datetime.utcnow().date().isoformat()
    today_count = sum(
        1 for a in activity
        if a.get("time", "")[:10] == today_str
    )

    xp_val = state.get("xp", 0) if st.session_state.family_viewer else st.session_state.xp
    streak_val = (
        state.get("streak_days", 0)
        if st.session_state.family_viewer else st.session_state.streak_days
    )

    current_lvl = get_level(xp_val)
    next_lvl = get_next_level(xp_val)
    progress_pct = progress_to_next_level(xp_val)

    c1.metric("Today's activity", today_count)
    c2.metric("Level", f"{current_lvl['badge']} L{current_lvl['level']}")
    c3.metric("XP", xp_val)
    c4.metric("Streak", f"{streak_val}d")

    # Progress bar
    st.markdown(f"**{current_lvl['name']}**")
    if next_lvl:
        st.markdown(f"""
        <div class="xp-bar"><div class="xp-fill" style="width: {progress_pct*100}%"></div></div>
        <small>{int(progress_pct*100)}% to {next_lvl['name']}</small>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Refresh button for family viewers (Streamlit reruns on most interactions
    # but an explicit refresh gives visible control)
    if st.button("🔄 Refresh activity", key="refresh_feed"):
        st.rerun()

    st.markdown("### Recent activity")

    if not activity:
        st.info("No activity yet. It will appear here as it happens.")
    else:
        for item in activity[:30]:
            try:
                time_str = datetime.fromisoformat(item["time"]).strftime("%I:%M %p")
            except Exception:
                time_str = ""
            css_class = "activity-item"
            if item.get("concern"):
                css_class += " concern"
            elif item.get("milestone"):
                css_class += " milestone"
            st.markdown(f"""
            <div class="{css_class}">
            {item.get('action', '')}
            <span class="activity-time"> · {time_str}</span>
            </div>
            """, unsafe_allow_html=True)

    # Recovered words at the bottom
    rw = state.get("recovered_words") or sorted(list(st.session_state.recovered_words))
    st.markdown("---")
    st.markdown("### Recovered words")
    if rw:
        if isinstance(rw, set):
            rw = sorted(list(rw))
        st.markdown(" · ".join(f"**{w}**" for w in rw[:50]))
    else:
        st.caption("Words appear here as they are recovered through exercises.")


# ==========================================================
# PROGRESS (patient-only)
# ==========================================================
def render_progress():
    lang = get_lang()
    st.markdown(f"## 📊 {t('progress.title', lang)}")

    total = len(st.session_state.exercise_log)
    correct = sum(1 for e in st.session_state.exercise_log if e["correct"])
    accuracy = (correct / total * 100) if total else 0

    current_lvl = get_level(st.session_state.xp)
    next_lvl = get_next_level(st.session_state.xp)
    progress_pct = progress_to_next_level(st.session_state.xp)

    st.markdown(f"""
    <div class="hero">
      <h1>{current_lvl['badge']} {current_lvl['name']}</h1>
      <p>{st.session_state.xp} XP · Level {current_lvl['level']}</p>
    </div>
    """, unsafe_allow_html=True)

    if next_lvl:
        st.markdown(f"""
        <div class="xp-bar"><div class="xp-fill" style="width: {progress_pct*100}%"></div></div>
        <small>{int(progress_pct*100)}% {t('progress.to_next_level', lang)} {next_lvl['name']}</small>
        """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t("progress.total_ex", lang), total)
    c2.metric(t("ex.accuracy", lang), f"{accuracy:.0f}%")
    c3.metric(t("ex.streak", lang), f"{st.session_state.streak_days}d")
    c4.metric(t("progress.words_recovered", lang), len(st.session_state.recovered_words))

    if st.session_state.severity_history:
        st.markdown("### Severity over time")
        df = pd.DataFrame(st.session_state.severity_history, columns=["date", "score"])
        df["date"] = pd.to_datetime(df["date"])
        fig = px.line(df, x="date", y="score", markers=True, range_y=[0, 5])
        fig.update_traces(line_color="#2B6CB0", marker=dict(size=12))
        fig.update_layout(height=320, plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

    if st.session_state.exercise_log:
        st.markdown("### Practice calendar (last 30 days)")
        df = pd.DataFrame(st.session_state.exercise_log)
        df["day"] = pd.to_datetime(df["date"]).dt.date
        daily = df.groupby("day").size().reset_index(name="count")
        today_d = datetime.now().date()
        start = today_d - timedelta(days=29)
        full = pd.DataFrame({"day": pd.date_range(start, today_d).date})
        merged = full.merge(daily, on="day", how="left").fillna(0)
        merged["week"] = [(d - start).days // 7 for d in merged["day"]]
        merged["weekday"] = [d.weekday() for d in merged["day"]]
        fig = go.Figure(data=go.Heatmap(
            x=merged["week"], y=merged["weekday"], z=merged["count"],
            colorscale=[[0, "#F1EFE8"], [0.3, "#C0DD97"], [1, "#27500A"]],
            showscale=False,
        ))
        fig.update_layout(
            height=200, plot_bgcolor="white", paper_bgcolor="white",
            yaxis=dict(tickvals=[0,1,2,3,4,5,6],
                       ticktext=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]),
            xaxis=dict(showticklabels=False),
            margin=dict(l=30, r=10, t=20, b=30),
        )
        st.plotly_chart(fig, use_container_width=True)


# ==========================================================
# CAREGIVER TAB (patient-facing, emotional check-in + manual daily send)
# ==========================================================
def render_caregiver():
    lang = get_lang()
    profile = st.session_state.profile
    st.markdown("## 🤝 Caregiver tools")

    st.markdown("### Emotional check-in")
    EMOTIONS_UI = [
        {"emoji": "😰", "label": "In pain", "score": 1, "flag": True},
        {"emoji": "😢", "label": "Sad", "score": 2, "flag": False},
        {"emoji": "😐", "label": "Okay", "score": 3, "flag": False},
        {"emoji": "🙂", "label": "Good", "score": 4, "flag": False},
        {"emoji": "😊", "label": "Great", "score": 5, "flag": False},
    ]
    cols = st.columns(len(EMOTIONS_UI))
    for i, e in enumerate(EMOTIONS_UI):
        with cols[i]:
            if st.button(f"{e['emoji']}\n{e['label']}", key=f"emo_{i}", use_container_width=True):
                st.session_state.emotion_log.append({
                    "date": datetime.now().isoformat(),
                    "emoji": e["emoji"], "label": e["label"], "score": e["score"],
                })
                st.success(f"Logged: {e['emoji']} {e['label']}")
                if e["flag"]:
                    _record_activity(
                        f"feeling: {e['label']}",
                        is_concern=True,
                        email_detail="Emotional check-in flagged as concerning.",
                    )
                else:
                    _record_activity(f"feeling: {e['label']}")

    st.markdown("---")
    st.markdown("### Send daily summary now")
    st.caption("Daily summaries go only to the primary caregiver.")

    primary = None
    for m in st.session_state.family_members:
        if m.get("primary"):
            primary = m
            break
    if not primary and st.session_state.family_members:
        primary = st.session_state.family_members[0]

    if not primary or not primary.get("email"):
        st.info(
            "Add a family member with an email and mark them as the primary caregiver "
            "(Family tab) to enable daily summaries."
        )
    else:
        if st.button(
            f"📧 Send today's summary to {primary['name']} ({primary['email']})",
            use_container_width=True,
        ):
            completed, _, _ = get_today_stats()
            today_em = [e for e in st.session_state.emotion_log
                        if e["date"][:10] == datetime.now().date().isoformat()[:10]]
            emotion_txt = (
                f"{today_em[-1]['label']} ({today_em[-1]['emoji']})"
                if today_em else "Not logged"
            )
            flags = [
                detect_crisis(x["sentence"])
                for x in st.session_state.communicated_today
                if detect_crisis(x["sentence"])
            ]
            ok, msg = send_daily_summary(
                caregiver_email=primary["email"],
                caregiver_name=primary["name"],
                patient_name=profile["name"],
                phrases_communicated=len(st.session_state.communicated_today),
                exercises_completed=completed,
                exercises_total=st.session_state.daily_target,
                streak_days=st.session_state.streak_days,
                xp_earned=st.session_state.xp,
                level_name=get_level(st.session_state.xp)["name"],
                emotion_trend=emotion_txt,
                concerning_flags=flags,
            )
            if ok:
                st.success(f"✅ Sent to {primary['email']}")
            else:
                st.error("We could not send the email right now. Please try again later.")


# ==========================================================
# SETTINGS
# ==========================================================
def render_settings():
    lang = get_lang()
    profile = st.session_state.profile

    st.markdown(f"## ⚙️ {t('nav.settings', lang)}")

    user = current_user()
    if user:
        method = user.get("auth_method", "password")
        ident = user.get("email") or current_username()
        st.markdown(f"**Signed in as:** {ident} · method: {method}")
        if st.button(f"🚪 {t('nav.logout', lang)}", type="secondary"):
            _persist_patient_state()
            logout()
            st.rerun()
        st.markdown("---")

    if profile:
        st.markdown(f"### {t('settings.profile', lang)}")
        for k, v in profile.items():
            if v and k != "created_at":
                st.markdown(f"**{k.replace('_', ' ').title()}:** {v}")

        new_lang = st.selectbox(
            t("settings.change_lang", lang),
            list(LANGUAGES.keys()),
            index=list(LANGUAGES.keys()).index(profile.get("language", "English")),
        )
        if new_lang != profile.get("language"):
            if st.button(t("btn.save", lang)):
                st.session_state.profile["language"] = new_lang
                save_profile(current_username(), st.session_state.profile)
                st.success(f"Language changed to {new_lang}")
                st.rerun()

    st.markdown("---")
    st.session_state.daily_target = st.slider(
        t("settings.daily_target", lang), 1, 20, st.session_state.daily_target,
    )

    st.markdown("---")
    st.markdown("### Reassess")
    st.caption(
        "You can retake the assessment any time. Your XP, streak, and recovered "
        "words will not be lost."
    )
    if st.button("Start reassessment"):
        st.session_state.assessment_complete = False
        st.rerun()

    st.markdown("---")
    st.markdown("### About")
    st.markdown(
        "SpeakAgain is a multilingual AI-powered aphasia rehabilitation tool. "
        "It provides augmentative communication, daily practice, and a family "
        "dashboard for loved ones to stay informed.\n\n"
        "**Contact:** soluwakoyat@gmail.com · samueloluwakoyat@gmail.com\n\n"
        "**Source code:** github.com/samexdgs\n\n"
        "*Not a medical device. Does not replace professional speech therapy.*"
    )


# ==========================================================
# MAIN ROUTER
# ==========================================================
def main():
    lang = get_lang()

    # Automatic Google OIDC return handling — runs every script execution
    # so a user who just returned from Google is signed in immediately.
    if not is_authenticated() and not st.session_state.family_viewer:
        _handle_google_return()

    with st.sidebar:
        st.markdown("# 💬 SpeakAgain")

        # Case A: totally unauthenticated
        if not is_authenticated() and not st.session_state.family_viewer:
            st.caption("Sign in or paste an invite code.")
            st.markdown("---")
            st.caption("soluwakoyat@gmail.com · samueloluwakoyat@gmail.com")
            render_auth()
            return

        # Case B: family viewer (invite-code holder)
        if st.session_state.family_viewer:
            viewer = st.session_state.family_viewer
            st.caption(f"👪 Family view")
            st.markdown(f"**{viewer['family_name']}**")
            st.caption(viewer["relationship"])
            st.markdown("---")
            if st.button("🚪 Sign out"):
                # Family viewer logout: just clear viewer state
                st.session_state.family_viewer = None
                st.rerun()
            render_family_dashboard()
            return

        # Case C: authenticated patient/caregiver
        user = current_user()

        # First-time-after-login bootstrap: restore persisted state
        uname = current_username()
        if uname and not st.session_state._profile_loaded:
            _restore_patient_state(uname)

        if st.session_state.profile:
            profile = st.session_state.profile
            st.markdown(f"### {profile['name']}")
            st.caption(f"🌍 {LANGUAGES[profile['language']]['label']}")
            if st.session_state.aphasia_type:
                aph = APHASIA_TYPES[st.session_state.aphasia_type]
                st.markdown(f"*{aph['name']}*")
                st.caption(f"Severity: {st.session_state.severity}/5")

            lvl = get_level(st.session_state.xp)
            st.markdown(f"**{lvl['badge']} {lvl['name']}**")
            st.caption(f"{st.session_state.xp} XP · {st.session_state.streak_days}d")

            st.markdown("---")

            page_map = {
                t("nav.communication", lang): "communication",
                t("nav.exercises", lang): "exercises",
                t("nav.games", lang): "games",
                t("nav.progress", lang): "progress",
                t("nav.family", lang): "family",
                t("nav.dashboard", lang): "dashboard",
                t("nav.caregiver", lang): "caregiver",
                t("nav.settings", lang): "settings",
            }
            page_label = st.radio(
                t("nav.settings", lang),
                list(page_map.keys()),
                label_visibility="collapsed",
            )
            page = page_map[page_label]
        else:
            page = None

        st.markdown("---")
        if st.button(f"🚪 {t('nav.logout', lang)}"):
            _persist_patient_state()
            logout()
            st.rerun()
        # Contact footer — ONLY the two Gmail addresses. No sender email.
        st.caption("soluwakoyat@gmail.com · samueloluwakoyat@gmail.com")

    # Body routing (authenticated patient flow)
    if not st.session_state.profile:
        render_onboarding()
    elif not st.session_state.assessment_complete:
        render_assessment()
    elif st.session_state.severity is not None and page is None:
        render_assessment_result()
    else:
        if page == "communication":
            render_communication()
        elif page == "exercises":
            render_exercises()
        elif page == "games":
            render_games()
        elif page == "progress":
            render_progress()
        elif page == "family":
            render_family_management()
        elif page == "dashboard":
            render_family_dashboard()
        elif page == "caregiver":
            render_caregiver()
        elif page == "settings":
            render_settings()


if __name__ == "__main__":
    main()
