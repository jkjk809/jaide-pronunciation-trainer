FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y ffmpeg libportaudio2 libsndfile1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --no-compile torch
RUN pip install --no-cache-dir --no-compile transformers numpy scipy
RUN pip install --no-cache-dir --no-compile fastapi uvicorn python-multipart librosa sounddevice gTTS pydub g2p_en panphon edge_tts

COPY download_models.py .
RUN python download_models.py

COPY . .

EXPOSE 7860

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]