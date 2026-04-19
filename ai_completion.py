"""
ai_completion.py — SpeakAgain v2.0
-----------------------------------
Fragment-to-sentence completion with:
- Multilingual prompts (9 languages, AI responds in user's language)
- Family-name-aware completion ("call son" becomes "call my son Samuel")
- Offline rule-based fallback in every supported language
"""

import os
import json
import requests
import streamlit as st
from typing import Optional


def _get_claude_key() -> Optional[str]:
    try:
        if "ANTHROPIC_API_KEY" in st.secrets:
            return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        pass
    return os.environ.get("ANTHROPIC_API_KEY")


# Offline patterns per language — used when no internet / no API key
OFFLINE_PATTERNS = {
    "English": {
        ("hungry", "food", "eat"): [
            ("I am hungry and would like to eat", 0.85),
            ("Please give me some food", 0.78),
            ("When will the meal be ready?", 0.65),
        ],
        ("thirsty", "water", "drink"): [
            ("I am thirsty and would like some water", 0.88),
            ("Please bring me a drink", 0.80),
            ("Can I have a cup of water please?", 0.72),
        ],
        ("pain", "hurt", "ache"): [
            ("I am in pain and need help", 0.90),
            ("The pain is getting worse", 0.82),
            ("Please call the doctor about my pain", 0.75),
        ],
        ("tired", "sleep", "rest"): [
            ("I am tired and want to rest", 0.88),
            ("I would like to go to sleep now", 0.80),
        ],
        ("son",): [
            ("Please call my son", 0.85),
            ("I want to speak with my son", 0.80),
            ("Tell my son I love him", 0.72),
        ],
        ("daughter",): [
            ("Please call my daughter", 0.85),
            ("I want to speak with my daughter", 0.80),
            ("Tell my daughter I love her", 0.72),
        ],
        ("wife",): [
            ("Please call my wife", 0.85),
            ("I want to see my wife", 0.80),
            ("Tell my wife I miss her", 0.72),
        ],
    },
    "Spanish": {
        ("hambre", "comida", "comer"): [
            ("Tengo hambre y quiero comer", 0.85),
            ("Por favor, dame comida", 0.78),
        ],
        ("sed", "agua"): [
            ("Tengo sed y quiero agua", 0.88),
            ("Por favor, traeme agua", 0.80),
        ],
        ("dolor", "duele"): [
            ("Tengo dolor y necesito ayuda", 0.90),
            ("El dolor está empeorando", 0.82),
        ],
        ("hijo",): [
            ("Por favor, llame a mi hijo", 0.85),
            ("Quiero hablar con mi hijo", 0.80),
        ],
        ("hija",): [
            ("Por favor, llame a mi hija", 0.85),
            ("Quiero hablar con mi hija", 0.80),
        ],
    },
    "French": {
        ("faim", "manger"): [
            ("J'ai faim et je voudrais manger", 0.85),
            ("Apportez-moi à manger s'il vous plaît", 0.78),
        ],
        ("soif", "eau"): [
            ("J'ai soif et je voudrais de l'eau", 0.88),
        ],
        ("mal", "douleur"): [
            ("J'ai mal et j'ai besoin d'aide", 0.90),
        ],
        ("fils",): [
            ("Appelez mon fils s'il vous plaît", 0.85),
        ],
        ("fille",): [
            ("Appelez ma fille s'il vous plaît", 0.85),
        ],
    },
    "Portuguese": {
        ("fome",): [
            ("Estou com fome e quero comer", 0.85),
        ],
        ("sede",): [
            ("Estou com sede e quero água", 0.88),
        ],
        ("dor",): [
            ("Estou com dor e preciso de ajuda", 0.90),
        ],
        ("filho",): [
            ("Por favor, chame o meu filho", 0.85),
        ],
        ("filha",): [
            ("Por favor, chame a minha filha", 0.85),
        ],
    },
    "Yoruba": {
        ("ebi",): [("Ebi n pa mi, mo fẹ jẹun", 0.85)],
        ("omi",): [("Omi ngbẹ mi", 0.88)],
        ("irora",): [("Mo ni irora, mo nilo iranlowo", 0.90)],
        ("ọmọkunrin", "son"): [("Jọwọ pe ọmọkunrin mi", 0.85)],
        ("ọmọbinrin", "daughter"): [("Jọwọ pe ọmọbinrin mi", 0.85)],
    },
    "Igbo": {
        ("agụụ",): [("Agụụ na-agụ m, achọrọ m iri nri", 0.85)],
        ("mmiri",): [("Akpịrị na-akpọ m nkụ, achọrọ m mmiri", 0.88)],
        ("egbu",): [("Ahụ na-egbu m, achọrọ m enyemaka", 0.90)],
    },
    "Hausa": {
        ("yunwa",): [("Ina jin yunwa, ina son ci abinci", 0.85)],
        ("kishirwa",): [("Ina jin kishirwa, ina son ruwa", 0.88)],
        ("zafi",): [("Ina jin zafi, ina bukatar taimako", 0.90)],
    },
    "Pidgin": {
        ("hungry",): [("Hunger dey catch me, I wan chop", 0.85)],
        ("water",): [("Water dey thirst me, bring water", 0.88)],
        ("pain",): [("Body dey pain me, I need help", 0.90)],
        ("son",): [("Abeg call my son", 0.85)],
        ("daughter",): [("Abeg call my daughter", 0.85)],
    },
    "Arabic": {
        ("جائع", "طعام"): [("أنا جائع وأريد أن آكل", 0.85)],
        ("عطشان", "ماء"): [("أنا عطشان وأريد ماء", 0.88)],
        ("ألم",): [("أشعر بألم وأحتاج مساعدة", 0.90)],
    },
}


def _offline_complete(fragment: str, language: str = "English") -> list[tuple[str, float]]:
    fragment_lower = fragment.lower().strip()
    if not fragment_lower:
        return []

    words = set(fragment_lower.replace(",", " ").replace(".", " ").split())
    patterns = OFFLINE_PATTERNS.get(language, OFFLINE_PATTERNS["English"])

    matches = []
    for keywords, suggestions in patterns.items():
        overlap = sum(1 for kw in keywords if any(kw in w or w in kw for w in words))
        if overlap > 0:
            matches.append((overlap, suggestions))

    if matches:
        matches.sort(key=lambda x: -x[0])
        return matches[0][1]

    # Fall back to English patterns if no match in chosen language
    if language != "English":
        return _offline_complete(fragment, "English")

    # Generic fallback
    if len(words) == 1:
        word = list(words)[0]
        return [
            (f"I need {word}", 0.60),
            (f"I want {word}", 0.55),
            (f"Please bring me {word}", 0.50),
        ]

    return [
        (f"I would like to say: {fragment.strip()}", 0.55),
        (f"Please understand: {fragment.strip()}", 0.45),
    ]


def _claude_complete(
    fragment: str,
    aphasia_type: str = "anomic",
    language: str = "English",
    context_history: Optional[list[str]] = None,
    family_members: Optional[list[dict]] = None,
) -> Optional[list[tuple[str, float]]]:
    """Call Claude API with multilingual, family-aware prompt."""
    api_key = _get_claude_key()
    if not api_key:
        return None

    context_str = ""
    if context_history:
        recent = context_history[-3:]
        context_str = "\n\nRecent conversation context:\n" + "\n".join(f"- {c}" for c in recent)

    family_str = ""
    if family_members:
        members_desc = "\n".join(
            f"- {m.get('name', 'unnamed')} ({m.get('relationship', 'family')})"
            for m in family_members
        )
        family_str = (
            f"\n\nThe patient's family members (use these names in suggestions when relevant):\n"
            f"{members_desc}\n"
            f"For example, if the fragment is 'call son' and the son is named Samuel, "
            f"generate 'Please call my son Samuel' rather than generic 'call my son'."
        )

    prompt = f"""A stroke survivor with {aphasia_type} aphasia has typed these fragments: "{fragment}"

They know what they want to say but struggle to produce complete sentences. Generate 3 likely complete sentences they might mean.

CRITICAL: Generate all suggestions in {language}. Do not use English unless the user's language is English.{context_str}{family_str}

Guidelines:
- Use simple, natural everyday language in {language}
- Keep each sentence under 15 words
- Make them distinctly different interpretations
- Score each with confidence 0.0 to 1.0
- If family members are listed and relevant, use their actual names

Return ONLY valid JSON in this exact format:
{{"suggestions": [
  {{"sentence": "...", "confidence": 0.87}},
  {{"sentence": "...", "confidence": 0.72}},
  {{"sentence": "...", "confidence": 0.61}}
]}}"""

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 600,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=15,
        )
        if response.status_code != 200:
            return None

        data = response.json()
        text = data["content"][0]["text"].strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        parsed = json.loads(text)
        return [(s["sentence"], float(s["confidence"])) for s in parsed["suggestions"]]
    except Exception:
        return None


def complete_sentence(
    fragment: str,
    aphasia_type: str = "anomic",
    language: str = "English",
    context_history: Optional[list[str]] = None,
    family_members: Optional[list[dict]] = None,
) -> tuple[list[tuple[str, float]], str]:
    """Main entry — Claude first, offline fallback."""
    if not fragment or not fragment.strip():
        return [], "none"

    ai_result = _claude_complete(fragment, aphasia_type, language, context_history, family_members)
    if ai_result and len(ai_result) > 0:
        return ai_result, "ai"
    return _offline_complete(fragment, language), "offline"


# Predictive word completions per language
COMMON_WORDS_BY_LANG = {
    "English": {
        "a": ["and", "am", "at", "ask", "after"],
        "b": ["bed", "be", "bathroom", "bring", "blanket", "better"],
        "c": ["can", "call", "come", "cold", "cup", "chair", "child", "care"],
        "d": ["doctor", "drink", "daughter", "dinner"],
        "e": ["eat", "end", "every"],
        "f": ["family", "food", "feel", "friend", "father"],
        "g": ["go", "get", "good", "give"],
        "h": ["help", "hungry", "home", "hot", "hurt", "hospital", "husband"],
        "i": ["I", "in", "is", "it", "if"],
        "m": ["my", "more", "medicine", "morning", "mother"],
        "n": ["no", "not", "now", "need", "nurse"],
        "p": ["please", "pain", "phone", "pillow"],
        "r": ["rest", "room", "remember"],
        "s": ["sleep", "sit", "stop", "sad", "son", "sick"],
        "t": ["thank", "tired", "today", "together", "toilet"],
        "w": ["want", "water", "wife", "warm", "where"],
        "y": ["yes", "you", "your"],
    },
    "Spanish": {
        "a": ["ayuda", "agua", "ahora"],
        "b": ["baño", "beber"],
        "c": ["casa", "cama", "cansado", "comida"],
        "d": ["dolor", "dormir"],
        "e": ["esposa", "esposo"],
        "f": ["familia"],
        "h": ["hambre", "hijo", "hija"],
        "l": ["llame"],
        "m": ["médico", "madre"],
        "n": ["necesito", "no"],
        "p": ["por", "padre", "favor"],
        "q": ["quiero"],
        "s": ["sí", "sed"],
        "t": ["tengo"],
    },
    "French": {
        "a": ["aide", "ai", "appelez"],
        "b": ["besoin"],
        "d": ["docteur", "dormir", "douleur"],
        "e": ["eau", "épouse"],
        "f": ["faim", "famille", "fils", "fille"],
        "j": ["j'ai", "je"],
        "m": ["mal", "mari", "mère", "médecin"],
        "o": ["oui"],
        "p": ["père", "pain", "pour"],
        "s": ["soif"],
        "t": ["toilettes"],
    },
    "Portuguese": {
        "a": ["ajuda", "água"],
        "c": ["casa", "chame"],
        "d": ["dor", "dormir"],
        "e": ["esposa", "esposo"],
        "f": ["fome", "filho", "filha", "família"],
        "m": ["médico", "mãe", "marido"],
        "p": ["pai", "por", "favor"],
        "q": ["quero"],
        "s": ["sim", "sede"],
        "t": ["toilet", "tenho"],
    },
    "Yoruba": {
        "e": ["ebi", "e se"],
        "j": ["jọwọ"],
        "m": ["mo", "mi"],
        "o": ["omi", "oko"],
        "ọ": ["ọmọ", "ọmọkunrin", "ọmọbinrin"],
    },
    "Igbo": {
        "a": ["ahụ", "agụụ"],
        "b": ["biko"],
        "d": ["daalụ"],
        "m": ["mmiri"],
        "n": ["nwa"],
    },
    "Hausa": {
        "i": ["ina"],
        "y": ["yunwa"],
        "z": ["zafi"],
        "n": ["na gode"],
    },
    "Pidgin": {
        "a": ["abeg"],
        "b": ["body", "belle"],
        "c": ["chop", "call"],
        "h": ["hunger", "help"],
        "i": ["I"],
        "w": ["water", "want", "wan"],
    },
    "Arabic": {
        "أ": ["أحتاج", "أريد", "ألم", "أنا"],
        "ش": ["شكراً"],
        "م": ["ماء", "مساعدة"],
    },
}


def predict_next_words(partial: str, limit: int = 6, language: str = "English") -> list[str]:
    if not partial:
        # language-appropriate starter words
        defaults = {
            "English":    ["I", "please", "help", "want", "need", "thank"],
            "Spanish":    ["necesito", "quiero", "por favor", "ayuda"],
            "French":     ["j'ai", "je veux", "aidez", "merci"],
            "Portuguese": ["quero", "preciso", "ajuda", "obrigado"],
            "Yoruba":     ["mo", "jọwọ", "mi"],
            "Igbo":       ["biko", "achọrọ m"],
            "Hausa":      ["ina", "don Allah"],
            "Pidgin":     ["abeg", "I", "want"],
            "Arabic":     ["أحتاج", "من فضلك", "شكراً"],
        }
        return defaults.get(language, defaults["English"])[:limit]

    partial_lower = partial.lower().strip()
    if not partial_lower:
        return []

    first_char = partial_lower[0]
    candidates = COMMON_WORDS_BY_LANG.get(language, COMMON_WORDS_BY_LANG["English"]).get(first_char, [])

    matches = [w for w in candidates if w.lower().startswith(partial_lower)]

    if len(partial_lower) == 1:
        return matches[:limit]
    return matches[:limit]
