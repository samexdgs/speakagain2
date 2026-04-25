# 💬 SpeakAgain — Multilingual AI Aphasia Rehabilitation

**Project #6 in the Neurological Rehabilitation AI Series by **Samuel Oluwakoya**.
A computer science graduate, foot drop patient, and independent AI health researcher based in Lagos, Nigeria, building open-source rehabilitation tools for stroke survivors.

**Contact:** soluwakoyat@gmail.com
**GitHub:** github.com/samexdgs

---

## What is SpeakAgain

SpeakAgain is a free web application that helps people with aphasia after stroke. It offers three things:

1. **Communication mode** — type any fragment, get three complete spoken sentences. Fully multilingual.
2. **Daily exercises + games** — graded word retrieval, sentence building, and five pictographic mini-games.
3. **Family dashboard** — a read-only live view for loved ones, with crisis alerts routed to email.

The platform is built for patients in low-resource settings. It works on any browser, stays usable on intermittent connectivity, and costs nothing to run.

## How family notifications work (important)

This is often misunderstood. In v2.2 the rules are precise:

- **Every event** goes to the shared store. Family members see everything on the dashboard in real time.
- **Crisis events only** (pain, fall, can't breathe, dizzy, emergency, plus translations in every supported language) trigger an immediate email to **every** family member.
- **Milestones** (level-ups, assessment gains) email **only the primary caregiver** you mark in the Family tab.
- **Daily summaries** are manually sent from the Caregiver tab and go to the primary caregiver only.
- **Everyday activity** (phrases spoken, exercises completed, emotion check-ins below threshold) stays on the dashboard. Nobody gets spammed.



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

## Disclaimer

SpeakAgain is a research and accessibility tool. It has not been validated as a medical device and does not replace professional speech-language therapy. In a medical emergency, contact emergency services.

---

Built by **Samuel Oluwakoya Tobi** — Computer Science Graduate, Foot Drop Patient, AI Health Researcher
Lagos, Nigeria · soluwakoyat@gmail.com  github.com/samexdgs
