---
name: li-human
description: >-
  Strip the machine fingerprint out of any draft - em dashes, AI slop words,
  invisible watermark characters - and score it against a five-check detection
  panel before it goes out. Use whenever text needs to sound human, when the
  user says humanize, "does this sound like AI", "remove the em dashes", "de-slop
  this", "will this get flagged", or before any LinkedIn post, comment, reply
  or DM is shown to the user.
---

# li-human

Two tools live in this folder and they both actually run. Use them. Do not
eyeball this.

```bash
python3 humanize.py draft.txt --report        # clean it, show what changed
python3 detect.py draft.txt                    # score it, five checks
python3 detect.py before.txt after.txt         # prove the delta
```

Both detect the language of the draft (`--lang auto`, the default) and load
the matching lexicon: `slop.json` for English, `slop_it.json` for Italian.
Force it with `--lang it` or `--lang en`. Pass the same `--lang` to every call
in one job, so before and after are scored the same way.

`slop.json` is the English lexicon: 100+ stock words and phrases with
plain-English replacements, 17 invisible character classes, 11 typographic
substitutions, and 11 structural tells. It is meant to be edited. If the user
has a word they always use that the lexicon strips, remove it from the file.

## Italian (`slop_it.json`)

Italian is scored on its own terms, not as broken English:

- **Words** are matched with accents, so "perché" and "città" count as words.
- **VOICE** does not look for contractions, which Italian does not have. It
  counts discourse particles (beh, insomma, cioè, magari, comunque, anzi, un
  po'), sentences that open on "E" or "Ma", and first and second person,
  including verb forms that carry the person without a pronoun ("ho visto",
  "abbiamo chiuso").
- **FINGERPRINT** does not penalise the curly apostrophe (’). Every phone
  keyboard types it in "l'azienda". It is still normalised to a straight one.
  Curly double quotes and em dashes still count.
- **SPECIFICITY** reads Italian numbers: 1.300, 1,5, 20%, €20.
- **The lexicon** has about 275 word forms, 50 phrases and 12 structures:
  fondamentale, cruciale, sfruttare, ottimizzare, valorizzare, sinergia,
  ecosistema, paradigma, inoltre, pertanto, "nel mondo frenetico di oggi",
  "è importante sottolineare che", "non si tratta solo di X, ma di Y",
  "Il risultato?", "Cosa ne pensate?" and the rest.

Most Italian entries have `"replace": null`. That means **flagged, not
swapped**: in Italian a blind substitution breaks gender and number agreement
("un mindset aperto" becomes "un mentalità aperto") or the meaning. The report
lists them as `(segnalato, riscrivere a mano)`. Treat them exactly like the
structural tells: rewrite the sentence yourself, keep the user's meaning, then
re-run `detect.py`. Only safe swaps with identical endings are automatic
(fondamentale -> importante, sfruttano -> usano, robusti -> solidi, inoltre ->
poi, pertanto -> quindi).

When you rewrite Italian, do not replace one stock word with its stock
synonym ("cruciale" -> "essenziale"). Replace the abstraction with the fact:
a number, a name, a thing that happened.

The thresholds (burstiness 0.70, voice targets) were calibrated on English.
For Italian they are provisional. If three of the user's own hand-written
posts do not score PASS, the threshold is wrong, not the user: tell them so,
and use the score only to compare drafts before and after.

## What gets fixed automatically

**1. Invisible characters.** Zero-width spaces and joiners, word joiners,
soft hyphens, byte-order marks, Unicode tag characters, non-breaking and
narrow spaces. A keyboard does not produce these. They survive copy-paste,
they are invisible in every editor, and they are the single most mechanical
thing in generated text. `humanize.py` deletes every one, including any
remaining Unicode format character it does not have a name for.

**2. Typography.** Em dash to comma, en dash to hyphen, curly quotes to
straight, ellipsis to three dots, bullet character to hyphen. The em dash pass
is the one that matters: it collapses ` — ` to `, ` and then cleans up the
double punctuation that leaves behind.

**3. The slop lexicon.** delve, leverage, robust, seamless, crucial, tapestry,
testament to, moreover, "in today's fast-paced world", "let that sink in" and
the rest, each swapped for a plain word, with capitalisation preserved and
URLs left untouched.

## What does NOT get fixed automatically

Structural tells get **flagged, not rewritten**, because changing the shape of
a sentence needs judgement:

- "It's not just X, it's Y" and "not only X but also Y"
- Rule-of-three triads
- Rhetorical one-word question lines: "The result?"
- Rocket, fire, bulb, sparkle and dart emoji
- Hashtag walls
- Reflex engagement bait: "Thoughts?", "Agree?", "Who else?"
- Uniform sentence length and uniform bullet length

That list is your job. Rewrite each flagged line by hand, keeping the meaning,
then re-run `detect.py`. This is the part that moves the score from REVIEW to
PASS, and it is the part a script cannot do.

## The five checks

`detect.py` scores five signals 0-100, higher is more human:

| check | what it measures | machine looks like |
| --- | --- | --- |
| BURSTINESS | sentence-length variation | every sentence the same length |
| SPECIFICITY | numbers, names, concrete markers per 100 words | abstract nouns, no figures |
| SLOP DENSITY | lexicon hits per 100 words | stock vocabulary |
| FINGERPRINT | invisible chars, em dashes, curly quotes per 1k chars | typographically perfect |
| VOICE | contractions (EN) or colloquial markers (IT), person, structural tells | no contractions, staged reveals |

The verdict weights the mean at 60% and the **weakest single check** at 40%,
because a detector only needs one signal to fire. PASS needs an overall of 70+
with no check below 55.

## Say this honestly

These are five local heuristics modelled on the signals public detectors key
on. They run entirely on the user's machine and nothing is uploaded. They are
**not** GPTZero, Originality, Copyleaks, Winston or Turnitin, they do not call
those APIs, and they cannot promise those verdicts. Fixing what they measure
does tend to move those numbers, because they are measuring the same
underlying things. That is the claim. Do not make a bigger one on the user's
behalf, and do not tell a user their text is undetectable.

## Order of operations

1. `humanize.py draft.txt -o clean.txt --report`
2. Read the structural flags. Rewrite those lines yourself.
3. `detect.py draft.txt clean.txt` to show the before and after.
4. If the verdict is not PASS, fix the weakest check named in the output and
   go again. Two rounds is normal. Five means the draft was written by
   formula, and the fix is a different draft, not more passes.
5. Show the user the cleaned text and the score. Never the score alone.
