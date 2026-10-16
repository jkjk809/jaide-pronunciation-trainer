"""
Thin caching + CMUdict lookup layer on top of g2p_align.

Why this is separate from g2p_align.py: align_word() is already lru_cache'd
in-process, but this module additionally handles:
  1. Looking up a word's ARPABET pronunciation from CMUdict (matching
     whichever pronunciation g2p_en/g2p_en's underlying cmudict picked --
     see note in get_alignment_for_word below).
  2. Providing one call site (`get_alignment_for_word`) that the rest of the
     pipeline uses, so if caching strategy changes later (e.g. persistent
     disk cache across server restarts), only this file needs to change.
"""

from nltk.corpus import cmudict
from g2p_align import align_word

_CMU_DICT = cmudict.dict()


def get_arpabet_for_word(word):
    """
    Look up ARPABET phonemes (WITH stress digits, as CMUdict stores them)
    for a single word. Returns the FIRST pronunciation variant CMUdict lists
    (matches g2p_en's own behavior: `pron = self.cmu[word][0]`).

    Returns None if the word isn't in CMUdict (rare for common English words;
    g2p_en would fall back to a neural predictor in that case -- see the
    note in get_alignment_for_word for how callers should handle this).
    """
    word_lower = word.lower()
    entries = _CMU_DICT.get(word_lower)
    if not entries:
        return None
    return tuple(entries[0])


def get_alignment_for_word(word):
    """
    Get the (char_start, char_end, phoneme_index) spans for `word`, aligned
    against its CMUdict ARPABET pronunciation.

    HYPHENATED WORDS: CMUdict essentially never has an entry for a fused
    hyphenated form ("well-known" -> None), but reliably has each side on
    its own ("well" -> found, "known" -> found). g2p_en itself treats a
    hyphenated word as one fused pronunciation unit with no separate token
    for the hyphen (confirmed empirically -- no '-' appears in its output).
    So a hyphenated word is handled as a small compound: split on '-',
    align each sub-word independently against its own CMUdict entry, then
    stitch the results into one alignment spanning the whole hyphenated
    word -- sub-word char offsets shifted to account for earlier sub-words
    and their hyphens, sub-word phoneme indices renumbered to be sequential
    across the whole word (matching how g2p_en concatenates the sub-words'
    phonemes with no separator). If ANY sub-word is missing from CMUdict,
    the whole compound alignment is abandoned (returns None) rather than
    returning a partial/inconsistent alignment -- caller falls back.

    IMPORTANT CAVEAT: this looks up ARPABET independently via CMUdict, rather
    than receiving the ARPABET phonemes g2p_en actually produced for this
    word in context. For the overwhelming majority of words these are
    identical (g2p_en uses CMUdict as its primary source). They can differ
    when:
      - g2p_en used its neural predictor because the word wasn't in CMUdict
        at all (rare -- proper nouns, typos, made-up words)
      - g2p_en picked a homograph variant based on part-of-speech (e.g.
        "read" as past vs present tense) that differs from CMUdict's [0]
    In both cases, get_alignment_for_word returns None (see below) and the
    caller should fall back to treating the whole word as one span rather
    than risk mismatched phoneme count vs. what the NW alignment actually
    scored -- see the fallback in the error_detection.py integration.

    Returns None if the word (or, for a hyphenated word, any sub-word) has
    no CMUdict entry (see fallback note above).
    """
    if '-' in word:
        return _get_alignment_for_hyphenated_word(word)

    arpabet = get_arpabet_for_word(word)
    if arpabet is None:
        return None
    return align_word(word.lower(), arpabet)


def _get_alignment_for_hyphenated_word(word):
    """
    Compound-word alignment: split `word` on '-', align each piece on its
    own, then stitch into one alignment covering the full hyphenated string
    (hyphens included in char positions, claimed by no phoneme -- same as
    how a space between two separate words claims no phoneme).
    """
    sub_words = word.split('-')
    if any(sw == '' for sw in sub_words):
        # leading/trailing/double hyphen (e.g. "-well-known", "well--known")
        # -- not a normal compound, don't guess.
        return None

    stitched_spans = []
    char_shift = 0       # running offset into the full hyphenated string
    phoneme_shift = 0    # running offset into the full phoneme index space

    for i, sub_word in enumerate(sub_words):
        arpabet = get_arpabet_for_word(sub_word)
        if arpabet is None:
            # Any sub-word missing from CMUdict -> can't build a reliable
            # compound alignment. Bail entirely rather than return partial
            # coverage (caller's phoneme-count check would likely catch a
            # partial result anyway, but bailing here is more explicit).
            return None

        sub_alignment = align_word(sub_word.lower(), arpabet)
        for start, end, idx in sub_alignment:
            stitched_spans.append((
                start + char_shift,
                end + char_shift,
                idx + phoneme_shift,
            ))

        char_shift += len(sub_word)
        if i < len(sub_words) - 1:
            char_shift += 1  # account for the hyphen character itself
        phoneme_shift += len(arpabet)

    return tuple(stitched_spans)


def alignment_matches_phoneme_count(alignment, expected_ipa_phoneme_count):
    """
    Sanity check: does this alignment's phoneme count match the number of
    IPA phonemes the CALLER'S pipeline actually produced for this word
    (i.e. from tp.text_to_ipa_phoneme, which is what NW actually scored)?

    If they don't match, the alignment is unusable for this word -- it would
    silently mislabel indices. Caller must fall back (see integration).
    """
    if alignment is None:
        return False
    max_idx = max((idx for _, _, idx in alignment), default=-1)
    return (max_idx + 1) == expected_ipa_phoneme_count