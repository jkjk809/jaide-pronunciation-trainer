import os
import json
import random
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import text_processing as tp
import error_detection as ed
import models as md
import edge_tts
import tempfile
from models import stt_model
from fastapi.responses import StreamingResponse

import ssl
import nltk

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

print("Initializing NLTK dependencies...")
nltk.download('punkt')
nltk.download('cmudict')
nltk.download('averaged_perceptron_tagger_eng')
print("NLTK assets initialized successfully.")

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
with open('res/sentences.json', 'r') as f:
    SENTENCES = json.load(f)


@app.get("/get_sentence")
def get_sentence():
    try:
        sentences = [entry["sentence"] for entry in SENTENCES["data"]]
        random_sentence = random.choice(sentences)
        #random_sentence = "The great big day was ahead of him, so therefore. took away the apples fool. through knight colonel there's well-here"
        random_sentence_phonemes = tp.text_to_ipa_phoneme(random_sentence)
        return {"sentence": random_sentence, "sentence_phonemes": random_sentence_phonemes}
    except Exception as e:
        print(f"Error in get_sentence: {str(e)}")
        return "Error loading sentence from backend"

@app.post("/score")
async def score_pronunciation(file: UploadFile = File(...), current_text: str = Form(...)):
    file_path = None
    try:
        audio_bytes = await file.read()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            file_path = f.name        

        user_text = stt_model.transcribe(file_path)
        print("Transcription: ", user_text)

        user_phonemes = tp.text_to_ipa_phoneme(user_text)
        print("Phonemes: ", user_phonemes)

        target_words = current_text.split()
        user_words = user_text.split()

        current_phoneme = tp.text_to_ipa_phoneme(current_text)
        error_info = ed.get_pronunciation_score(current_text, current_phoneme, user_phonemes, user_words, target_words)
        
        if os.path.exists(file_path):
            os.remove(file_path)

        return {
            "status": "success",
            "accuracy": error_info['accuracy'],
            "incorrect_indices": error_info['incorrect_indices'],
            "phoneme_indices": error_info['phoneme_indices'],
            "word_feedback": error_info['word_feedback']
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

@app.get("/tts")
async def tts(text: str, voice: str = "en-US-AriaNeural"):   
    tts = edge_tts.Communicate(text, voice)
    async def stream():                                          
        async for chunk in tts.stream():                 
            if chunk["type"] == "audio":
                yield chunk["data"]
    return StreamingResponse(stream(), media_type="audio/mpeg")
