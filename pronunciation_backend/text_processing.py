from g2p_en import G2p
import re

# this module holds text processing functions
# IMPORTANT: removed eng_to_ipa because it does not correctly map.
#            to simplify building application for users i use g2p then map arpabet to ipa

# dont delete this pls
def text_to_phoneme(text):
    # clean text for processing
    text = re.sub(r"[^\w\s'-]", '', text)
    g2p = G2p()
    phonemes = g2p(text)
    #remove stress markers of phonetic representation
    return [re.sub(r'\d+', '', phoneme) for phoneme in phonemes]

ARPA_TO_IPA = {
    "AA": "ɑ", "AE": "æ", "AH": "ʌ", "AO": "ɔ", "AW": "aʊ", "AY": "aɪ",
    "B": "b", "CH": "tʃ", "D": "d", "DH": "ð", "EH": "ɛ", "ER": "ɝ",
    "EY": "eɪ", "F": "f", "G": "ɡ", "HH": "h", "IH": "ɪ", "IY": "i",
    "JH": "dʒ", "K": "k", "L": "l", "M": "m", "N": "n", "NG": "ŋ",
    "OW": "oʊ", "OY": "ɔɪ", "P": "p", "R": "ɹ", "S": "s", "SH": "ʃ",
    "T": "t", "TH": "θ", "UH": "ʊ", "UW": "u", "V": "v", "W": "w",
    "Y": "j", "Z": "z", "ZH": "ʒ"
}


def text_to_ipa_phoneme(text):
    arpabet_phonemes = text_to_phoneme(text)
    # convert to IPA
    ipa_phonemes = []
    for phoneme in arpabet_phonemes:
        if phoneme in ARPA_TO_IPA:
            ipa_phonemes.append(ARPA_TO_IPA[phoneme])
        elif phoneme == ' ':
            ipa_phonemes.append(' ')

    return ipa_phonemes
 

if __name__ == "__main__":
    text = "dog, there."    
    phoneme_output = text_to_ipa_phoneme(text)
    print("IPA:", phoneme_output)