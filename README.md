# 💬 SpeakAgain — Multilingual AI Aphasia Rehabilitation

**Project #6 of 10** in the Neurological Rehabilitation AI Series by **Samuel Oluwakoya**.
A computer science graduate, foot drop patient, and independent AI health researcher based in Lagos, Nigeria, building open-source rehabilitation tools for stroke survivors.

**Contact:** soluwakoyat@gmail.com · samueloluwakoyat@gmail.com
**GitHub:** github.com/samexdgs

---

## What is SpeakAgain

SpeakAgain is a free web application that helps people with aphasia after stroke. It offers three things:

1. **Communication mode** — type any fragment, get three complete spoken sentences. Fully multilingual.
2. **Daily exercises + games** — graded word retrieval, sentence building, and five pictographic mini-games.
3. **Family dashboard** — a read-only live view for loved ones, with crisis alerts routed to email.

The platform is built for patients in low-resource settings. It works on any browser, stays usable on intermittent connectivity, and costs nothing to run.

---

## What's new in v2.2 — the important fixes

| Issue | Fix |
|---|---|
| Profile and assessment wiped on every login | Shared on-disk store keyed by username. Login restores everything: profile, assessment, XP, streak, recovered words, family list. Returning users land on Communication, not the assessment. |
| Family dashboard empty after invite login | Family viewers read from the shared store by patient username. They see real-time activity across sessions. |
| Family inbox spammed by every word | Only **crisis events** (pain, fall, can't breathe, dizzy) email every family member. Daily summaries go to **one primary caregiver** only. Everyday activity stays on the dashboard. |
| Google sign-in didn't work | Uses Streamlit's native `st.login()` (Streamlit ≥ 1.42). Auto-signs-in on OAuth return. |
| Hard-coded `speakagain.streamlit.app` in invite emails | Configurable via `APP_URL` in secrets. |
| `Samuel@bloomgatelaw.com` leaking into email bodies and app UI | Removed from every user-visible surface. Configured only at the Brevo API sender level via `BREVO_SENDER_EMAIL` in secrets. |
| Invite codes never expired | 24-hour TTL. Removing a family member revokes their codes. |

---

## Authentication model

Two patient pathways + one family pathway.

### For patients
- **Username + password** — PBKDF2-HMAC-SHA256, 200,000 iterations, 16-byte salt per user. Constant-time hash comparison to prevent timing attacks.
- **Sign in with Google** — Streamlit's native OpenID Connect (`st.login()`). The app auto-completes sign-in when the OAuth callback returns.

### For family members
- **Invite code only.** No account, no password. Each family member gets an 8-character code by email and pastes it into the "Family invite" tab. Codes expire after 24 hours if unused. Removing a family member invalidates their codes.

---

## How family notifications work (important)

This is often misunderstood. In v2.2 the rules are precise:

- **Every event** goes to the shared store. Family members see everything on the dashboard in real time.
- **Crisis events only** (pain, fall, can't breathe, dizzy, emergency, plus translations in every supported language) trigger an immediate email to **every** family member.
- **Milestones** (level-ups, assessment gains) email **only the primary caregiver** you mark in the Family tab.
- **Daily summaries** are manually sent from the Caregiver tab and go to the primary caregiver only.
- **Everyday activity** (phrases spoken, exercises completed, emotion check-ins below threshold) stays on the dashboard. Nobody gets spammed.

This design mirrors how you'd actually want a health app to behave: quiet until something needs attention.

---

## Deployment — Streamlit Cloud setup

### 1. Fork or push the code to a public GitHub repo

### 2. Create the Streamlit app
- Go to [share.streamlit.io](https://share.streamlit.io)
- "Create app" → paste the repo URL
- **Advanced settings → Python version: 3.11**
- Deploy. It takes about 90 seconds.

### 3. Paste secrets (App settings → Secrets)

```toml
# Brevo for email (crisis alerts + daily digests + family invites)
BREVO_API_KEY = "xkeysib-YOUR-KEY-HERE"
BREVO_SENDER_EMAIL = "Samuel@bloomgatelaw.com"   # the Brevo-verified sender

# The public URL of this app — used in invite emails
APP_URL = "https://your-app-name.streamlit.app"

# Optional: Claude for smart sentence suggestions (works without it)
ANTHROPIC_API_KEY = "sk-ant-api03-YOUR-KEY-HERE"

# Optional: Google sign-in
[auth]
redirect_uri    = "https://your-app-name.streamlit.app/oauth2callback"
cookie_secret   = "GENERATE-A-LONG-RANDOM-STRING-AT-LEAST-32-CHARS"
client_id       = "1234567890-xxxxx.apps.googleusercontent.com"
client_secret   = "GOCSPX-xxxxxxxxxxxxxxxxxxxxxxxx"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

---

## How to get the Google OAuth values

1. Go to [console.cloud.google.com](https://console.cloud.google.com/)
2. Create or select a project
3. **APIs & Services → OAuth consent screen** → fill in App name ("SpeakAgain") and support email
4. **APIs & Services → Credentials → Create Credentials → OAuth client ID**
   - Application type: **Web application**
   - **Authorised redirect URIs:** add `https://your-app-name.streamlit.app/oauth2callback`
     (the `/oauth2callback` path is handled by Streamlit — don't change it)
5. Copy **Client ID** and **Client Secret** into the `[auth]` block above.

Generate `cookie_secret` with `python -c "import secrets; print(secrets.token_urlsafe(32))"`.

---

## How to get the Brevo API key

1. Sign up at [brevo.com](https://brevo.com) (free tier: 300 emails/day)
2. **Settings → Senders, Domains & IPs** → verify your sender domain with SPF, DKIM, DMARC
3. **Settings → Senders** → verify the sender address (`Samuel@bloomgatelaw.com` or your own)
4. **Settings → API Keys → Generate a new API key** (starts with `xkeysib-`)
5. Paste into Streamlit secrets as `BREVO_API_KEY`

Without domain verification, emails land in spam. Without sender verification, they fail silently.

---

## How to get the Anthropic API key

This one only you can get. Nobody can hand you a key that works with your account — Anthropic issues keys to authenticated account holders only, and anyone offering a key in a chat has either scammed you or leaked their own credentials.

Steps:
1. Go to [console.anthropic.com](https://console.anthropic.com/)
2. Sign up, verify your email
3. Click your profile (top right) → **API Keys → Create Key**
4. Name it "SpeakAgain" → the key (`sk-ant-api03-...`) is shown **once** — copy it immediately
5. **Settings → Billing** → add $5 credits (lasts months at this app's volume)
6. Paste into Streamlit secrets as `ANTHROPIC_API_KEY`

The app works without this key — it falls back to rule-based multilingual sentence completion. The key just enables Claude for smarter AI suggestions.

---

## Architecture

```
speakagain_v2/
├── app.py              # Main router, all UI rendering, event dispatch
├── auth.py             # Signup/login, Google OIDC, invite-code lifecycle
├── patient_store.py    # Shared on-disk store keyed by username
├── clinical_data.py    # 9 languages, phrases, exercises, XP table
├── i18n.py             # 82 UI translation keys × 9 languages
├── games.py            # 5 playable mini-games with emoji visuals
├── ai_completion.py    # Claude API + offline rule fallback
├── brevo_mailer.py     # Crisis alerts, daily summaries, family invites
├── requirements.txt    # streamlit>=1.42, Authlib>=1.3.2, + standard deps
├── runtime.txt         # python-3.11
└── .streamlit/
    ├── config.toml
    └── secrets.toml.example
```

### Data flow

```
Patient action (say phrase, complete exercise, etc.)
    ↓
_record_activity() — single dispatch point
    ↓
┌──────────────────────┐     ┌───────────────────────┐
│ append_activity()    │     │ Crisis detected?      │
│ → shared store       │     │  Yes → send_crisis_   │
│ (dashboard visible)  │     │        alert() to all │
└──────────────────────┘     │  No  → dashboard only │
                             └───────────────────────┘
                                       ↓
                     (milestone? → send_milestone_email()
                      to primary caregiver only)
```

### Why a shared on-disk store

Streamlit's `session_state` is per browser session. Two browsers (a patient and their family member) cannot share it. The patient store writes JSON atomically to disk, keyed by patient username. The family dashboard reads by the username recorded in the invite code — so updates show up in the family view within one refresh.

When the filesystem is read-only (some cloud hosts), the store gracefully falls back to session state with a note that data won't persist. On Streamlit Community Cloud the container filesystem is writable within one session, which is enough for the dashboard sync to work.

For a production deployment at scale, the JSON store should be replaced with Supabase or Postgres; the `patient_store.py` interface is already structured so this swap is one module change. A v3.0 migration plan is documented in the companion manuscript.

---

## The 9 languages

| Language | Text | Voice | Predictive | Offline AI | Crisis keywords |
|---|---|---|---|---|---|
| English | ✓ | native | ✓ | ✓ | ✓ |
| Spanish | ✓ | native (es-ES) | ✓ | ✓ | ✓ |
| French | ✓ | native (fr-FR) | ✓ | ✓ | ✓ |
| Portuguese | ✓ | native (pt-BR) | ✓ | ✓ | ✓ |
| Arabic | ✓ | native | partial | partial | ✓ |
| Yoruba | ✓ | Nigerian English | partial | ✓ | ✓ |
| Igbo | ✓ | Nigerian English | partial | ✓ | ✓ |
| Hausa | ✓ | Nigerian English | partial | ✓ | ✓ |
| Pidgin | ✓ | Nigerian English | partial | ✓ | partial |

Google's gTTS does not yet ship native voices for Yoruba, Igbo, Hausa, or Pidgin. Nigerian-accented English is used as a linguistic bridge until v3 integrates a Nigerian-language TTS vendor.

---

## Security notes

- **PBKDF2-HMAC-SHA256** with 200,000 iterations for password hashing (will migrate to Argon2id in v3).
- **Constant-time** hash comparison (`secrets.compare_digest`) prevents timing attacks.
- **Invite codes** are generated from `secrets.token_urlsafe(9)` (~48 bits of entropy) and expire in 24 hours.
- **Removing a family member** automatically revokes all active invite codes bound to their email.
- **Username validation** (regex whitelist) and **atomic file writes** (`os.replace`) prevent directory traversal and partial-write corruption.
- **No credentials or sender addresses** are surfaced in the UI or in email bodies. Everything sensitive lives server-side.
- **Read-only dashboard** for family viewers — they cannot modify anything about the patient's account.

---

## Running locally

```bash
git clone https://github.com/samexdgs/speakagain.git
cd speakagain
pip install -r requirements.txt
streamlit run app.py
```

The first-run experience: create an account with username + password, complete the 5-minute assessment, add a family member with their email, check your Brevo logs to confirm the invite was sent, open a second browser, paste the invite code, watch the dashboard update when you say something in the first browser.

---

## Disclaimer

SpeakAgain is a research and accessibility tool. It has not been validated as a medical device and does not replace professional speech-language therapy. In a medical emergency, contact emergency services.

---

Built by **Samuel Oluwakoya** — Computer Science Graduate, Foot Drop Patient, AI Health Researcher
Lagos, Nigeria · soluwakoyat@gmail.com · samueloluwakoyat@gmail.com · github.com/samexdgs
