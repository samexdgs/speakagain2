"""
brevo_mailer.py — SpeakAgain v2.0
-----------------------------------
Email notifications via Brevo REST API.

v2.0 additions:
- Real-time activity feed emails to family members
- Family dashboard access link invites
- Weekly progress digests
- Milestone celebrations
- Gamification achievement emails
"""

import os
import requests
import streamlit as st
from datetime import datetime
from typing import Optional

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"
DEFAULT_SENDER_NAME = "SpeakAgain — Samuel Oluwakoya"
DEFAULT_SENDER_EMAIL = "Samuel@bloomgatelaw.com"


def _get_api_key() -> Optional[str]:
    try:
        if "BREVO_API_KEY" in st.secrets:
            return st.secrets["BREVO_API_KEY"]
    except Exception:
        pass
    return os.environ.get("BREVO_API_KEY")


def send_email(
    to_email: str,
    to_name: str,
    subject: str,
    html_content: str,
    sender_email: str = DEFAULT_SENDER_EMAIL,
    sender_name: str = DEFAULT_SENDER_NAME,
    reply_to: Optional[str] = None,
) -> tuple[bool, str]:
    api_key = _get_api_key()
    if not api_key:
        return False, "Brevo API key not configured."

    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json",
    }
    payload = {
        "sender": {"name": sender_name, "email": sender_email},
        "to": [{"email": to_email, "name": to_name}],
        "subject": subject,
        "htmlContent": html_content,
    }
    if reply_to:
        payload["replyTo"] = {"email": reply_to}

    try:
        r = requests.post(BREVO_API_URL, json=payload, headers=headers, timeout=20)
        if r.status_code in (200, 201):
            return True, f"Email sent to {to_email}"
        try:
            err = r.json()
            msg = err.get("message") or err.get("code") or str(err)
        except Exception:
            msg = r.text[:300]
        return False, f"Brevo error ({r.status_code}): {msg}"
    except requests.exceptions.Timeout:
        return False, "Email request timed out."
    except Exception as e:
        return False, f"Email send failed: {str(e)[:200]}"


BASE_STYLE = """
<style>
body { font-family: -apple-system, 'Segoe UI', Roboto, sans-serif; background: #F5F7FA; margin: 0; padding: 20px; }
.wrap { max-width: 580px; margin: 0 auto; background: #ffffff; border-radius: 14px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.06); }
.header { background: #1A3A5C; color: white; padding: 26px 30px; }
.header h1 { margin: 0; font-size: 23px; font-weight: 500; }
.header .sub { font-size: 13px; opacity: 0.85; margin-top: 4px; }
.body { padding: 28px 30px; color: #2C2C2A; line-height: 1.65; font-size: 15px; }
.card { background: #EBF4FF; border-left: 3px solid #2B6CB0; padding: 14px 18px; border-radius: 8px; margin: 14px 0; }
.metric-box { display: inline-block; background: #F1EFE8; padding: 10px 16px; border-radius: 8px; margin: 4px 6px 4px 0; font-size: 13px; }
.metric-box strong { display: block; font-size: 20px; color: #1A3A5C; font-weight: 500; }
.footer { background: #F1EFE8; padding: 16px 30px; font-size: 12px; color: #5F5E5A; text-align: center; }
.alert { background: #FCEBEB; border-left: 3px solid #E24B4A; color: #791F1F; padding: 12px 16px; border-radius: 8px; margin: 14px 0; }
.good { background: #EAF3DE; border-left: 3px solid #639922; color: #27500A; padding: 12px 16px; border-radius: 8px; margin: 14px 0; }
.cta { display: inline-block; background: #2B6CB0; color: white; padding: 10px 22px; border-radius: 8px; text-decoration: none; margin-top: 10px; font-weight: 500; }
.activity-item { padding: 10px 0; border-bottom: 0.5px solid #E0E0E0; font-size: 14px; }
.activity-item:last-child { border-bottom: none; }
.activity-time { color: #888; font-size: 12px; margin-left: 10px; }
</style>
"""


def send_realtime_activity(
    family_email: str,
    family_name: str,
    patient_name: str,
    activity: str,
    activity_detail: str = "",
    is_concern: bool = False,
    dashboard_url: str = "",
) -> tuple[bool, str]:
    """Send a real-time notification when patient does something noteworthy."""
    time_str = datetime.now().strftime("%I:%M %p")

    style_block = "alert" if is_concern else "card"
    subject_prefix = "⚠️" if is_concern else "💬"

    dashboard_btn = ""
    if dashboard_url:
        dashboard_btn = f'<a href="{dashboard_url}" class="cta">View live dashboard</a>'

    html = f"""{BASE_STYLE}
<div class="wrap">
  <div class="header" style="background: {'#A32D2D' if is_concern else '#1A3A5C'};">
    <h1>{subject_prefix} {patient_name} just {activity}</h1>
    <div class="sub">{time_str}</div>
  </div>
  <div class="body">
    <p>Hello {family_name},</p>
    <div class="{style_block}">
      <strong>{patient_name}:</strong> {activity_detail or activity}
    </div>
    <p style="margin-top: 16px; font-size: 14px; color: #5F5E5A;">
      {dashboard_btn}
    </p>
  </div>
  <div class="footer">
    SpeakAgain v2.0 — Family real-time updates<br>
    Samuel Oluwakoya · Samuel@bloomgatelaw.com
  </div>
</div>"""
    return send_email(
        to_email=family_email,
        to_name=family_name,
        subject=f"{subject_prefix} {patient_name}: {activity[:60]}",
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
    dashboard_url: str = "",
) -> tuple[bool, str]:
    today = datetime.now().strftime("%A, %d %B %Y")

    flags_html = ""
    if concerning_flags:
        flags_html = '<div class="alert"><strong>Please check in:</strong><br>' + \
                     "<br>".join(f"• {f}" for f in concerning_flags) + "</div>"
    else:
        flags_html = '<div class="good">No concerns today.</div>'

    cta = f'<a href="{dashboard_url}" class="cta">Open live dashboard</a>' if dashboard_url else ""

    html = f"""{BASE_STYLE}
<div class="wrap">
  <div class="header">
    <h1>Daily update — {patient_name}</h1>
    <div class="sub">{today}</div>
  </div>
  <div class="body">
    <p>Hello {caregiver_name},</p>
    <p>Here is today's summary for {patient_name}.</p>
    <div>
      <div class="metric-box"><strong>{phrases_communicated}</strong>phrases said</div>
      <div class="metric-box"><strong>{exercises_completed}/{exercises_total}</strong>exercises</div>
      <div class="metric-box"><strong>{streak_days}</strong>day streak</div>
      <div class="metric-box"><strong>+{xp_earned}</strong>XP earned</div>
    </div>
    <div class="card">
      <strong>Level:</strong> {level_name}<br>
      <strong>Emotional state:</strong> {emotion_trend}
    </div>
    {flags_html}
    <p style="margin-top: 16px;">{cta}</p>
  </div>
  <div class="footer">
    SpeakAgain v2.0 — AI aphasia rehabilitation<br>
    Samuel Oluwakoya · Lagos, Nigeria · Samuel@bloomgatelaw.com
  </div>
</div>"""
    return send_email(
        to_email=caregiver_email,
        to_name=caregiver_name,
        subject=f"{patient_name}'s daily update — {phrases_communicated} phrases, +{xp_earned} XP",
        html_content=html,
    )


def send_milestone_email(
    recipient_email: str,
    recipient_name: str,
    patient_name: str,
    milestone: str,
    old_score: float,
    new_score: float,
    badge: str = "🎉",
) -> tuple[bool, str]:
    html = f"""{BASE_STYLE}
<div class="wrap">
  <div class="header" style="background: #27500A;">
    <h1>{badge} Milestone reached</h1>
    <div class="sub">{patient_name}</div>
  </div>
  <div class="body">
    <p>Hello {recipient_name},</p>
    <p>Wonderful news. {patient_name} just reached a meaningful milestone:</p>
    <div class="good"><strong>{milestone}</strong></div>
    <div>
      <div class="metric-box"><strong>{old_score:.1f}</strong>before</div>
      <div class="metric-box"><strong>{new_score:.1f}</strong>now</div>
      <div class="metric-box"><strong>+{new_score - old_score:.1f}</strong>gain</div>
    </div>
    <p style="margin-top: 16px;">This progress comes from consistent practice. Thank you for supporting {patient_name}.</p>
  </div>
  <div class="footer">
    SpeakAgain v2.0<br>Samuel@bloomgatelaw.com
  </div>
</div>"""
    return send_email(
        to_email=recipient_email,
        to_name=recipient_name,
        subject=f"{badge} {patient_name}: {milestone}",
        html_content=html,
    )


def send_family_invite(
    family_email: str,
    family_name: str,
    patient_name: str,
    relationship: str,
    dashboard_url: str,
    invite_code: str,
) -> tuple[bool, str]:
    html = f"""{BASE_STYLE}
<div class="wrap">
  <div class="header"><h1>You're invited to {patient_name}'s family dashboard</h1>
    <div class="sub">A window into their rehabilitation journey</div>
  </div>
  <div class="body">
    <p>Hello {family_name},</p>
    <p>{patient_name} has added you as a family member on SpeakAgain — an app that helps
    stroke survivors with aphasia communicate and recover their speech.</p>
    <p>As their {relationship}, you'll be able to:</p>
    <ul>
      <li>See daily progress and word recovery in real time</li>
      <li>Receive alerts when {patient_name} needs you</li>
      <li>Celebrate milestones together</li>
      <li>Add family-specific phrases (like your children's names)</li>
    </ul>
    <div class="card">
      <strong>Your invite code:</strong> <code>{invite_code}</code>
    </div>
    <p><a href="{dashboard_url}" class="cta">Open dashboard</a></p>
    <p style="margin-top: 20px; font-size: 13px; color: #5F5E5A;">
      This dashboard is private to {patient_name}'s family. Please do not share this link.
    </p>
  </div>
  <div class="footer">
    SpeakAgain v2.0 — Family dashboard<br>
    Samuel Oluwakoya · Samuel@bloomgatelaw.com
  </div>
</div>"""
    return send_email(
        to_email=family_email,
        to_name=family_name,
        subject=f"👪 You're invited to {patient_name}'s family dashboard",
        html_content=html,
    )


def send_welcome_email(to_email: str, to_name: str, role: str = "patient") -> tuple[bool, str]:
    role_msg = (
        "You've taken a brave step. SpeakAgain is built to help you communicate today "
        "and rebuild your speech over time. Everything works at your own pace."
        if role == "patient"
        else "You're now connected. You'll receive updates and can check in on progress any time."
    )
    html = f"""{BASE_STYLE}
<div class="wrap">
  <div class="header"><h1>Welcome to SpeakAgain v2.0</h1>
    <div class="sub">Your rehabilitation journey starts here</div>
  </div>
  <div class="body">
    <p>Hello {to_name},</p>
    <p>{role_msg}</p>
    <div class="card">
      <strong>What happens next:</strong><br>
      Take the 5-minute assessment<br>
      Use Communication mode whenever you need to say something<br>
      Do one short exercise set per day — that is enough<br>
      Earn XP, unlock levels, celebrate your own progress
    </div>
  </div>
  <div class="footer">
    SpeakAgain v2.0 — Samuel@bloomgatelaw.com
  </div>
</div>"""
    return send_email(to_email, to_name, "Welcome to SpeakAgain v2.0", html)
