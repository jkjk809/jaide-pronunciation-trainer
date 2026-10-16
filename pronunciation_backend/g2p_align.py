from functools import lru_cache
PHONEME_TO_GRAPHEMES = {
    "F": {"f", "ff", "ph", "gh"},
    "K": {"k", "c", "ck", "ch", "q", "qu", "x"},
    "S": {"s", "ss", "c", "ce", "sc"},
    "Z": {"z", "s", "zz", "x"},
    "T": {"t", "tt", "ed"},
    "D": {"d", "dd", "ed"},
    "N": {"n", "nn", "kn", "gn", "pn"},
    "M": {"m", "mm", "mb", "mn"},
    "L": {"l", "ll"},
    "R": {"r", "rr", "wr", "rh"},
    "W": {"w", "wh", "u", "o"},
    "Y": {"y", "i", "u"},
    "HH": {"h", "wh"},
    "B": {"b", "bb"},
    "P": {"p", "pp"},
    "G": {"g", "gg", "gh", "gu"},
    "JH": {"j", "g", "dg", "dge"},
    "CH": {"ch", "tch", "t"},
    "SH": {"sh", "ti", "ci", "ssi", "s"},
    "ZH": {"si", "s", "z", "g"},
    "TH": {"th"},
    "DH": {"th"},
    "V": {"v", "f", "ph"},
    "NG": {"ng", "n"},
    "AA": {"a", "o", "au", "aa"},
    "AE": {"a"},
    "AH": {"a", "e", "i", "o", "u", "ou", "ough"},
    "AO": {"o", "au", "aw", "a", "ough"},
    "AW": {"ow", "ou"},
    "AY": {"i", "y", "ie", "igh", "y", "eigh", "ai"},
    "EH": {"e", "ea", "a"},
    "ER": {"er", "ir", "ur", "or", "ear", "olo", "ar"},
    "EY": {"a", "ay", "ai", "ey", "eigh", "ea"},
    "IH": {"i", "y", "e"},
    "IY": {"e", "ee", "ea", "ie", "y", "ey", "i"},
    "OW": {"o", "oa", "ow", "oe", "ough", "eau", "ou"},
    "OY": {"oy", "oi"},
    "UH": {"oo", "u", "ou"},
    "UW": {"oo", "u", "ue", "ew", "ough", "o", "u_e", "eu"},
}

SILENT_LETTERS = {"e", "h", "k", "g", "b", "w", "u", "gh"}
 
MAX_GRAPHEME_LEN = 4
 

LETTER_TO_PHONEME_PAIR = {
    "x": {("K", "S"), ("G", "Z")},
    "u": {("Y", "UW")}, 
}
 
 
def _strip_stress(phoneme):
    return "".join(c for c in phoneme if not c.isdigit())
 
 
def _grapheme_score(letters_chunk, phoneme_base):
    chunk = letters_chunk.lower()
    graphemes = PHONEME_TO_GRAPHEMES.get(phoneme_base, set())
    if chunk in graphemes:
        return 10 + len(chunk)
    if len(chunk) == 1 and chunk in graphemes:
        return 8
    return -5 * len(chunk)
 
 
def _silent_bonus(letters_chunk):
    return 3 if letters_chunk.lower() in SILENT_LETTERS else 0
 
 
@lru_cache(maxsize=4096)
def align_word(word, phoneme_tuple):
    word = word.lower()
    phonemes = list(phoneme_tuple)
    n_chars = len(word)
    n_ph = len(phonemes)
 
    if n_ph == 0:
        return tuple()
    if n_ph == 1:
        return ((0, n_chars, 0),)
 
    phoneme_bases = [_strip_stress(p) for p in phonemes]
 
    NEG_INF = float("-inf")
    dp = [[NEG_INF] * (n_ph + 1) for _ in range(n_chars + 1)]
    choice = [[None] * (n_ph + 1) for _ in range(n_chars + 1)]
    dp[0][0] = 0.0
 
    def pair_bonus(chunk, base_a, base_b):
        pairs = LETTER_TO_PHONEME_PAIR.get(chunk.lower())
        if pairs and (base_a, base_b) in pairs:
            return 12  
        return None  
 
    for k in range(1, n_ph + 1):
        phoneme_base = phoneme_bases[k - 1]
        for i in range(1, n_chars + 1):
            best_score = NEG_INF
            best_choice = None
            max_take = min(MAX_GRAPHEME_LEN, i)
            for take in range(1, max_take + 1):
                prev = dp[i - take][k - 1]
                if prev == NEG_INF:
                    continue
                chunk = word[i - take:i]
                score = prev + _grapheme_score(chunk, phoneme_base) + _silent_bonus(chunk)
                if score > best_score:
                    best_score = score
                    best_choice = (take, "single")
 
            if k >= 2:
                prev_base = phoneme_bases[k - 2]
                max_take_pair = min(2, i) 
                for take in range(1, max_take_pair + 1):
                    prev = dp[i - take][k - 2]
                    if prev == NEG_INF:
                        continue
                    chunk = word[i - take:i]
                    bonus = pair_bonus(chunk, prev_base, phoneme_base)
                    if bonus is None:
                        continue
                    score = prev + bonus
                    if score > best_score:
                        best_score = score
                        best_choice = (take, "pair")
 
            dp[i][k] = best_score
            choice[i][k] = best_choice
 
    spans = []
    i, k = n_chars, n_ph
    while k > 0:
        move = choice[i][k]
        if move is None:
            move = (1, "single")
        take, move_type = move
        if move_type == "single":
            spans.append((i - take, i, k - 1))
            i -= take
            k -= 1
        else: 
            spans.append((i - take, i, k - 1))
            spans.append((i - take, i, k - 2))
            i -= take
            k -= 2
 
    spans.reverse()
    return tuple(spans)
 
 
def get_char_span_for_phoneme(word, phoneme_tuple, phoneme_index):
    spans = align_word(word, phoneme_tuple)
    for start, end, idx in spans:
        if idx == phoneme_index:
            return (start, end)
    return None
 