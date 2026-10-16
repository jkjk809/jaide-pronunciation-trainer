import numpy as np
import pickle
from panphon.distance import Distance
import panphon.featuretable
import re
import align_cache
# magic to default panphon to utf-8 encoding
# else it wont work on windows
panphon.featuretable.open = lambda fn, *args, **kwargs: open(fn, *args, encoding='utf-8', **kwargs)
# threshold which phonemes are considered slightly mispronounced
COST_THRESHOLD = 0.09

with open('res/dist_matrix.pkl', 'rb') as f:
    dist_matrix = pickle.load(f)

IPA_MAPPINGS = {
   # consonants
    'ð': 2, 'θ': 2, 'tʃ': 2, 'ʃ': 2, 'ŋ': 2,
    'ʒ': 2, 'dʒ': 2, 'j': 1, 'r': 1, 'l': 1,
    'w': 1, 'm': 1, 'n': 1, 'k': 1, 'g': 1, 'ɡ':1,
    'f': 1, 'v': 1, 's': 1, 'z': 1, 'p': 1,
    'b': 1, 't': 1, 'd': 1,
    # vowels
    'ɑ': 1, 'æ': 1, 'ə': 1, 'ɔ': 1, 'aʊ': 2,
    'aɪ': 2, 'ɛ': 1, 'ɝ': 2, 'eɪ': 2, 'ɪ': 1,
    'i': 1, 'oʊ': 2, 'ɔɪ': 2, 'ʊ': 1, 'u': 1
}

def needleman_wunsch_with_debug(target_phonemes, user_phonemes, 
                               match_reward=3, gap_penalty=-2, 
                               word_boundary_penalty=-2):
    """
    Needleman-Wunsch with special handling for word boundaries (spaces)
    with DEBUGGING. Change word_boundary to gap_penalty for no change
    
    Args:
        target_phonemes: List of target phonemes (including spaces)
        user_phonemes: List of user phonemes (including spaces)
        match_reward: Score for perfect matches
        gap_penalty: Standard gap penalty
        word_boundary_penalty: Higher penalty for gaps at word boundaries
    """

    # NOTE: this uses word_boundary penalty and will
    #      probably be deprecated as it doesn't really work
    #
    print("\n========== STARTING NEEDLEMAN-WUNSCH ALIGNMENT ==========")
    print(f"TARGET: {target_phonemes}")
    print(f"USER: {user_phonemes}")
    print(f"Parameters: match_reward={match_reward}, gap_penalty={gap_penalty}, word_boundary_penalty={word_boundary_penalty}")
    
    dist = Distance()
    m, n = len(target_phonemes), len(user_phonemes)
    
    score = np.zeros((m+1, n+1), dtype=float)
    
    traceback = np.zeros((m+1, n+1), dtype=int)
    # 0: diagonal, 1: up (deletion), 2: left (insertion)
    
    #print("\n--- INITIALIZING MATRICES ---")
    for i in range(1, m+1):
        penalty = word_boundary_penalty if target_phonemes[i-1] == ' ' else gap_penalty
        score[i, 0] = score[i-1, 0] + penalty
        traceback[i, 0] = 1
       # print(f"Row {i} ('{target_phonemes[i-1]}'): score={score[i, 0]}, traceback={traceback[i, 0]}")
    
    for j in range(1, n+1):
        penalty = word_boundary_penalty if user_phonemes[j-1] == ' ' else gap_penalty
        score[0, j] = score[0, j-1] + penalty
        traceback[0, j] = 2
      #  print(f"Col {j} ('{user_phonemes[j-1]}'): score={score[0, j]}, traceback={traceback[0, j]}")
    
   # print("\n--- INITIAL MATRIX ---")
   # print_matrix(score, target_phonemes, user_phonemes)
    
   # print("\n--- FILLING MATRICES ---")
    for i in range(1, m+1):
        for j in range(1, n+1):
            target_is_space = target_phonemes[i-1] == ' '
            user_is_space = user_phonemes[j-1] == ' '
            #print(f"\nProcessing cell [{i},{j}]: Target '{target_phonemes[i-1]}', User '{user_phonemes[j-1]}'")
            # MISMATCH/MATCH
            if target_is_space and user_is_space:
                # space-to-space is a perfect match
                diag_score = score[i-1, j-1] + match_reward
               # print(f"  Both spaces: diag_score = {score[i-1, j-1]} + {match_reward} = {diag_score}")
            elif not target_is_space and not user_is_space:
                # Regular phoneme comparison using feature distance
                feature_dist = dist.feature_edit_distance(target_phonemes[i-1], user_phonemes[j-1])
                similarity = (1 - feature_dist) * match_reward
                diag_score = score[i-1, j-1] + similarity
               # print(f"  Phoneme comparison: feature_dist={feature_dist}, similarity={similarity}")
               # print(f"  diag_score = {score[i-1, j-1]} + {similarity} = {diag_score}")
            else:
                # space-to-phoneme mismatch is penalized
                diag_score = score[i-1, j-1] + word_boundary_penalty
                #print(f"  Space-phoneme mismatch: diag_score = {score[i-1, j-1]} + {word_boundary_penalty} = {diag_score}")
            
            # Calculate up and left scores (gaps)
            # Use special penalty if the current position is a space
            up_penalty = word_boundary_penalty if target_is_space else gap_penalty
            left_penalty = word_boundary_penalty if user_is_space else gap_penalty
            
            up_score = score[i-1, j] + up_penalty
            left_score = score[i, j-1] + left_penalty
            
           # print(f"  up_score = {score[i-1, j]} + {up_penalty} = {up_score}")
            #print(f"  left_score = {score[i, j-1]} + {left_penalty} = {left_score}")
            
            # Choose the best move
            best_scores = [diag_score, up_score, left_score]
            best_move = np.argmax(best_scores)
            
            # Update matrices
            score[i, j] = best_scores[best_move]
            traceback[i, j] = best_move
            
            move_names = ["diagonal", "up", "left"]
            #print(f"  Best move: {move_names[best_move]} with score {score[i, j]}")
    

    print("\n--- FINAL SCORE MATRIX ---")
    print_matrix(score, target_phonemes, user_phonemes)
    
    print("\n--- FINAL TRACEBACK MATRIX ---")
    print_traceback_matrix(traceback, target_phonemes, user_phonemes)
    
    #print("\n--- TRACEBACK ALIGNMENT ---")
    mispronounced_indices = {}
    i, j = m, n
    target_idx = m - 1
    
    # Define constants
    COST_THRESHOLD = 0.09
    
    alignment_target = []
    alignment_user = []
    alignment_status = []
    
    while i > 0 or j > 0:
        #print(f"At position [{i},{j}], target_idx={target_idx}")
        
        if i > 0 and j > 0 and traceback[i, j] == 0:  # diagonal (match or substitution)
            #print(f"  Diagonal move: comparing '{target_phonemes[i-1]}' and '{user_phonemes[j-1]}'")
            
            if not (target_phonemes[i-1] == ' ' and user_phonemes[j-1] == ' '):
                if target_phonemes[i-1] != ' ' and user_phonemes[j-1] != ' ':
                    feature_dist = dist.feature_edit_distance(target_phonemes[i-1], user_phonemes[j-1])
                   # print(f"  Feature distance: {feature_dist}")
                    
                    if feature_dist > 0:  # substitution error
                        severity = 'partial' if feature_dist <= COST_THRESHOLD else 'incorrect'
                        mispronounced_indices[target_idx] = severity
                       # print(f"  Marked as {severity} at index {target_idx}")
                        alignment_status.append(severity)
                    else:
                        alignment_status.append("correct")
                elif target_phonemes[i-1] != user_phonemes[j-1]:  # one is space, one is not
                    mispronounced_indices[target_idx] = "incorrect"
                   # print(f"  Space mismatch: marked as incorrect at index {target_idx}")
                    alignment_status.append("incorrect")
                else:
                    alignment_status.append("correct")
            else:
                alignment_status.append("space")
                
            alignment_target.append(target_phonemes[i-1])
            alignment_user.append(user_phonemes[j-1])
            
            i -= 1
            j -= 1
            target_idx -= 1
            
        elif i > 0 and traceback[i, j] == 1:  # up (deletion)
           #print(f"  Up move (deletion): '{target_phonemes[i-1]}' is missing in user input")
            # missing phoneme in user pronunciation
            if target_phonemes[i-1] != ' ': 
                mispronounced_indices[target_idx] = "incorrect"
                #print(f"  Marked as incorrect at index {target_idx}")
                alignment_status.append("deletion")
            else:
                alignment_status.append("space")
                
            alignment_target.append(target_phonemes[i-1])
            alignment_user.append("-")
            
            i -= 1
            target_idx -= 1
            
        else:  # left (insertion)
            #print(f"  Left move (insertion): '{user_phonemes[j-1]}' is extra in user input")

            if target_idx >= 0 and target_idx < len(target_phonemes) and target_phonemes[target_idx] != ' ':
                mispronounced_indices[target_idx] = "incorrect"
                #print(f"  Marked current index {target_idx} as incorrect")
            
            if target_idx + 1 < len(target_phonemes) and target_phonemes[target_idx + 1] != ' ':
                mispronounced_indices[target_idx + 1] = "incorrect"
                #print(f"  Marked next index {target_idx + 1} as incorrect")
                
            alignment_target.append("-")
            alignment_user.append(user_phonemes[j-1])
            alignment_status.append("insertion")
            
            j -= 1
    
    alignment_target.reverse()
    alignment_user.reverse()
    alignment_status.reverse()
    
    print("\n--- FINAL ALIGNMENT ---")
    print("Target: ", " ".join(alignment_target))
    print("User:   ", " ".join(alignment_user))
    print("Status: ", " ".join(alignment_status))
    
    matched_count = sum(1 for i in range(len(target_phonemes)) 
                       if target_phonemes[i] != ' ' and i not in mispronounced_indices)
    total_phonemes = sum(1 for p in target_phonemes if p != ' ')
    accuracy = (matched_count / total_phonemes) * 100 if total_phonemes > 0 else 100
    
    print(f"\nAccuracy: {accuracy:.2f}% ({matched_count}/{total_phonemes} phonemes correct)")
    print(f"Mispronounced indices: {mispronounced_indices}")
    
    return mispronounced_indices, accuracy

def print_matrix(matrix, target_phonemes, user_phonemes):
    #### DEBUGGNG ####
    m, n = len(target_phonemes), len(user_phonemes)
    
    header = "     "
    for j in range(n):
        phoneme = user_phonemes[j]
        header += f"{phoneme:^5}"
    print(header)
    
    for i in range(m+1):
        if i == 0:
            row = "   |"
        else:
            row = f" {target_phonemes[i-1]} |"
        
        for j in range(n+1):
            row += f"{matrix[i,j]:5.2f}"
        print(row)

def print_traceback_matrix(matrix, target_phonemes, user_phonemes):
    #### DEBUGGING ####
    m, n = len(target_phonemes), len(user_phonemes)
    moves = {0: "diag", 1: "up", 2: "left"}
 
    header = "     "
    for j in range(n):
        phoneme = user_phonemes[j]
        header += f"{phoneme:^5}"
    print(header)
    for i in range(m+1):
        if i == 0:
            row = "   |"
        else:
            row = f" {target_phonemes[i-1]} |"
        
        for j in range(n+1):
            move = moves[matrix[i,j]]
            row += f"{move:^5}"
        print(row)

def split_phonemes(phonemes):
    """
    Split a list of phonemes into words based on spaces.
    
    Args:
    -----
        phonemes (list): List of phonemes with spaces between words
                            e.g., ['ð', 'ə', ' ', 'k', 'æ', 't']
                        
    Returns:
    --------
        list: List of phoneme lists, where each sublist corresponds to a word
                e.g., [['ð', 'ə'], ['k', 'æ', 't']]
    """
    words = []
    current_word = []
    for phoneme in phonemes:
        if phoneme == ' ':
            words.append(current_word)
            current_word = []
        else:
            current_word.append(phoneme)
    words.append(current_word)
    return words


def get_phoneme_index_in_word(phonemes, global_index):
    """
    Get the relative index of a phoneme within its word.
    
    Args:
    -----
        phonemes (list): Complete phoneme list
        global_index (int): Global index in the list
        
    Returns:
    --------
        int: Relative index within the word
    """
    word_start = global_index
    while word_start > 0 and phonemes[word_start-1] != ' ':
        word_start -= 1
    return global_index - word_start

def get_word_start_position(phrase, word_index):
    """
    Get the character position where a word starts in the phrase.
    
    Args:
    -----
        phrase (str): Original phrase
        word_idx (int): Index of the word
        
    Returns:
    --------
        int: Character position where the word starts
    """
    words = phrase.split()
    position = 0
    
    for i in range(word_index):
        if i < len(words):
            position += len(words[i]) + 1  # +1 for space
    
    return position

def needleman_wunsch(target_phonemes, user_phonemes, match_reward=3, gap_penalty=-2):
    """
    Needleman-Wunsch algorithm for sequence alignment
    
    Args:
        target_phonemes: List of target phonemes
        user_phonemes: List of user phonemes
        match_reward: Score for perfect matches
        gap_penalty: Standard gap penalty
    """
    dist = Distance()

    feature_edit_distance = dist.weighted_feature_edit_distance(target_phonemes, user_phonemes)
    max_possible_distance = dist.weighted_feature_edit_distance(target_phonemes, "")
    accuracy =  (1 - (feature_edit_distance / max_possible_distance)) * 100

    m, n = len(target_phonemes), len(user_phonemes)

    score = np.zeros((m+1, n+1), dtype=float)

    traceback = np.zeros((m+1, n+1), dtype=int)
    # 0: diagonal, 1: up (deletion), 2: left (insertion)
    
    # init first row/col
    for i in range(1, m+1):
        score[i, 0] = score[i-1, 0] + gap_penalty
        traceback[i, 0] = 1

    for j in range(1, n+1):
        score[0, j] = score[0, j-1] + gap_penalty
        traceback[0, j] = 2
    
    
    # fill matrix
    for i in range(1, m+1):
        for j in range(1, n+1):
            if target_phonemes[i-1] == user_phonemes[j-1]:
                diag_score = score[i-1, j-1] + match_reward
            else:
                feature_dist = dist_matrix[(target_phonemes[i-1], user_phonemes[j-1])]
                # scale similarity acc to match reward
                similarity = (1 - feature_dist) * match_reward
                diag_score = score[i-1, j-1] + similarity
            # up and left scores (gaps)
            up_score = score[i-1, j] + gap_penalty
            left_score = score[i, j-1] + gap_penalty
            
            best_scores = [diag_score, up_score, left_score]
            best_move = np.argmax(best_scores)
            score[i, j] = best_scores[best_move]
            traceback[i, j] = best_move
    
    # traceback to find mispronounced indices
    mispronounced_indices = {}
    i, j = m, n
    target_idx = m - 1
    while i > 0 or j > 0:
        if i > 0 and j > 0 and traceback[i, j] == 0:  # diagonal (match or substitution)
            feature_dist = dist_matrix[(target_phonemes[i-1], user_phonemes[j-1])]
            if feature_dist > 0:
                severity = 'partial' if feature_dist <= COST_THRESHOLD else 'incorrect'
                mispronounced_indices[target_idx] = severity
            i -= 1
            j -= 1
            target_idx -= 1
        
        elif i > 0 and traceback[i, j] == 1:  # up (deletion)
            # Missing phoneme in user pronunciation
            mispronounced_indices[target_idx] = "incorrect"
            i -= 1
            target_idx -= 1
            
        else:  # left (insertion)
            # i knda forgpt why i did this but its important
            if target_idx >= 0 and target_idx < len(target_phonemes):
                mispronounced_indices[target_idx] = "incorrect"
            if target_idx + 1 < len(target_phonemes):
                mispronounced_indices[target_idx + 1] = "incorrect"
            j -= 1

    return mispronounced_indices, accuracy
    
def get_pronunciation_score(target_phrase, target_phonemes, user_phonemes, user_words, target_words):
    """
    Get pronunciation score and error info for a target phrase and user phonemes,
    handling different word counts by comparing entire phoneme sequences.
    
    Args:
    -----
        target_phrase (str): Original text phrase (e.g., "the cat")
        target_phonemes (list): List of target IPA phonemes with spaces (e.g., ['ð', 'ə', ' ', 'k', 'æ', 't'])
        user_phonemes (list): List of user's spoken IPA phonemes with spaces (e.g., ['d', 'ə', ' ', 'k', 'æ', 't'])
        
    Returns:
    --------
        dict: Dictionary containing pronunciation feedback information 
    """

    # NOTE:
    # trust process 💀
    error_info = {
        'accuracy': 0, # advanced accuracy metric!
        'incorrect_indices': [], # global character indices for highlighting
        'phoneme_indices': [], # global phoneme indices for highlighting
        'word_feedback': [] # phonemes and start/end positions for all words
    }  
    #user doesnt try
    if (abs(len(target_words) - len(user_words)) >= 4):
        mispronounced_indices = {
            i: 'incorrect'
            for i, phoneme in enumerate(target_phonemes)
            if phoneme != ' '
        }
        error_info['accuracy'] = 0.0
    else:
        # phoneme indices with severity mapping
        mispronounced_indices, error_info['accuracy'] = needleman_wunsch(target_phonemes, user_phonemes)
    
    # split target phrase into words and phonemes into word sublists
    target_word_phonemes = split_phonemes(target_phonemes)
    # clean punctuation (hyphen and apostrophe preserved -- see note in
    # text_processing.text_to_phoneme for why hyphen must survive: dropping
    # it shrinks a hyphenated word by 1+ characters and desyncs every
    # downstream character-position calculation for the rest of the phrase)
    original_words = re.sub(r"[^\w\s'-]", '', target_phrase).split()
    
    ######### POPULATE WORD_FEEDBACK ###########
    phoneme_index = 0
    for word_index, word in enumerate(original_words):
        # get words character positions
        # count the characters to get to word index
        word_start_pos = get_word_start_position(target_phrase, word_index)
        word_end_pos = word_start_pos + len(word) 
        
        word_phonemes = target_word_phonemes[word_index]
        word_data = {
            'word': word,
            'char_start_index': word_start_pos,
            'char_end_index': word_end_pos,
            'phonemes': []
        }
        # populate phoneme list with a mapping of 
        # phonemes and severity
        for phoneme in word_phonemes:
            severity = mispronounced_indices.get(phoneme_index, "correct")
            word_data['phonemes'].append({
                'phoneme': phoneme,
                'severity': severity
            })
            phoneme_index +=1
        phoneme_index+=1 # space
        error_info['word_feedback'].append(word_data)
    
    ####### GLOBAL CHARACTER INDICES ########

    # phoneme to word mapping
    phoneme_to_word_map = {}
    word_index = 0
    for i, phoneme in enumerate(target_phonemes):
        if phoneme == ' ':
            word_index += 1
        else:
            phoneme_to_word_map[i] = word_index
    
    # grab mispronounced phonemes
    #
    # CHAR SPAN LOOKUP: for each word, try to get a REAL letter<->phoneme
    # alignment (which letters actually produced this phoneme) rather than
    # guessing a fixed width per phoneme. IPA_MAPPINGS-based guessing is kept
    # ONLY as a fallback for words the aligner can't handle (see
    # alignment_matches_phoneme_count docstring for exactly when that is --
    # OOV words or homograph pronunciation mismatches, both rare).
    #
    # word_alignment_cache: word_index -> alignment spans (or None if this
    # word must fall back to the old fixed-width behavior). Built lazily,
    # once per word actually referenced below, not for every word up front.
    word_alignment_cache = {}

    def get_word_alignment(word_index, word_phonemes_ipa):
        """
        Returns alignment spans for word at word_index, or None if this word
        must use the IPA_MAPPINGS fallback. word_phonemes_ipa is this word's
        own IPA phoneme list (used only to sanity-check phoneme count).
        """
        if word_index in word_alignment_cache:
            return word_alignment_cache[word_index]

        word_text = error_info['word_feedback'][word_index]['word']
        alignment = align_cache.get_alignment_for_word(word_text)

        if not align_cache.alignment_matches_phoneme_count(alignment, len(word_phonemes_ipa)):
            # OOV word, or CMUdict's [0] pronunciation doesn't match the
            # phoneme count g2p_en actually produced for this word (e.g. a
            # homograph resolved differently) -- can't trust this alignment,
            # must fall back for this word specifically.
            alignment = None

        word_alignment_cache[word_index] = alignment
        return alignment

    for phoneme_index, severity in mispronounced_indices.items():

        phoneme = target_phonemes[phoneme_index]
        if phoneme == ' ':
            continue
        # word this phoneme belongs to
        word_index = phoneme_to_word_map.get(phoneme_index, 0)
        word_start_pos = error_info['word_feedback'][word_index]['char_start_index']

        # phoneme index within the word (used both as fallback input AND as
        # the index into this word's own phoneme list for the aligner)
        relative_phoneme_index = get_phoneme_index_in_word(target_phonemes, phoneme_index)

        word_phonemes_ipa = target_word_phonemes[word_index]
        alignment = get_word_alignment(word_index, word_phonemes_ipa)

        if alignment is not None:
            # REAL alignment path: find the char span for this exact phoneme
            # index within its word. A phoneme can map to 0, 1, or several
            # letters (e.g. 'u'->"oo" in fool), and in rare shared-letter
            # cases (e.g. 'x'->K+S) two DIFFERENT phoneme indices can map to
            # the SAME letter -- that's intentional, not a bug: both
            # phonemes really are spelled by that one letter.
            matched_spans = [
                (start, end) for start, end, idx in alignment
                if idx == relative_phoneme_index
            ]
            for start, end in matched_spans:
                for char_offset_in_span in range(start, end):
                    global_char_pos = word_start_pos + char_offset_in_span
                    error_info['incorrect_indices'].append((global_char_pos, severity))
        else:
            # FALLBACK: original fixed-width guess, unchanged, for words the
            # aligner couldn't confidently handle.
            char_offset = 0
            for i in range(phoneme_index - relative_phoneme_index, phoneme_index):
                if i >= 0 and i < len(target_phonemes) and target_phonemes[i] != ' ':
                    char_offset += IPA_MAPPINGS.get(target_phonemes[i], 1)

            phoneme_length = IPA_MAPPINGS.get(phoneme, 1)
            for j in range(phoneme_length):
                global_char_pos = word_start_pos + char_offset + j
                error_info['incorrect_indices'].append((global_char_pos, severity))
    
    ###### GLOBAL PHONEME INDICES #######
    error_info['phoneme_indices'] = [(index, sev) for index, sev in mispronounced_indices.items()]
    
    return error_info

# EXAMPLE #
def test_alignment():
    from panphon.distance import Distance
    import numpy as np
    import text_processing as tp
    
    target = "the, quick. brown.. fox!"
    user = "yuh quick brown fox"

    target_phonemes = tp.text_to_ipa_phoneme(target)
    user_phonemes = tp.text_to_ipa_phoneme(user)

    #target_phonemes = ['ð', 'ʌ', ' ', 'k', 'w', 'ɪ', 'k', ' ', 'b', 'ɹ', 'aʊ', 'n', ' ', 'f', 'ɑ', 'k', 's']
    #user_phonemes = ['j', 'ʌ', ' ', 'k', 'w', 'ɪ', 'k', ' ', 'b', 'ɹ', 'aʊ', 'n', ' ', 'f', 'ɑ', 'k', 's']
    print(user)
    ### you can uncomment the print statements but this is final result
    needleman_wunsch_with_debug(target_phonemes, user_phonemes)

    score = get_pronunciation_score(target, target_phonemes, user_phonemes)
    #print(score['phoneme_indices'])
    print(score)

if __name__ == "__main__":
    test_alignment()