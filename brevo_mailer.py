"""
brevo_mailer.py — Transactional email via the Brevo API

User-facing email templates. The Brevo sender address is configured at the
API payload level only and is NEVER exposed in the email body or the app UI.

Emails sent by this module:
- send_family_invite: one-shot invite code to a family member
- send_crisis_alert: immediate alert to caregiver (pain, fall, etc.)
- send_milestone_email: celebration of patient achievement
- send_daily_summary: end-of-day caregiver digest

Design principles:
- Minimal, calm visual design (no "v2.0" or product branding noise)
- Only a generic product name ("SpeakAgain") in footers
- Never leak the sender address to the recipient
"""
import os
import requests
import streamlit as st
from datetime import datetime
from typing import Optional

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"

# Sender identity — configured server-side, never surfaced to the UI
_SENDER_NAME = "SpeakAgain"
_SENDER_EMAIL = os.environ.get("BREVO_SENDER_EMAIL", "Samuel@bloomgatelaw.com")


def _get_api_key() -> Optional[str]:
    """Retrieve Brevo API key from secrets or environment."""
    try:
        if "BREVO_API_KEY" in st.secrets:
            return st.secrets["BREVO_API_KEY"]
    except Exception:
        pass
    return os.environ.get("BREVO_API_KEY")


def _get_sender() -> dict:
    """Build the sender dict for the Brevo payload. Configured via secrets
    so deployments can override. Never shown to the end user."""
    try:
        if "BREVO_SENDER_EMAIL" in st.secrets:
            return {
                "name": _SENDER_NAME,
                "email": st.secrets["BREVO_SENDER_EMAIL"],
            }
    except Exception:
        pass
    return {"name": _SENDER_NAME, "email": _SENDER_EMAIL}


def _get_dashboard_url() -> str:
    """App's public URL. Used inside email templates as the dashboard link."""
    try:
        if "APP_URL" in st.secrets:
            return str(st.secrets["APP_URL"]).rstrip("/")
    except Exception:
        pass
    return os.environ.get("APP_URL", "https://speakagain.streamlit.app").rstrip("/")


def _send(
    to_email: str,
    to_name: str,
    subject: str,
    html_content: str,
) -> tuple[bool, str]:
    """Low-level Brevo send. Returns (ok, debug_message)."""
    api_key = _get_api_key()
    if not api_key:
        return False, "Email service not configured."

    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json",
    }
    payload = {
        "sender": _get_sender(),
        "to": [{"email": to_email, "name": to_name or to_email}],
        "subject": subject,
        "htmlContent": html_content,
    }
    try:
        r = requests.post(BREVO_API_URL, json=payload, headers=headers, timeout=20)
        if r.status_code in (200, 201):
            return True, "sent"
        try:
            err = r.json()
            msg = err.get("message") or err.get("code") or "unknown"
        except Exception:
            msg = r.text[:200]
        return False, f"Send failed ({r.status_code}): {msg}"
    except requests.exceptions.Timeout:
        return False, "Timeout."
    except Exception as e:
        return False, f"Send error: {str(e)[:120]}"


# ==========================================================
# HTML STYLING
# ==========================================================
_BASE_STYLE = """
<style>
body { font-family: -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
       background: #F5F7FA; margin: 0; padding: 20px; color: #2C2C2A; }
.wrap { max-width: 580px; margin: 0 auto; background: #ffffff;
        border-radius: 14px; overflow: hidden;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06); }
.header { padding: 26px 30px; color: white; }
.header h1 { margin: 0; font-size: 22px; font-weight: 500; }
.header .sub { font-size: 13px; opacity: 0.9; margin-top: 6px; }
.body { padding: 28px 30px; line-height: 1.65; font-size: 15px; }
.card { background: #EBF4FF; border-left: 3px solid #2B6CB0;
        padding: 14px 18px; border-radius: 8px; margin: 14px 0; }
.alert { background: #FCEBEB; border-left: 3px solid #E24B4A;
         color: #791F1F; padding: 14px 18px; border-radius: 8px; margin: 14px 0; }
.good { background: #EAF3DE; border-left: 3px solid #639922;
        color: #27500A; padding: 12px 16px; border-radius: 8px; margin: 14px 0; }
.metric { display: inline-block; background: #F1EFE8; padding: 10px 16px;
          border-radius: 8px; margin: 4px 6px 4px 0; font-size: 13px; }
.metric strong { display: block; font-size: 20px; color: #1A3A5C; font-weight: 500; }
.cta { display: inline-block; background: #2B6CB0; color: white !important;
       padding: 10px 22px; border-radius: 8px; text-decoration: none;
       margin-top: 10px; font-weight: 500; }
.code-box { background: #1A3A5C; color: #FFFFFF; font-family: monospace;
            font-size: 24px; letter-spacing: 3px; text-align: center;
            padding: 16px 12px; border-radius: 8px; margin: 18px 0; }
.footer { background: #F1EFE8; padding: 14px 30px;
          font-size: 11px; color: #5F5E5A; text-align: center; }
.footer a { color: #5F5E5A; }
</style>
"""


# ==========================================================
# EMAIL TEMPLATES
# ==========================================================
def send_family_invite(
    family_email: str,
    family_name: str,
    patient_name: str,
    relationship: str,
    invite_code: str,
) -> tuple[bool, str]:
    """Invite a family member to the read-only dashboard."""
    dashboard_url = _get_dashboard_url()
    html = f"""{_BASE_STYLE}
<div class="wrap">
  <div class="header" style="background: #1A3A5C;">
    <h1>👪 You're invited</h1>
    <div class="sub">{patient_name} has added you as family on SpeakAgain</div>
  </div>
  <div class="body">
    <p>Hello {family_name},</p>
    <p>As {patient_name}'s {relationship}, you can now see their
    rehabilitation progress in a read-only dashboard. You do not need to create
    an account. Simply paste the code below at the app's "family invite" screen.</p>
    <div class="code-box">{invite_code}</div>
    <p style="text-align: center; margin-top: 18px;">
      <a class="cta" href="{dashboard_url}">Open dashboard</a>
    </p>
    <p style="font-size: 13px; color: #5F5E5A; margin-top: 22px;">
      This code is private to your family. Please do not share it.
      It is valid for 24 hours from the time it was generated.
    </p>
  </div>
  <div class="footer">SpeakAgain · Aphasia rehabilitation companion</div>
</div>"""
    return _send(
        to_email=family_email,
        to_name=family_name,
        subject=f"You're invited to {patient_name}'s dashboard",
        html_content=html,
    )


def send_crisis_alert(
    recipient_email: str,
    recipient_name: str,
    patient_name: str,
    concern: str,
    detail: str = "",
) -> tuple[bool, str]:
    """Immediate alert when the patient signals pain, falling, etc.
    This is a CRITICAL alert and should be the only thing that pages family
    in real time."""
    dashboard_url = _get_dashboard_url()
    time_str = datetime.now().strftime("%I:%M %p")

    detail_block = f'<p style="margin-top: 8px;">"{detail}"</p>' if detail else ""

    html = f"""{_BASE_STYLE}
<div class="wrap">
  <div class="header" style="background: #A32D2D;">
    <h1>⚠️ {patient_name} needs attention</h1>
    <div class="sub">{time_str}</div>
  </div>
  <div class="body">
    <p>Hello {recipient_name},</p>
    <div class="alert">
      <strong>{concern}</strong>
      {detail_block}
    </div>
    <p>This is an automatic alert from {patient_name}'s app. Please check on them.</p>
    <p style="text-align: center;">
      <a class="cta" href="{dashboard_url}">Open dashboard</a>
    </p>
  </div>
  <div class="footer">SpeakAgain · Care alerts are sent only for pain, falls, and emergencies.</div>
</div>"""

    return _send(
        to_email=recipient_email,
        to_name=recipient_name,
        subject=f"⚠️ {patient_name} needs attention",
        html_content=html,
    )


def send_milestone_email(
    recipient_email: str,
    recipient_name: str,
    patient_name: str,
    milestone: str,
) -> tuple[bool, str]:
    """Celebrate a meaningful recovery milestone."""
    html = f"""{_BASE_STYLE}
<div class="wrap">
  <div class="header" style="background: #27500A;">
    <h1>🎉 Milestone reached</h1>
    <div class="sub">{patient_name}</div>
  </div>
  <div class="body">
    <p>Hello {recipient_name},</p>
    <p>Wonderful news. {patient_name} just reached a meaningful milestone:</p>
    <div class="good"><strong>{milestone}</strong></div>
    <p>Thank you for supporting them on this journey.</p>
  </div>
  <div class="footer">SpeakAgain</div>
</div>"""
    return _send(
        to_email=recipient_email,
        to_name=recipient_name,
        subject=f"🎉 {patient_name}: {milestone[:80]}",
        html_content=html,
    )


def send_daily_summary(
    caregiver_email: str,
    caregiver_name: str,
    patient_name: str,
    phrases_communicated: int,
    exercises_completed: int,
    exercises_total: int,
    streak_days: int,
    xp_earned: int,
    level_name: str,
    emotion_trend: str,
    concerning_flags: list[str],
) -> tuple[bool, str]:
    """Evening digest for the primary caregiver only (not routed to every family)."""
    today = datetime.now().strftime("%A, %d %B %Y")
    dashboard_url = _get_dashboard_url()

    if concerning_flags:
        flags_html = (
            '<div class="alert"><strong>Please check in:</strong><br>'
            + "<br>".join(f"• {f}" for f in concerning_flags)
            + "</div>"
        )
    else:
        flags_html = '<div class="good">No concerns today.</div>'

    html = f"""{_BASE_STYLE}
<div class="wrap">
  <div class="header" style="background: #1A3A5C;">
    <h1>Daily update — {patient_name}</h1>
    <div class="sub">{today}</div>
  </div>
  <div class="body">
    <p>Hello {caregiver_name},</p>
    <p>Here is today's summary for {patient_name}.</p>
    <div>
      <div class="metric"><strong>{phrases_communicated}</strong>phrases said</div>
      <div class="metric"><strong>{exercises_completed}/{exercises_total}</strong>exercises</div>
      <div class="metric"><strong>{streak_days}</strong>day streak</div>
      <div class="metric"><strong>+{xp_earned}</strong>XP earned</div>
    </div>
    <div class="card">
      <strong>Level:</strong> {level_name}<br>
      <strong>Emotional state:</strong> {emotion_trend}
    </div>
    {flags_html}
    <p style="text-align: center;">
      <a class="cta" href="{dashboard_url}">Open dashboard</a>
    </p>
  </div>
  <div class="footer">SpeakAgain · Daily digests are sent to the primary caregiver only.</div>
</div>"""
    return _send(
        to_email=caregiver_email,
        to_name=caregiver_name,
        subject=f"{patient_name}'s daily update",
        html_content=html,
    )


def send_welcome_email(to_email: str, to_name: str) -> tuple[bool, str]:
    """Sent once on first signup."""
    html = f"""{_BASE_STYLE}
<div class="wrap">
  <div class="header" style="background: #1A3A5C;">
    <h1>Welcome to SpeakAgain</h1>
    <div class="sub">Your rehabilitation journey starts here</div>
  </div>
  <div class="body">
    <p>Hello {to_name},</p>
    <p>You've taken a brave step. SpeakAgain is built to help you communicate today
    and rebuild your speech over time. Everything works at your own pace.</p>
    <div class="card">
      <strong>Getting started:</strong><br>
      Take the 5-minute assessment<br>
      Use Communication mode whenever you need to say something<br>
      Do one short exercise set per day — that is enough<br>
      Earn XP, unlock levels, celebrate your own progress
    </div>
  </div>
  <div class="footer">SpeakAgain</div>
</div>"""
    return _send(to_email, to_name, "Welcome to SpeakAgain", html)


# ==========================================================
# BACKWARDS-COMPAT SHIM
# The old name send_realtime_activity is still imported by older app.py code.
# In v2.2 we only route CRITICAL events to email (see send_crisis_alert).
# Non-critical activity goes to the shared patient_store dashboard, not email.
# ==========================================================
def send_realtime_activity(
    family_email: str,
    family_name: str,
    patient_name: str,
    activity: str,
    activity_detail: str = "",
    is_concern: bool = False,
) -> tuple[bool, str]:
    """Legacy shim. Only fires when is_concern=True. Otherwise silent."""
    if is_concern:
        return send_crisis_alert(
            recipient_email=family_email,
            recipient_name=family_name,
            patient_name=patient_name,
            concern=activity,
            detail=activity_detail,
        )
    # Non-critical events are NOT emailed in v2.2. They appear on dashboard.
    return True, "routed-to-dashboard"
