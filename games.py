"""
games.py — SpeakAgain v2.1 interactive games
---------------------------------------------
Five therapeutic mini-games, all fully playable in this version:

1. Picture match — emoji-based word-to-picture pairing (replaces
   earlier text-only version)
2. Category sort — sort words by semantic category
3. Sentence puzzle — rearrange scrambled words into a correct sentence
4. First letter challenge — naming burst against the clock
5. Story builder — fill the missing word in each of four sentences

Each game is language-aware. The emoji vocabulary for Picture match
is the same across languages because emoji are visual — only the
target word is translated.
"""

import random
import streamlit as st
from typing import Optional
from i18n import t


# ==========================================================
# PICTURE LIBRARY — emoji is a universal visual language
# Picture match works in every language because emoji don't translate
# ==========================================================
PICTURE_LIBRARY = {
    # Food
    "apple":    {"emoji": "🍎", "translations": {"English": "apple", "Spanish": "manzana", "French": "pomme", "Portuguese": "maçã", "Yoruba": "apulu", "Igbo": "apụl", "Hausa": "tuffa", "Pidgin": "apple", "Arabic": "تفاحة"}},
    "bread":    {"emoji": "🍞", "translations": {"English": "bread", "Spanish": "pan", "French": "pain", "Portuguese": "pão", "Yoruba": "buredi", "Igbo": "achịcha", "Hausa": "burodi", "Pidgin": "bread", "Arabic": "خبز"}},
    "rice":     {"emoji": "🍚", "translations": {"English": "rice", "Spanish": "arroz", "French": "riz", "Portuguese": "arroz", "Yoruba": "iresi", "Igbo": "osikapa", "Hausa": "shinkafa", "Pidgin": "rice", "Arabic": "أرز"}},
    "fish":     {"emoji": "🐟", "translations": {"English": "fish", "Spanish": "pez", "French": "poisson", "Portuguese": "peixe", "Yoruba": "eja", "Igbo": "azụ", "Hausa": "kifi", "Pidgin": "fish", "Arabic": "سمكة"}},
    # Animals
    "dog":      {"emoji": "🐕", "translations": {"English": "dog", "Spanish": "perro", "French": "chien", "Portuguese": "cão", "Yoruba": "aja", "Igbo": "nkịta", "Hausa": "kare", "Pidgin": "dog", "Arabic": "كلب"}},
    "cat":      {"emoji": "🐈", "translations": {"English": "cat", "Spanish": "gato", "French": "chat", "Portuguese": "gato", "Yoruba": "ologbo", "Igbo": "nwamba", "Hausa": "kyanwa", "Pidgin": "cat", "Arabic": "قطة"}},
    # Household
    "bed":      {"emoji": "🛏️", "translations": {"English": "bed", "Spanish": "cama", "French": "lit", "Portuguese": "cama", "Yoruba": "bedi", "Igbo": "akwa", "Hausa": "gado", "Pidgin": "bed", "Arabic": "سرير"}},
    "chair":    {"emoji": "🪑", "translations": {"English": "chair", "Spanish": "silla", "French": "chaise", "Portuguese": "cadeira", "Yoruba": "aga", "Igbo": "oche", "Hausa": "kujera", "Pidgin": "chair", "Arabic": "كرسي"}},
    "cup":      {"emoji": "☕", "translations": {"English": "cup", "Spanish": "taza", "French": "tasse", "Portuguese": "xícara", "Yoruba": "ago", "Igbo": "iko", "Hausa": "koko", "Pidgin": "cup", "Arabic": "كوب"}},
    "phone":    {"emoji": "📱", "translations": {"English": "phone", "Spanish": "teléfono", "French": "téléphone", "Portuguese": "telefone", "Yoruba": "foonu", "Igbo": "ekwentị", "Hausa": "waya", "Pidgin": "phone", "Arabic": "هاتف"}},
    "key":      {"emoji": "🔑", "translations": {"English": "key", "Spanish": "llave", "French": "clé", "Portuguese": "chave", "Yoruba": "kokoro", "Igbo": "igodo", "Hausa": "maɓallai", "Pidgin": "key", "Arabic": "مفتاح"}},
    # Nature
    "sun":      {"emoji": "☀️", "translations": {"English": "sun", "Spanish": "sol", "French": "soleil", "Portuguese": "sol", "Yoruba": "oorun", "Igbo": "anyanwụ", "Hausa": "rana", "Pidgin": "sun", "Arabic": "شمس"}},
    "tree":     {"emoji": "🌳", "translations": {"English": "tree", "Spanish": "árbol", "French": "arbre", "Portuguese": "árvore", "Yoruba": "igi", "Igbo": "osisi", "Hausa": "itace", "Pidgin": "tree", "Arabic": "شجرة"}},
    "flower":   {"emoji": "🌸", "translations": {"English": "flower", "Spanish": "flor", "French": "fleur", "Portuguese": "flor", "Yoruba": "ododo", "Igbo": "ifuru", "Hausa": "fure", "Pidgin": "flower", "Arabic": "زهرة"}},
    "water":    {"emoji": "💧", "translations": {"English": "water", "Spanish": "agua", "French": "eau", "Portuguese": "água", "Yoruba": "omi", "Igbo": "mmiri", "Hausa": "ruwa", "Pidgin": "water", "Arabic": "ماء"}},
    # Transport
    "car":      {"emoji": "🚗", "translations": {"English": "car", "Spanish": "coche", "French": "voiture", "Portuguese": "carro", "Yoruba": "moto", "Igbo": "ụgbọala", "Hausa": "mota", "Pidgin": "motor", "Arabic": "سيارة"}},
    "book":     {"emoji": "📖", "translations": {"English": "book", "Spanish": "libro", "French": "livre", "Portuguese": "livro", "Yoruba": "iwe", "Igbo": "akwụkwọ", "Hausa": "littafi", "Pidgin": "book", "Arabic": "كتاب"}},
    "door":     {"emoji": "🚪", "translations": {"English": "door", "Spanish": "puerta", "French": "porte", "Portuguese": "porta", "Yoruba": "ilekun", "Igbo": "ọnụ ụzọ", "Hausa": "ƙofa", "Pidgin": "door", "Arabic": "باب"}},
}


# ==========================================================
# CATEGORIES for category-sort game
# ==========================================================
CATEGORIES_BY_LANG = {
    "English": {
        "Food": ["rice", "bread", "fish", "apple"],
        "Animals": ["dog", "cat"],
        "Household": ["bed", "chair", "cup", "phone", "key", "door"],
        "Nature": ["sun", "tree", "flower", "water"],
    },
    "Spanish": {
        "Comida": ["arroz", "pan", "pez", "manzana"],
        "Animales": ["perro", "gato"],
        "Casa": ["cama", "silla", "taza", "teléfono", "llave", "puerta"],
        "Naturaleza": ["sol", "árbol", "flor", "agua"],
    },
    "French": {
        "Nourriture": ["riz", "pain", "poisson", "pomme"],
        "Animaux": ["chien", "chat"],
        "Maison": ["lit", "chaise", "tasse", "téléphone", "clé", "porte"],
        "Nature": ["soleil", "arbre", "fleur", "eau"],
    },
    "Portuguese": {
        "Comida": ["arroz", "pão", "peixe", "maçã"],
        "Animais": ["cão", "gato"],
        "Casa": ["cama", "cadeira", "xícara", "telefone", "chave", "porta"],
        "Natureza": ["sol", "árvore", "flor", "água"],
    },
    "Yoruba": {
        "Ounjẹ": ["iresi", "buredi", "eja"],
        "Ẹranko": ["aja", "ologbo"],
        "Ile": ["bedi", "aga", "ago", "foonu", "ilekun"],
        "Iseda": ["oorun", "igi", "ododo", "omi"],
    },
    "Igbo": {
        "Nri": ["osikapa", "achịcha", "azụ"],
        "Anụmanụ": ["nkịta", "nwamba"],
        "Ụlọ": ["akwa", "oche", "iko", "ekwentị", "ọnụ ụzọ"],
        "Okike": ["anyanwụ", "osisi", "ifuru", "mmiri"],
    },
    "Hausa": {
        "Abinci": ["shinkafa", "burodi", "kifi"],
        "Dabbobi": ["kare", "kyanwa"],
        "Gida": ["gado", "kujera", "koko", "waya", "ƙofa"],
        "Halitta": ["rana", "itace", "fure", "ruwa"],
    },
    "Pidgin": {
        "Food": ["rice", "bread", "fish"],
        "Animals": ["dog", "cat"],
        "House": ["bed", "chair", "cup", "phone", "door"],
        "Nature": ["sun", "tree", "flower", "water"],
    },
    "Arabic": {
        "طعام": ["أرز", "خبز", "سمكة", "تفاحة"],
        "حيوانات": ["كلب", "قطة"],
        "منزل": ["سرير", "كرسي", "كوب", "هاتف", "باب"],
        "طبيعة": ["شمس", "شجرة", "زهرة", "ماء"],
    },
}


# ==========================================================
# SENTENCES for sentence-puzzle game
# ==========================================================
PUZZLE_SENTENCES = {
    "English": [
        "I want a cup of water",
        "Please call my doctor today",
        "The food is very hot",
        "My family loves me very much",
        "I am feeling better now",
    ],
    "Spanish": [
        "Quiero una taza de agua",
        "Por favor llame al médico",
        "La comida está muy caliente",
        "Mi familia me quiere mucho",
    ],
    "French": [
        "Je veux une tasse d'eau",
        "Appelez le médecin s'il vous plaît",
        "La nourriture est très chaude",
    ],
    "Portuguese": [
        "Quero uma xícara de água",
        "Por favor chame o médico",
        "A comida está muito quente",
    ],
    "Yoruba": [
        "Mo fẹ ago omi kan",
        "Jọwọ pe dokita",
        "Ounjẹ gbona pupọ",
    ],
    "Igbo": [
        "Achọrọ m iko mmiri",
        "Biko kpọọ dọkịta",
    ],
    "Hausa": [
        "Ina son koko na ruwa",
        "Don Allah kira likita",
    ],
    "Pidgin": [
        "I want cup of water",
        "Abeg call the doctor",
    ],
    "Arabic": [
        "أريد كوب من الماء",
        "من فضلك اتصل بالطبيب",
    ],
}


# ==========================================================
# STORIES for story-builder game — 4 sentences, one blank per sentence
# ==========================================================
STORIES = {
    "English": [
        {
            "title": "Morning routine",
            "parts": [
                ("I woke up at seven in the ___", "morning", ["morning", "kitchen", "garden"]),
                ("I brushed my ___", "teeth", ["teeth", "phone", "door"]),
                ("Then I drank a cup of ___", "water", ["water", "bed", "tree"]),
                ("Finally I went to the ___", "hospital", ["hospital", "cup", "flower"]),
            ],
        },
        {
            "title": "Visiting family",
            "parts": [
                ("My son came to visit with his ___", "wife", ["wife", "car", "sun"]),
                ("We all sat in the ___", "living room", ["living room", "fish", "key"]),
                ("The children played with the ___", "dog", ["dog", "chair", "flower"]),
                ("I was very ___", "happy", ["happy", "cold", "thirsty"]),
            ],
        },
    ],
    "Spanish": [
        {
            "title": "Rutina matinal",
            "parts": [
                ("Me desperté a las siete de la ___", "mañana", ["mañana", "cocina", "jardín"]),
                ("Me cepillé los ___", "dientes", ["dientes", "teléfono", "puerta"]),
                ("Luego bebí una taza de ___", "agua", ["agua", "cama", "árbol"]),
                ("Finalmente fui al ___", "hospital", ["hospital", "taza", "flor"]),
            ],
        },
    ],
    "French": [
        {
            "title": "Routine matinale",
            "parts": [
                ("Je me suis réveillé à sept heures du ___", "matin", ["matin", "cuisine", "jardin"]),
                ("Je me suis brossé les ___", "dents", ["dents", "téléphone", "porte"]),
                ("Puis j'ai bu une tasse d' ___", "eau", ["eau", "lit", "arbre"]),
                ("Finalement je suis allé à l' ___", "hôpital", ["hôpital", "tasse", "fleur"]),
            ],
        },
    ],
    "Portuguese": [
        {
            "title": "Rotina matinal",
            "parts": [
                ("Acordei às sete da ___", "manhã", ["manhã", "cozinha", "jardim"]),
                ("Escovei os ___", "dentes", ["dentes", "telefone", "porta"]),
                ("Depois bebi uma xícara de ___", "água", ["água", "cama", "árvore"]),
                ("Finalmente fui ao ___", "hospital", ["hospital", "xícara", "flor"]),
            ],
        },
    ],
    "Yoruba": [
        {
            "title": "Ilana owurọ",
            "parts": [
                ("Mo ji ni aago meje ___", "owurọ", ["owurọ", "ile ounjẹ", "ọgba"]),
                ("Mo fọ ___ mi", "ehin", ["ehin", "foonu", "ilekun"]),
                ("Lẹhin naa mo mu ___ kan", "omi", ["omi", "bedi", "igi"]),
                ("Nikẹhin mo lọ si ___", "ile iwosan", ["ile iwosan", "ago", "ododo"]),
            ],
        },
    ],
    "Pidgin": [
        {
            "title": "Morning things",
            "parts": [
                ("I wake up for seven for ___", "morning", ["morning", "kitchen", "garden"]),
                ("I brush my ___", "teeth", ["teeth", "phone", "door"]),
                ("Then I drink one cup of ___", "water", ["water", "bed", "tree"]),
                ("Finally I go ___", "hospital", ["hospital", "cup", "flower"]),
            ],
        },
    ],
}


# ==========================================================
# GAME 1: PICTURE MATCH (fixed — now emoji-based)
# ==========================================================
def play_picture_match(language: str, award_xp, notify_family):
    """Pair emoji pictures with their correct words."""
    st.markdown(f"### 🎯 {t('games.word_match', language)}")

    if "picmatch" not in st.session_state or st.session_state.picmatch.get("done"):
        # Start a fresh round with 4 items
        words = random.sample(list(PICTURE_LIBRARY.keys()), 4)
        translated = {
            w: PICTURE_LIBRARY[w]["translations"].get(language,
                PICTURE_LIBRARY[w]["translations"]["English"])
            for w in words
        }
        # Shuffle the word list that the player sees
        shuffled_words = list(translated.values())
        random.shuffle(shuffled_words)

        st.session_state.picmatch = {
            "keys": words,
            "translated": translated,
            "shuffled": shuffled_words,
            "matches": {},       # {english_key: selected_word_or_None}
            "done": False,
        }

    state = st.session_state.picmatch

    st.caption("Match each picture to the correct word by selecting from the dropdown.")

    # Display emoji cards with dropdowns
    for key in state["keys"]:
        emoji = PICTURE_LIBRARY[key]["emoji"]
        correct = state["translated"][key]

        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown(
                f"<div style='font-size: 64px; text-align: center;'>{emoji}</div>",
                unsafe_allow_html=True,
            )
        with col2:
            selected = st.selectbox(
                "Select word:",
                ["— choose —"] + state["shuffled"],
                key=f"picmatch_{key}",
                label_visibility="collapsed",
            )
            if selected != "— choose —":
                state["matches"][key] = selected

    # Check button
    if len(state["matches"]) == len(state["keys"]):
        if st.button(t("btn.check", language), type="primary"):
            correct_count = sum(
                1 for k in state["keys"]
                if state["matches"].get(k) == state["translated"][k]
            )
            total = len(state["keys"])
            state["done"] = True

            if correct_count == total:
                st.balloons()
                award_xp(50, "perfect picture match")
                notify_family(f"scored a perfect picture match ({total}/{total})")
                st.success(f"🎉 Perfect! {correct_count}/{total} — +50 XP")
            else:
                award_xp(20 + correct_count * 5, "picture match")
                notify_family(f"completed picture match ({correct_count}/{total})")
                st.info(f"Got {correct_count}/{total} — +{20 + correct_count * 5} XP")

                # Show corrections
                for k in state["keys"]:
                    chosen = state["matches"].get(k)
                    expected = state["translated"][k]
                    emoji = PICTURE_LIBRARY[k]["emoji"]
                    if chosen == expected:
                        st.markdown(f"✅ {emoji} — {expected}")
                    else:
                        st.markdown(f"❌ {emoji} — you said **{chosen}**, correct was **{expected}**")

    # Play again
    if state.get("done"):
        if st.button(t("btn.next", language)):
            del st.session_state.picmatch
            st.rerun()


# ==========================================================
# GAME 2: CATEGORY SORT (now fully playable)
# ==========================================================
def play_category_sort(language: str, award_xp, notify_family):
    st.markdown(f"### 🧺 {t('games.category_sort', language)}")

    categories = CATEGORIES_BY_LANG.get(language, CATEGORIES_BY_LANG["English"])

    if "catsort" not in st.session_state or st.session_state.catsort.get("done"):
        # Pick 2-3 categories and pull a few words from each
        chosen_cats = random.sample(list(categories.keys()),
                                    min(3, len(categories)))
        word_to_cat = {}
        for c in chosen_cats:
            for w in categories[c][:3]:
                word_to_cat[w] = c

        shuffled = list(word_to_cat.keys())
        random.shuffle(shuffled)

        st.session_state.catsort = {
            "categories": chosen_cats,
            "word_to_cat": word_to_cat,
            "shuffled": shuffled,
            "assignments": {},
            "done": False,
        }

    state = st.session_state.catsort

    st.caption(
        "Assign each word to the correct category. "
        f"Categories: {', '.join(state['categories'])}"
    )

    # Render each word with a dropdown for category
    for word in state["shuffled"]:
        col1, col2 = st.columns([2, 3])
        with col1:
            st.markdown(f"**{word}**")
        with col2:
            choice = st.selectbox(
                "Category:",
                ["— choose —"] + state["categories"],
                key=f"catsort_{word}",
                label_visibility="collapsed",
            )
            if choice != "— choose —":
                state["assignments"][word] = choice

    if len(state["assignments"]) == len(state["shuffled"]):
        if st.button(t("btn.check", language), type="primary"):
            correct = sum(
                1 for w, c in state["assignments"].items()
                if c == state["word_to_cat"][w]
            )
            total = len(state["shuffled"])
            state["done"] = True

            if correct == total:
                st.balloons()
                award_xp(50, "perfect category sort")
                notify_family(f"scored a perfect category sort ({correct}/{total})")
                st.success(f"🎉 Perfect! {correct}/{total} — +50 XP")
            else:
                award_xp(20 + correct * 3, "category sort")
                notify_family(f"completed category sort ({correct}/{total})")
                st.info(f"{correct}/{total} — +{20 + correct * 3} XP")

    if state.get("done"):
        if st.button(t("btn.next", language)):
            del st.session_state.catsort
            st.rerun()


# ==========================================================
# GAME 3: SENTENCE PUZZLE (now fully playable)
# ==========================================================
def play_sentence_puzzle(language: str, award_xp, notify_family):
    st.markdown(f"### 🧩 {t('games.sentence_puzzle', language)}")

    sentences = PUZZLE_SENTENCES.get(language, PUZZLE_SENTENCES["English"])

    if "puzzle" not in st.session_state or st.session_state.puzzle.get("done"):
        target = random.choice(sentences)
        words = target.split()
        shuffled = words.copy()
        # Ensure it's actually shuffled
        while shuffled == words and len(words) > 1:
            random.shuffle(shuffled)

        st.session_state.puzzle = {
            "target": target,
            "words": words,
            "shuffled": shuffled,
            "built": [],
            "remaining": shuffled.copy(),
            "done": False,
        }

    state = st.session_state.puzzle

    st.caption("Tap the words in the correct order to build the sentence.")

    # Show what's been built so far
    built_display = " ".join(state["built"]) if state["built"] else "_(empty)_"
    st.markdown(
        f"<div style='background: #EAF3DE; padding: 14px 18px; "
        f"border-radius: 8px; font-size: 18px; min-height: 50px;'>"
        f"{built_display}</div>",
        unsafe_allow_html=True,
    )

    # Word buttons
    st.markdown("**Remaining words:**")
    if state["remaining"]:
        cols = st.columns(min(len(state["remaining"]), 5))
        for i, word in enumerate(state["remaining"]):
            with cols[i % len(cols)]:
                if st.button(word, key=f"puz_{i}_{word}_{random.random()}",
                             use_container_width=True):
                    state["built"].append(word)
                    state["remaining"].remove(word)
                    st.rerun()

    # Control buttons
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        if st.button("↩ Undo", disabled=not state["built"]):
            if state["built"]:
                state["remaining"].append(state["built"].pop())
                st.rerun()
    with col_b:
        if not state["remaining"] and not state["done"]:
            if st.button(t("btn.check", language), type="primary"):
                built_sentence = " ".join(state["built"])
                state["done"] = True
                if built_sentence.lower() == state["target"].lower():
                    st.balloons()
                    award_xp(50, "perfect sentence puzzle")
                    notify_family(f'solved sentence puzzle: "{state["target"]}"')
                    st.success(f"🎉 {state['target']} — +50 XP")
                else:
                    award_xp(15, "sentence puzzle attempt")
                    notify_family("attempted sentence puzzle")
                    st.info(f"You had: **{built_sentence}**")
                    st.info(f"Correct: **{state['target']}** — +15 XP")
    with col_c:
        if state.get("done") or state["remaining"] or state["built"]:
            if st.button(t("btn.next", language)):
                del st.session_state.puzzle
                st.rerun()


# ==========================================================
# GAME 4: FIRST LETTER CHALLENGE
# ==========================================================
def play_first_letter(language: str, award_xp, notify_family):
    st.markdown(f"### 🔤 {t('games.first_letter', language)}")

    if "firstletter" not in st.session_state:
        letter_sets = {
            "English": "BCDFGHLMNPRST",
            "Spanish": "BCDFGHLMNPRST",
            "French": "BCDFGHLMNPRST",
            "Portuguese": "BCDFGHLMNPRST",
            "Yoruba": "BDFGKMNORSṢT",
            "Igbo": "ABCDEGHIKLMNOS",
            "Hausa": "BDFGHJKLMNRSTWY",
            "Pidgin": "BCDFGHLMNPRST",
            "Arabic": "بمشكرلنتدف",
        }
        letters = letter_sets.get(language, letter_sets["English"])
        st.session_state.firstletter = {
            "letter": random.choice(letters),
            "done": False,
        }

    state = st.session_state.firstletter
    letter = state["letter"]

    st.markdown(
        f"<h1 style='text-align: center; font-size: 72px; color: #2B6CB0;'>"
        f"{letter}</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"**Name as many words as you can that start with "
        f"{letter}. Write one per line.**"
    )

    entries = st.text_area("Your words:", height=150, key="fl_entries")

    if not state["done"]:
        if st.button(t("btn.submit", language), type="primary"):
            lines = [x.strip() for x in entries.split("\n") if x.strip()]
            valid = [w for w in lines if w and w[0].upper() == letter.upper()]
            score = len(valid)
            state["done"] = True

            if score >= 5:
                st.balloons()
                award_xp(50, "first letter bonus")
                notify_family(f"scored {score} words in First Letter challenge")
                st.success(f"🎉 {score} words! +50 XP")
            elif score >= 3:
                award_xp(30, "first letter")
                notify_family(f"scored {score} in First Letter")
                st.success(f"Good — {score} words! +30 XP")
            else:
                award_xp(15, "first letter effort")
                notify_family(f"attempted First Letter ({score} words)")
                st.info(f"Got {score} words. +15 XP for trying.")

            if valid:
                st.markdown("**Your valid words:** " + ", ".join(valid))

    if state.get("done"):
        if st.button(t("btn.next", language)):
            del st.session_state.firstletter
            st.rerun()


# ==========================================================
# GAME 5: STORY BUILDER
# ==========================================================
def play_story_builder(language: str, award_xp, notify_family):
    st.markdown(f"### 📖 {t('games.story_builder', language)}")

    stories = STORIES.get(language, STORIES["English"])

    if "story" not in st.session_state or st.session_state.story.get("done"):
        st.session_state.story = {
            "story": random.choice(stories),
            "answers": {},
            "done": False,
        }

    state = st.session_state.story
    story = state["story"]

    st.markdown(f"**{story['title']}**")
    st.caption("Fill in the missing word in each sentence.")

    for i, (sentence, answer, options) in enumerate(story["parts"]):
        st.markdown(f"**{i + 1}.** {sentence}")
        choice = st.radio(
            f"Choose for sentence {i + 1}:",
            options,
            key=f"story_{i}",
            horizontal=True,
            label_visibility="collapsed",
        )
        state["answers"][i] = choice

    if not state["done"]:
        if st.button(t("btn.check", language), type="primary"):
            correct = sum(
                1 for i, (_, ans, _) in enumerate(story["parts"])
                if state["answers"].get(i) == ans
            )
            total = len(story["parts"])
            state["done"] = True

            if correct == total:
                st.balloons()
                award_xp(70, "perfect story")
                notify_family(f"completed story perfectly ({total}/{total})")
                st.success(f"🎉 Perfect story! +70 XP")

                # Show completed story
                st.markdown("---")
                st.markdown("**Your story:**")
                for sentence, answer, _ in story["parts"]:
                    st.markdown(f"_{sentence.replace('___', '**' + answer + '**')}_")
            else:
                award_xp(25 + correct * 10, "story builder")
                notify_family(f"completed story ({correct}/{total})")
                st.info(f"{correct}/{total} — +{25 + correct * 10} XP")

                st.markdown("**Corrections:**")
                for i, (sentence, answer, _) in enumerate(story["parts"]):
                    chosen = state["answers"].get(i)
                    check = "✅" if chosen == answer else "❌"
                    st.markdown(f"{check} {sentence.replace('___', answer)}")

    if state.get("done"):
        if st.button(t("btn.next", language)):
            del st.session_state.story
            st.rerun()


# ==========================================================
# ROUTER
# ==========================================================
def play_game(game_id: str, language: str, award_xp, notify_family):
    """Dispatch to the right game implementation."""
    dispatch = {
        "word_match": play_picture_match,
        "category_sort": play_category_sort,
        "sentence_puzzle": play_sentence_puzzle,
        "first_letter": play_first_letter,
        "story_builder": play_story_builder,
    }
    handler = dispatch.get(game_id)
    if handler:
        handler(language, award_xp, notify_family)
    else:
        st.info(f"Unknown game: {game_id}")
