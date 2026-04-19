# 💬 SpeakAgain v2.1 — Multilingual AI Aphasia Rehabilitation Platform

**Project #6 of 10** in the Neurological Rehabilitation AI Series by **Samuel Oluwakoya**.
Computer science graduate, foot drop patient, independent AI health researcher based in Lagos, Nigeria. Building open-source AI rehabilitation tools for stroke survivors.

**Contact:** soluwakoyat@gmail.com · samueloluwakoyat@gmail.com
**GitHub:** github.com/samexdgs
**Live:** speakagain.streamlit.app

> *Samuel@bloomgatelaw.com is the Brevo verified sender address used for outbound alerts and daily digests only. Please use the personal addresses above for all correspondence about this project.*

---

## What's new in v2.1

| Feature | v1.0 | v2.0 | v2.1 |
|---|---|---|---|
| UI translation | Phrase bar only | Phrase bar + some menus | **Entire UI in chosen language** |
| Games playable | None | Partial placeholders | **5 complete games including picture match** |
| Pictures in word match | — | Text only | **Emoji visuals (64px)** |
| Authentication | None | Not required | **Username+password + Google OAuth** |
| Family access | Not supported | Simulated | **Invite-code only, no account required** |
| Languages | 5 Nigerian + English | 9 | 9 |
| Caregiver alerts | Email digest | Real-time per event | Real-time per event |

---

## Key v2.1 behaviours — responding to user feedback

### 1. The whole UI translates, not just phrases
Earlier versions translated the communication phrase library but left navigation, buttons, game names, and instructions in English. In v2.1 every piece of UI text routes through `i18n.t(key, language)`, which pulls from a central dictionary of 82 translation keys covering all 9 languages. Selecting Spanish, French, Portuguese, or Arabic now changes the entire interface. Nigerian languages (Yoruba, Igbo, Hausa, Pidgin) have the main navigation and category labels translated; exercise instructions fall back to English where native wording is pending professional review.

### 2. Games are real and playable
Five games are fully implemented in `games.py`:

- **Picture match** uses emoji visuals rendered at 64px as the pictographic anchor. The player sees four emoji cards and pairs each with its word (translated into the current language). Emoji are used because they render consistently everywhere without licence or network cost, and they survive across all 9 languages without retranslation.
- **Category sort** presents words and asks the player to sort them into Food / Animals / House / Nature categories, with categories translated.
- **Sentence puzzle** scrambles a target sentence and asks the player to click words in correct order to rebuild it.
- **First letter challenge** is a 60-second naming burst on a random letter.
- **Story builder** fills the missing word in each of four connected story sentences.

No game is marked "coming in version 3".

### 3. Authentication with Google OAuth or username/password
`auth.py` provides two pathways:

- **Username + password** — PBKDF2-SHA256 hashed with 100,000 iterations and a per-user salt. Credentials persist in `.users.json` or, when the filesystem is read-only, in session-state fallback.
- **Google OAuth** — uses Streamlit's built-in `st.login("google")` when the deployment is configured with a Google client in `secrets.toml`. When not configured, a demo mode is offered that signs in a placeholder account so the flow can be exercised locally.

Family members do *not* create accounts. When a patient adds a family member, an 8-character invite code is generated and emailed to the family member via Brevo. The family member pastes the code into the "Family invite" tab to open a read-only dashboard view of the patient's current session. This matches the requirement that "members retain only the key sent to them via email."

---

## The 9 languages

Each language has phrases, predictive words, voice output, and offline AI completion:

1. **English** (en-GB voice)
2. **Yorùbá** — native orthography for display, Nigerian-accented English voice
3. **Igbo** — same approach
4. **Hausa** — same approach
5. **Pidgin** — displayed in Pidgin, Nigerian-accented English voice
6. **Español** (es-ES voice)
7. **Français** (fr-FR voice)
8. **Português** (pt-BR voice)
9. **العربية** (ar voice)

Google's gTTS does not yet ship native voices for Yoruba, Igbo, Hausa, or Pidgin, so Nigerian-accented English is used as a linguistic bridge. Version 3 will integrate a Nigerian-language TTS vendor (for example Lelapa AI) for native voice output.

---

## Family member system

Patients add family members with name, relationship, and email. Once added:

**Auto-expansion of phrases:**
- "Call my son" becomes "Call my son Samuel"
- "I want to speak with my daughter" becomes "I want to speak with my daughter Grace"

**Contextual name suggestions:**
Typing "Sam" in the communication box produces: "Please call my son Samuel", "I want to speak with Samuel", "Tell Samuel I love him", "Where is Samuel?"

**Real-time notifications:**
Each communicated sentence, exercise completion, or crisis keyword triggers an email to every registered family member via Brevo.

**Invite-code dashboard:**
When a family member pastes their invite code, they see a read-only live view of the patient's recent activity, current level, streak, and recovered words. They do not create accounts and cannot edit anything.

---

## Gamification

| Level | Name | XP required | Badge |
|---|---|---|---|
| 1 | Starting the journey | 0 | 🌱 |
| 2 | Finding words | 100 | 🌿 |
| 3 | Building sentences | 300 | 🌳 |
| 4 | Speaking with confidence | 600 | 💬 |
| 5 | Voice rising | 1,000 | 📢 |
| 6 | Fluent again | 1,500 | ⭐ |
| 7 | Inspiring others | 2,200 | 🏆 |
| 8 | SpeakAgain Champion | 3,000 | 🥇 |

**XP rewards:** exercise correct +10; no-hint correct +15; first-time word recovered +20; communication sent +2; daily streak +5; weekly streak +50; monthly streak +250; milestone +100; perfect picture match +50; sentence puzzle +50; story builder +70.

---

## Running locally

```bash
git clone https://github.com/samexdgs/speakagain.git
cd speakagain
pip install -r requirements.txt
streamlit run app.py
```

## Deploying to Streamlit Cloud

**Python version is locked at first deploy.** Do this correctly the first time:

1. Push this folder to a public GitHub repo
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **Create app** and paste the repo URL
4. Click **Advanced settings**
5. Set **Python version: 3.11** (the default of 3.14 breaks some wheels)
6. In **Secrets**, paste:
```toml
BREVO_API_KEY = "xkeysib-your-key-here"
ANTHROPIC_API_KEY = "sk-ant-api03-your-key-here"

# Optional: Google OAuth via Streamlit's native auth
[auth]
redirect_uri = "https://your-app.streamlit.app/oauth2callback"
cookie_secret = "a-long-random-string"
client_id = "your-google-client-id.apps.googleusercontent.com"
client_secret = "your-google-client-secret"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```
7. Click **Deploy**

If you already deployed and it is stuck on Python 3.14, delete the app from the Manage app menu, then redeploy with Python 3.11 set in Advanced settings.

---

## Brevo setup (one-time, for email alerts)

1. Sign up at brevo.com (free tier: 300 emails/day)
2. Go to **Settings → Senders, Domains & IPs**
3. **Verify domain `bloomgatelaw.com`** by adding SPF, DKIM, and DMARC DNS records
4. **Verify sender `Samuel@bloomgatelaw.com`** (this address is used only as the Brevo sender for outbound alerts and daily digests)
5. **Settings → API Keys → Generate a new key** (starts with `xkeysib-`)
6. Paste into Streamlit secrets as `BREVO_API_KEY`

---

## Getting the Anthropic API key

I cannot issue you an API key, and nobody else can either — Anthropic issues keys only to authenticated account owners. If anyone hands you a key in a chat, it is either a scam or someone leaking their own credentials, both of which get the key revoked.

The real steps:

1. Go to **console.anthropic.com** and sign up with your email
2. Verify your email
3. Click your profile (top right) → **API Keys** → **Create Key**
4. Name it "SpeakAgain" and click **Create**
5. Copy the key shown on screen once — it starts with `sk-ant-api03-`
6. Add $5 of credits under Settings → Billing (this lasts months at this app's usage)
7. Paste into Streamlit secrets as `ANTHROPIC_API_KEY`

The app works without this key — it falls back to rule-based offline completion. The key just enables Claude's multilingual smart suggestions.

---

## Architecture

```
speakagain_v2/
├── app.py              # Main Streamlit router + UI
├── clinical_data.py    # 9 languages, phrases, exercises, XP table, gamification
├── i18n.py             # UI translation dictionary (82 keys × 9 languages)
├── auth.py             # Username/password + Google OAuth + invite codes
├── games.py            # 5 playable mini-games with emoji picture match
├── ai_completion.py    # Claude API + offline rule fallback (multilingual)
├── brevo_mailer.py     # Email templates for family alerts + digests
├── requirements.txt    # Unpinned versions for Python 3.11-3.14 compat
├── runtime.txt         # python-3.11
└── .streamlit/
    ├── config.toml
    └── secrets.toml.example
```

---

## The 10-app series

1. Drop Foot Management App — fdmapp.streamlit.app (LIVE)
2. Stroke Recovery Progress Tracker
3. Gait Quality Self-Assessment
4. Spasticity Severity Predictor
5. Hand Grip Rehabilitation Planner
6. **SpeakAgain — Aphasia Communication Aid v2.1 (THIS PROJECT)**
7. Falls Risk Predictor
8. Neurological Fatigue Manager
9. Caregiver Guidance System
10. Stroke Secondary Prevention Calculator

---

## Evidence base

- Kim et al., 2025 (JMIR mHealth) — VoiceAdapt RCT
- Braley et al., 2021 (Frontiers in Neurology) — Constant Therapy RCT
- Upton et al., 2024 — iTalkBetter adaptive anomia therapy
- Ericson et al., 2025 — systematic review of 39 self-administered interventions
- Brady et al., Cochrane 2016 — therapy intensity is the strongest predictor
- Breitenstein et al., 2017 (Lancet) — 10+ hours per week effective in chronic aphasia
- Akinyemi et al., 2021 (Nature Reviews Neurology) — African stroke burden
- Owolabi et al., 2023 (Lancet Neurology Commission) — pragmatic solutions
- Edwards et al., 2016 (BMJ Open) — gamification for health behaviour change

---

## Disclaimer

SpeakAgain is a research and accessibility tool. It has not been validated as a medical device and does not replace professional speech-language therapy. In a medical emergency, contact emergency services.

---

Built by **Samuel Oluwakoya** — Computer Science Graduate, Foot Drop Patient, AI Health Researcher
Lagos, Nigeria · soluwakoyat@gmail.com · samueloluwakoyat@gmail.com · github.com/samexdgs
