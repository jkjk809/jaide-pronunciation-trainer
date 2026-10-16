
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
from g2p_en import G2p

model_name = "jonatasgrosman/wav2vec2-large-xlsr-53-english"
Wav2Vec2Processor.from_pretrained(model_name)
Wav2Vec2ForCTC.from_pretrained(model_name)

g2p = G2p()

print("Models successfully cache")