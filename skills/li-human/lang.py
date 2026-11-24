"""
lang.py - language detection and per-language settings for li-human.

The original pack was written for English only. Run on Italian it broke in
three places: the word regex was ASCII-only (so "perché" became "perch"),
the VOICE check counted English contractions that Italian does not have, and
the FINGERPRINT check punished the curly apostrophe that every phone keyboard
inserts in "l'azienda". This module fixes all three by switching the
regexes, the lexicon and the voice markers on the detected language.

  --lang auto   (default) pick by stop-word share
  --lang it     force Italian
  --lang en     force English (original behaviour)
"""

import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

LEXICONS = {
    "en": os.path.join(HERE, "slop.json"),
    "it": os.path.join(HERE, "slop_it.json"),
}

IT_STOP = set("""
il lo la i gli le un uno una di da in con su per tra fra che non è e ma
anche come più perché questo questa questi queste quello quella sono ho
hai ha abbiamo hanno del della dei delle nel nella nei nelle al alla ai
alle dal dalla mi ti ci si se poi già ancora sempre molto tutto tutti
""".split())
EN_STOP = set("""
the a an of to in and is it that for on with as was are be this have
you i we not but they at by from or my your our what so if just
""".split())

WORD_RE = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*", re.UNICODE)


def detect_language(text):
    toks = [t.lower().replace("’", "'") for t in WORD_RE.findall(text)]
    if not toks:
        return "en"
    it = sum(1 for t in toks if t in IT_STOP or t.split("'")[0] in ("l", "un", "dell", "nell", "all", "dall", "c", "d"))
    en = sum(1 for t in toks if t in EN_STOP)
    return "it" if it > en else "en"


def resolve(lang, text):
    return detect_language(text) if lang in (None, "auto") else lang


# ---- per-language voice markers -------------------------------------------

SETTINGS = {
    "en": {
        # contractions are the colloquial marker in English
        "colloquial": re.compile(r"\b\w+['’](?:s|t|re|ve|ll|d|m)\b", re.IGNORECASE),
        "colloquial_label": "contractions",
        "colloquial_human": 3.0,
        "person": re.compile(r"\b(i|me|my|mine|we|us|our|you|your)\b", re.IGNORECASE),
        "person_human": 8.0,
        # curly apostrophes count as a fingerprint in English text
        "curly": "‘’“”",
        "numbers": re.compile(r"\b\d[\d,.]*%?\b|\$\d"),
    },
    "it": {
        # Italian has no contractions. What separates spoken-sounding Italian
        # from model Italian is the discourse particles and the sentence that
        # opens on "E" or "Ma", which school grammar forbids and models obey.
        "colloquial": re.compile(
            r"\b(?:beh|boh|mah|ecco|insomma|cioè|tipo|mica|magari|eh|dai|ok|okay|"
            r"vabbè|vabbe|vabbuò|praticamente|tanto|comunque|pure|allora|però|"
            r"un po['’]|niente|sì|no\?|appunto|ovvio|figurati|anzi)\b"
            r"|(?:^|[.!?]\s+|\n)(?:E|Ma|Che|Perché|Quindi)\s",
            re.IGNORECASE | re.MULTILINE),
        "colloquial_label": "colloquial markers",
        "colloquial_human": 2.5,
        # pronouns plus the first/second-person verb forms Italian uses
        # instead of a subject pronoun ("ho visto", not "io ho visto")
        "person": re.compile(
            r"\b(?:io|me|mi|mio|mia|miei|mie|noi|ci|nostro|nostra|nostri|nostre|"
            r"tu|te|ti|tuo|tua|tuoi|tue|voi|vi|vostro|vostra|vostri|vostre|"
            r"ho|hai|abbiamo|avete|sono stato|sono stata|siamo|sei|siete|"
            r"facevo|faccio|fai|facciamo|penso|credo|so|sai|devo|posso|voglio|"
            r"vedo|dico|ricordo|ero|eravamo|avevo|avevamo)\b",
            re.IGNORECASE),
        "person_human": 7.0,
        # the curly apostrophe is what iOS and most Android keyboards type in
        # Italian; only curly double quotes are a tell
        "curly": "“”",
        # 1.300 / 1,5 / 20% / €20 / 20€
        "numbers": re.compile(r"\b\d[\d.,]*\s?(?:%|€)?|€\s?\d"),
    },
}


def term_pattern(find):
    """Regex for a lexicon entry: case-insensitive, any run of spaces between
    words, straight or curly apostrophe, and word boundaries only where the
    entry starts or ends on a letter (so "spoiler:" and "pensateci" both work)."""
    body = re.escape(find).replace(r"\ ", r"\s+").replace("'", "['’]")
    left = r"\b" if find[:1].isalnum() else ""
    right = r"\b" if find[-1:].isalnum() else ""
    return re.compile(left + body + right, re.IGNORECASE)
