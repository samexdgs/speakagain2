"""
SpeakAgain v2.1 — Full-featured multilingual AI aphasia rehabilitation
======================================================================
Samuel Oluwakoya · Lagos, Nigeria
Contact: soluwakoyat@gmail.com · samueloluwakoyat@gmail.com
Project #6 Neurological Rehabilitation AI Series

v2.1 (this release):
- Login / signup (username+password) with Google OAuth option
- Family members receive an invite CODE via email — no account needed
- Entire UI translates to the chosen language (not just the phrase bar)
- Five playable games including picture match with emoji visuals
- Session-state bug fixed in communication predictions
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
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
    send_daily_summary, send_realtime_activity, send_family_invite,
    send_welcome_email,
)
from auth import (
    signup, login, logout, login_with_google, set_logged_in,
    is_authenticated, current_username, current_user,
    update_user_profile, get_user_profile,
    create_invite_code, validate_invite_code, consume_invite_code,
    google_oauth_available, trigger_google_login, handle_google_callback,
)
from games import play_game

try:
    from gtts import gTTS
    TTS_AVAILABLE = True
except Exception:
    TTS_AVAILABLE = False


st.set_page_config(
    page_title="SpeakAgain v2.1",
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
    .activity-time { color: #888; font-size: 12px; }
    .google-btn {
        background: white; color: #1A3A5C;
        border: 1px solid #D3D1C7; border-radius: 8px;
        padding: 10px 16px; text-align: center;
        font-weight: 500; text-decoration: none;
        display: inline-block; width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)


inject_css()


# ==========================================================
# SESSION STATE
# ==========================================================
def init_state():
    defaults = {
        "profile": None, "assessment_complete": False,
        "aphasia_type": None, "severity": None,
        "severity_history": [], "context_history": [],
        "communicated_today": [], "exercise_log": [],
        "emotion_log": [], "recovered_words": set(),
        "streak_days": 0, "last_session_date": None,
        "daily_target": 5, "last_suggestions": [],
        "last_suggestion_source": "", "family_members": [],
        "xp": 0, "badges": [],
        "current_exercise": None, "exercise_hints_used": 0,
        "game_state": None, "activity_feed": [],
        "view_as": "patient",
        "auth_mode": "login",  # or "signup"
        "family_viewer": None,  # {"code", "patient_username", "family_name"} when viewing dashboard
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()


# ==========================================================
# HELPERS
# ==========================================================
def get_lang() -> str:
    if st.session_state.profile:
        return st.session_state.profile.get("language", "English")
    return "English"


def TR(key: str) -> str:
    return t(key, get_lang())


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
        return f"""<audio autoplay controls style="width:100%;margin-top:6px;">
        <source src="data:audio/mpeg;base64,{audio_b64}" type="audio/mpeg"></audio>"""
    except Exception as e:
        return f"<div style='font-size:12px;color:#999'>Voice unavailable: {str(e)[:80]}</div>"


def speak(text: str):
    lang = get_lang()
    html = text_to_speech_html(text, lang=get_tts_lang_code(lang), tld=get_tts_tld(lang))
    if html:
        st.markdown(html, unsafe_allow_html=True)


def award_xp(amount: int, reason: str = ""):
    before = get_level(st.session_state.xp)["level"]
    st.session_state.xp += amount
    after = get_level(st.session_state.xp)["level"]
    if after > before:
        new_level = get_level(st.session_state.xp)
        st.toast(f"🎉 Level up! {new_level['badge']} {new_level['name']}", icon="🎉")
        notify_family(f"leveled up to {new_level['name']}", is_milestone=True)


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


def add_activity(action: str, is_concern: bool = False):
    st.session_state.activity_feed.insert(0, {
        "time": datetime.now().isoformat(),
        "action": action,
        "concern": is_concern,
    })
    st.session_state.activity_feed = st.session_state.activity_feed[:50]


def notify_family(activity: str, is_concern: bool = False, is_milestone: bool = False):
    profile = st.session_state.profile
    if not profile:
        return
    add_activity(activity, is_concern)
    for m in st.session_state.family_members:
        if m.get("email"):
            send_realtime_activity(
                family_email=m["email"], family_name=m["name"],
                patient_name=profile["name"], activity=activity,
                activity_detail=activity, is_concern=is_concern,
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


def get_today_stats():
    today = datetime.now().date().isoformat()[:10]
    today_log = [e for e in st.session_state.exercise_log if e["date"][:10] == today]
    return len(today_log), sum(1 for e in today_log if e["correct"]), len(today_log)


# ==========================================================
# AUTH SCREEN (login / signup / google / family-invite)
# ==========================================================
def render_auth():
    lang = get_lang()
    st.markdown(f"""
    <div class="hero">
      <h1>💬 {t('auth.welcome_title', lang)}</h1>
      <p>Multilingual AI aphasia rehabilitation · Samuel Oluwakoya, Lagos, Nigeria<br>
      Contact: soluwakoyat@gmail.com · samueloluwakoyat@gmail.com</p>
    </div>
    """, unsafe_allow_html=True)

    tab_account, tab_family = st.tabs([
        t("auth.login", lang) + " / " + t("auth.signup", lang),
        t("auth.family_invite", lang),
    ])

    with tab_account:
        col1, col2 = st.columns([1, 1])

        with col1:
            mode_toggle = st.radio(
                " ",
                [t("auth.login", lang), t("auth.signup", lang)],
                horizontal=True,
                label_visibility="collapsed",
                key="auth_mode_radio",
            )
            st.session_state.auth_mode = "signup" if mode_toggle == t("auth.signup", lang) else "login"

            if st.session_state.auth_mode == "login":
                with st.form("login_form"):
                    username = st.text_input(t("auth.username", lang))
                    password = st.text_input(t("auth.password", lang), type="password")
                    submitted = st.form_submit_button(
                        t("auth.login", lang), use_container_width=True, type="primary"
                    )
                    if submitted:
                        ok, msg, user = login(username, password)
                        if ok:
                            set_logged_in(username.strip().lower(), user)
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
            else:
                with st.form("signup_form"):
                    username = st.text_input(
                        t("auth.username", lang),
                        help="3+ characters, letters/numbers/_/-"
                    )
                    email = st.text_input(t("auth.email", lang) + " (optional)")
                    password = st.text_input(
                        t("auth.password", lang), type="password",
                        help="6+ characters"
                    )
                    submitted = st.form_submit_button(
                        t("auth.signup", lang), use_container_width=True, type="primary"
                    )
                    if submitted:
                        ok, msg = signup(username, password, email)
                        if ok:
                            _, _, user = login(username, password)
                            set_logged_in(username.strip().lower(), user)
                            if email.strip():
                                send_welcome_email(email.strip(), username.strip(), "patient")
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

        with col2:
            st.markdown(f"#### {t('auth.or', lang)}")

            if google_oauth_available():
                # Handle callback first
                google_data = handle_google_callback()
                if google_data:
                    ok, msg, user = login_with_google(
                        google_data["email"],
                        google_data.get("name", ""),
                        google_data.get("sub", ""),
                    )
                    if ok:
                        username = f"google:{google_data['email'].lower()}"
                        set_logged_in(username, user)
                        st.success(msg)
                        st.rerun()

                if st.button(
                    f"🔑 {t('auth.google', lang)}",
                    use_container_width=True, key="google_login_btn"
                ):
                    trigger_google_login()
            else:
                st.caption(
                    "Google OAuth is available when deployed to Streamlit Cloud "
                    "with `auth` configured in secrets.toml. "
                    "Use username + password for now."
                )
                if st.button(
                    f"🔑 {t('auth.google', lang)} (demo)",
                    use_container_width=True, key="google_demo_btn",
                    help="Demo mode: signs in a placeholder Google account"
                ):
                    demo_email = f"demo{random.randint(1000, 9999)}@example.com"
                    ok, msg, user = login_with_google(demo_email, "Demo User")
                    if ok:
                        username = f"google:{demo_email}"
                        set_logged_in(username, user)
                        st.success(msg)
                        st.rerun()

    with tab_family:
        st.markdown(f"#### {t('auth.family_invite', lang)}")
        st.caption(
            "Family members: paste the 8-character code from your invite email. "
            "You do not need to create an account."
        )
        code_input = st.text_input(t("auth.invite_code", lang), max_chars=8)
        if st.button(t("auth.join_family", lang), type="primary"):
            if code_input.strip():
                invite = validate_invite_code(code_input)
                if invite:
                    consume_invite_code(code_input)
                    st.session_state.family_viewer = {
                        "code": code_input.strip().upper(),
                        "patient_username": invite["patient_username"],
                        "family_name": invite["family_name"],
                        "relationship": invite["relationship"],
                    }
                    # Load the patient's profile for read-only view
                    patient_profile = get_user_profile(invite["patient_username"])
                    if patient_profile:
                        st.session_state.viewing_patient_profile = patient_profile
                    st.success(f"Welcome, {invite['family_name']}!")
                    st.rerun()
                else:
                    st.error("Invalid invite code. Check your email.")


# ==========================================================
# ONBOARDING (after auth)
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
        default_name = user.get("display_name", current_username() or "") if user else ""
        default_email = user.get("email", "") if user else ""

        name = st.text_input(t("onboard.your_name", lang), value=default_name)
        email = st.text_input(t("auth.email", lang), value=default_email)
        language = st.selectbox(
            t("onboard.language", lang),
            list(LANGUAGES.keys()),
            help="All app text, voice output, and phrases will use this language."
        )
        hand = st.radio(
            "Which hand do you write with?",
            ["Right", "Left"], horizontal=True
        )

        submitted = st.form_submit_button(
            t("onboard.start_app", lang),
            use_container_width=True, type="primary"
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
                update_user_profile(current_username(), profile)
                if email.strip():
                    send_welcome_email(email.strip(), name.strip(), "patient")
                st.rerun()


# ==========================================================
# ASSESSMENT
# ==========================================================
def render_assessment():
    lang = get_lang()
    st.markdown(f"## {TR('assess.title') if t('assess.title', lang) != 'assess.title' else 'Quick aphasia assessment'}")
    st.caption("8 questions, 5 minutes. Helps us personalise everything.")

    with st.form("assessment_form"):
        responses = {}
        for task in ASSESSMENT_TASKS:
            st.markdown(f"**{task['prompt']}**")
            option_labels = [opt[0] for opt in task["options"]]
            choice = st.radio(
                "Select one:",
                option_labels,
                key=f"ass_{task['id']}",
                label_visibility="collapsed",
            )
            score = next(opt[1] for opt in task["options"] if opt[0] == choice)
            responses[task["id"]] = score
            st.markdown("---")

        if st.form_submit_button(
            t("btn.submit", lang), use_container_width=True, type="primary"
        ):
            aph_type, severity = classify_aphasia(responses)
            st.session_state.aphasia_type = aph_type
            st.session_state.severity = severity
            st.session_state.severity_history.append(
                (datetime.now().isoformat(), severity)
            )
            st.session_state.assessment_complete = True
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

    if st.button(t("btn.continue", lang) + " →", use_container_width=True, type="primary"):
        st.rerun()


# ==========================================================
# COMMUNICATION MODE (multilingual + bug fixed)
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
            t("comm.complete", lang) + " →",
            use_container_width=True, type="primary"
        )

    # FIXED predictive button — just speaks, doesn't overwrite widget state
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

    # Family-name suggestions
    if fragment and st.session_state.family_members:
        family_sugg = suggest_family_name_phrases(fragment, st.session_state.family_members)
        if family_sugg:
            st.caption(f"👪 {t('comm.family_suggestions', lang)}")
            for i, sugg in enumerate(family_sugg):
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f'<div class="phrase-card">{sugg}</div>', unsafe_allow_html=True)
                with c2:
                    if st.button("🔊", key=f"famsug_{i}", use_container_width=True):
                        speak(sugg)
                        award_xp(XP_REWARDS["communication_sent"])
                        notify_family(f'said "{sugg}"')

    # Main AI completion
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
                    key=f"speak_{i}", use_container_width=True
                ):
                    speak(sentence)
                    st.session_state.communicated_today.append({
                        "date": datetime.now().isoformat(), "sentence": sentence,
                    })
                    st.session_state.context_history.append(sentence)
                    award_xp(XP_REWARDS["communication_sent"])
                    concern = detect_crisis(sentence)
                    if concern:
                        notify_family(concern, is_concern=True)
                        st.warning(f"⚠️ Family alerted: {concern}")
                    else:
                        notify_family(f'said "{sentence}"')

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
                        unsafe_allow_html=True
                    )
                with c2:
                    if st.button("🔊", key=f"ph_{category}_{i}", use_container_width=True):
                        speak(display_phrase)
                        st.session_state.communicated_today.append({
                            "date": datetime.now().isoformat(), "sentence": display_phrase,
                        })
                        award_xp(XP_REWARDS["communication_sent"])
                        concern = detect_crisis(display_phrase)
                        if concern:
                            notify_family(concern, is_concern=True)
                            st.warning(f"⚠️ {concern}")
                        else:
                            notify_family(f'said "{display_phrase}"')


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

    if (st.session_state.current_exercise is None or
            st.session_state.current_exercise.get("type") != "word_retrieval"):
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
    if (st.session_state.current_exercise is None or
            st.session_state.current_exercise.get("type") != "sentence_building"):
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

    if (st.session_state.current_exercise is None or
            st.session_state.current_exercise.get("type") != "cloze"):
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
        "English": [{"text": "James ate lunch. He was hungry.", "q": "Did James eat lunch?",
                     "opts": ["Yes", "No"], "ans": "Yes"}],
        "Spanish": [{"text": "Juan comió. Tenía hambre.", "q": "¿Juan comió?",
                     "opts": ["Sí", "No"], "ans": "Sí"}],
        "French": [{"text": "Pierre a mangé. Il avait faim.", "q": "Pierre a mangé?",
                    "opts": ["Oui", "Non"], "ans": "Oui"}],
        "Portuguese": [{"text": "João comeu. Ele estava com fome.", "q": "João comeu?",
                        "opts": ["Sim", "Não"], "ans": "Sim"}],
    }
    pool = passages.get(lang, passages["English"])

    if (st.session_state.current_exercise is None or
            st.session_state.current_exercise.get("type") != "reading"):
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
    if (st.session_state.current_exercise is None or
            st.session_state.current_exercise.get("type") != "repetition"):
        st.session_state.current_exercise = {
            "type": "repetition", "word": random.choice(words),
        }
    ex = st.session_state.current_exercise
    word = ex["word"]
    if st.button(f"🔊 {t('btn.play', lang)}", type="primary"):
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
# GAMES — delegates to games.py
# ==========================================================
def render_games():
    lang = get_lang()
    st.markdown(f"## 🎮 {t('games.title', lang)}")
    st.caption(t("games.subtitle", lang))

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
                    key=f"game_{g['id']}", use_container_width=True
                ):
                    st.session_state.game_state = {"id": g["id"]}
                    st.rerun()
    else:
        game_id = st.session_state.game_state["id"]
        play_game(game_id, lang, award_xp, notify_family)
        st.markdown("---")
        if st.button(t("btn.close", lang)):
            # Clear per-game state keys
            for key in list(st.session_state.keys()):
                if key in ("picmatch", "cat_sort", "puzzle", "first_letter", "story"):
                    del st.session_state[key]
            st.session_state.game_state = None
            st.rerun()


# ==========================================================
# FAMILY MANAGEMENT (patient side)
# ==========================================================
def render_family_management():
    lang = get_lang()
    st.markdown(f"## 👪 {t('family.title', lang)}")
    st.caption("Add family members. They get an invite code by email — no account needed.")

    with st.expander(f"➕ {t('family.add_member', lang)}",
                     expanded=(len(st.session_state.family_members) == 0)):
        with st.form("add_fam"):
            c1, c2 = st.columns(2)
            with c1:
                fname = st.text_input(t("family.name", lang), placeholder="e.g. Samuel")
                frel = st.selectbox(t("family.relationship", lang), RELATIONSHIPS)
            with c2:
                femail = st.text_input("Email (required for invite)")
                fphone = st.text_input("Phone (optional)")

            if st.form_submit_button(t("btn.add", lang), type="primary"):
                if not fname.strip():
                    st.error("Please enter a name.")
                elif not femail.strip():
                    st.error("Email is required so we can send the invite code.")
                else:
                    # Create the invite code
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
                        "added": datetime.now().isoformat(),
                    })

                    # Email the invite
                    profile = st.session_state.profile
                    dashboard_url = "https://speakagain.streamlit.app"
                    ok, msg = send_family_invite(
                        family_email=femail.strip(),
                        family_name=fname.strip(),
                        patient_name=profile["name"],
                        relationship=frel,
                        dashboard_url=dashboard_url,
                        invite_code=code,
                    )
                    if ok:
                        st.success(f"✅ Added {fname} and emailed invite code: **{code}**")
                    else:
                        st.warning(
                            f"Added {fname}. Email send failed ({msg}). "
                            f"Share this code manually: **{code}**"
                        )
                    st.rerun()

    if not st.session_state.family_members:
        st.info("No family members added yet.")
        return

    st.markdown("### Your family")
    for i, m in enumerate(st.session_state.family_members):
        c1, c2 = st.columns([5, 1])
        with c1:
            code_line = ""
            if m.get("invite_code"):
                code_line = f" · code <code>{m['invite_code']}</code>"
            st.markdown(f"""
            <div class="family-card">
            <strong>{m['name']}</strong> ({m['relationship']})
            · {m.get('email', '')}{code_line}
            </div>
            """, unsafe_allow_html=True)
        with c2:
            if st.button(t("btn.remove", lang), key=f"rm_{i}", use_container_width=True):
                st.session_state.family_members.pop(i)
                st.rerun()


# ==========================================================
# FAMILY DASHBOARD (family-member view)
# ==========================================================
def render_family_dashboard():
    lang = get_lang()
    st.markdown(f"## 📡 {t('nav.dashboard', lang)}")

    # If accessed as family viewer via invite code
    if st.session_state.family_viewer:
        viewer = st.session_state.family_viewer
        patient_profile = st.session_state.get("viewing_patient_profile") or {}
        patient_name = patient_profile.get("name", viewer["patient_username"])

        st.markdown(f"""
        <div class="hero">
          <h1>Viewing {patient_name}'s dashboard</h1>
          <p>Signed in as family ({viewer['relationship']}) — {viewer['family_name']}</p>
        </div>
        """, unsafe_allow_html=True)

        st.info(
            "This is a read-only view. You only see the latest 50 events and current "
            "progress. No historical data beyond that is shown."
        )

        # In v2.1 family viewing shows data from the current session. In v3 this will
        # cross sessions via Supabase.
    else:
        profile = st.session_state.profile
        if not profile:
            st.info("Profile not set up yet.")
            return
        patient_name = profile["name"]
        st.markdown(f"### Live activity — {patient_name}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Phrases today", len(st.session_state.communicated_today))
    c2.metric("Exercises today", get_today_stats()[0])
    c3.metric("Streak", f"{st.session_state.streak_days}d")
    c4.metric("Level", get_level(st.session_state.xp)["level"])

    current_lvl = get_level(st.session_state.xp)
    next_lvl = get_next_level(st.session_state.xp)
    progress_pct = progress_to_next_level(st.session_state.xp)

    st.markdown(f"**{current_lvl['badge']} {current_lvl['name']}** · {st.session_state.xp} XP")
    if next_lvl:
        st.markdown(f"""
        <div class="xp-bar"><div class="xp-fill" style="width: {progress_pct*100}%"></div></div>
        <small>{int(progress_pct*100)}% to {next_lvl['name']}</small>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📻 Recent activity")
    if not st.session_state.activity_feed:
        st.info("No activity yet.")
    else:
        for item in st.session_state.activity_feed[:20]:
            time_str = datetime.fromisoformat(item["time"]).strftime("%I:%M %p")
            border_color = "#A32D2D" if item.get("concern") else "#2B6CB0"
            st.markdown(f"""
            <div class="activity-item" style="border-left-color: {border_color};">
            {item['action']} <span class="activity-time"> · {time_str}</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Recovered words")
    if st.session_state.recovered_words:
        st.markdown(" · ".join(f"**{w}**" for w in sorted(st.session_state.recovered_words)))
    else:
        st.caption("Words will appear here as they are recovered through exercises.")


# ==========================================================
# PROGRESS
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
        today = datetime.now().date()
        start = today - timedelta(days=29)
        full = pd.DataFrame({"day": pd.date_range(start, today).date})
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
# CAREGIVER
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
                    notify_family(f"emotional state: {e['label']}", is_concern=True)

    st.markdown("---")
    st.markdown("### Send daily summary")
    if st.session_state.family_members:
        for m in st.session_state.family_members:
            if m.get("email"):
                if st.button(
                    f"📧 Send to {m['name']} ({m['email']})",
                    key=f"send_{m['email']}", use_container_width=True
                ):
                    completed, _, _ = get_today_stats()
                    today_em = [e for e in st.session_state.emotion_log
                                if e["date"][:10] == datetime.now().date().isoformat()[:10]]
                    emotion_txt = (
                        f"{today_em[-1]['label']} ({today_em[-1]['emoji']})"
                        if today_em else "Not logged"
                    )
                    flags = [detect_crisis(x["sentence"])
                             for x in st.session_state.communicated_today
                             if detect_crisis(x["sentence"])]
                    ok, msg = send_daily_summary(
                        caregiver_email=m["email"], caregiver_name=m["name"],
                        patient_name=profile["name"],
                        phrases_communicated=len(st.session_state.communicated_today),
                        exercises_completed=completed,
                        exercises_total=st.session_state.daily_target,
                        streak_days=st.session_state.streak_days,
                        xp_earned=st.session_state.xp,
                        level_name=get_level(st.session_state.xp)["name"],
                        emotion_trend=emotion_txt, concerning_flags=flags,
                    )
                    if ok:
                        st.success(f"✅ Sent to {m['email']}")
                    else:
                        st.error(f"Failed: {msg}")
    else:
        st.info("Add family members first (Family tab).")


# ==========================================================
# SETTINGS
# ==========================================================
def render_settings():
    lang = get_lang()
    profile = st.session_state.profile
    user = current_user()

    st.markdown(f"## ⚙️ {t('nav.settings', lang)}")

    if user:
        method = user.get("auth_method", "password")
        email_txt = user.get("email", current_username())
        st.markdown(f"**Signed in as:** {email_txt} ({method})")
        if st.button(f"🚪 {t('nav.logout', lang)}", type="secondary"):
            logout()
            st.rerun()
        st.markdown("---")

    if profile:
        st.markdown(f"### {t('settings.profile', lang)}")
        for k, v in profile.items():
            if v:
                st.markdown(f"**{k.replace('_', ' ').title()}:** {v}")

        new_lang = st.selectbox(
            t("settings.change_lang", lang),
            list(LANGUAGES.keys()),
            index=list(LANGUAGES.keys()).index(profile.get("language", "English")),
        )
        if new_lang != profile.get("language"):
            if st.button(t("btn.save", lang)):
                st.session_state.profile["language"] = new_lang
                update_user_profile(current_username(), st.session_state.profile)
                st.success(f"Language changed to {new_lang}")
                st.rerun()

    st.markdown("---")
    st.session_state.daily_target = st.slider(
        t("settings.daily_target", lang), 1, 20, st.session_state.daily_target,
    )

    st.markdown("---")
    if st.button("Start reassessment"):
        st.session_state.assessment_complete = False
        st.rerun()

    st.markdown("---")
    st.markdown("### About SpeakAgain v2.1")
    st.markdown(
        "**Samuel Oluwakoya** · Lagos, Nigeria\n\n"
        "- Contact: **soluwakoyat@gmail.com** · **samueloluwakoyat@gmail.com**\n"
        "- GitHub: github.com/samexdgs\n"
        "Project #6 in the Neurological Rehabilitation AI Series.\n\n"
        "*Not a medical device. Does not replace professional speech therapy.*"
    )


# ==========================================================
# MAIN ROUTER
# ==========================================================
def main():
    lang = get_lang()

    with st.sidebar:
        st.markdown("# 💬 SpeakAgain v2.1")

        # Not signed in — just show the app name and version
        if not is_authenticated() and not st.session_state.family_viewer:
            st.caption("Sign in or join via invite →")
            st.markdown("---")
            st.caption(
                "v2.1 · Samuel Oluwakoya\n\n"
                "soluwakoyat@gmail.com\n\n"
                "samueloluwakoyat@gmail.com"
            )
            # Route to auth
            render_auth()
            return

        # Family-viewer mode (no account)
        if st.session_state.family_viewer:
            viewer = st.session_state.family_viewer
            st.caption(f"👪 Family view: {viewer['family_name']} ({viewer['relationship']})")
            st.markdown("---")
            if st.button(f"🚪 {t('nav.logout', lang)}"):
                logout()
                st.rerun()
            render_family_dashboard()
            return

        # Signed-in patient/caregiver
        user = current_user()
        st.caption(f"🔐 {current_username()}")

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
                t("nav.settings", lang),  # just a non-empty label
                list(page_map.keys()),
                label_visibility="collapsed",
            )
            page = page_map[page_label]
        else:
            page = None

        st.markdown("---")
        if st.button(f"🚪 {t('nav.logout', lang)}"):
            logout()
            st.rerun()
        st.caption(
            "soluwakoyat@gmail.com\n\n"
            "samueloluwakoyat@gmail.com"
        )

    # Main body routing
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
