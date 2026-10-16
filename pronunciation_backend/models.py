import os
os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
import numpy as np
import torch
import librosa 
import threading
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
# currently reads audio file. ok for now
def load_audio(audio_path, sample_rate):
    audio_input, sr = librosa.load(audio_path, sr=sample_rate)
    return audio_input

def play_tts(text):
    """Generate and play TTS of the target phrase."""
    def _play():
        tts_filename = "tts_output.mp3"
        tts = gTTS(text)
        tts.save(tts_filename)

        audio = AudioSegment.from_file(tts_filename, format="mp3")
        play(audio)

    threading.Thread(target=_play, daemon=True).start() # avoid freezing main ui thread

#### DELETE PHONEME MODEL FOR STORAGE ####
# this model might get thrown but i need further testing with whisper
# Whisper model is core to chat bot
class STTModel:
    def __init__(self, model_name="jonatasgrosman/wav2vec2-large-xlsr-53-english", sample_rate=16000):
        from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

        self.processor = Wav2Vec2Processor.from_pretrained(model_name)
        self.model = Wav2Vec2ForCTC.from_pretrained(model_name)
        self.sample_rate = sample_rate
        self.device = torch.device(
            'cuda' if torch.cuda.is_available() 
            else 'mps' if torch.backends.mps.is_available() 
            else 'cpu'
        )
        self.device = torch.device('cpu')
        print(f"Using device: {self.device} for speech recognition")
        self.model.to(self.device)
        
    def transcribe(self, audio_path):
        try:
            print(f"Starting transcription of {audio_path}...")
            if not os.path.exists(audio_path):
                print(f"Error: Audio file {audio_path} does not exist!")
                return ""
                
            # Check file size
            file_size = os.path.getsize(audio_path)
            print(f"Audio file size: {file_size} bytes")
            if file_size < 100:
                print("Warning: Audio file is too small, may be empty")
                return ""
                
            audio_input = load_audio(audio_path, self.sample_rate)
            print(f"Audio loaded, shape: {audio_input.shape}, max value: {np.max(np.abs(audio_input))}")
            
            input_values = self.processor(audio_input, return_tensors="pt", sampling_rate=self.sample_rate).input_values
            input_values = input_values.to(self.device)
            
            with torch.no_grad():
                logits = self.model(input_values).logits
            predicted_ids = torch.argmax(logits, dim=-1)
            transcription = self.processor.decode(predicted_ids[0])
            
            print(f"Transcription result: '{transcription}'")
            return transcription
        except Exception as e:
            print(f"Error during transcription: {str(e)}")
            import traceback
            traceback.print_exc()
            return ""

stt_model = STTModel()