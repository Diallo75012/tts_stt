"""
import sounddevice as sd
import numpy as np
import tempfile
import os
from scipy.io.wavfile import write
import pyttsx3
import threading
from faster_whisper import WhisperModel

# Initialize Whisper model
# whisper_model = WhisperModel(model_size_or_path="base.en")
model = "base.en"
whisper_compute_type = "int8"
whisper = WhisperModel(
  model,
  device="auto",
  compute_type=whisper_compute_type
)

# Initialize text-to-speech
tts_engine = pyttsx3.init()
print(tts_engine.getProperty('voices'))
# Set female voice engine.setProperty('voice', 'english_rp+f3') OR engine.setProperty('voice', 'f1+f4')
tts_engine.setProperty('voice', 'english+f4')
def record_audio_to_file(duration=10, sample_rate=44100):
    # Record audio from the microphone and save to a temporary file.
    print("Recording...")
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
    sd.wait()  # Wait until the recording is finished
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    write(temp_file.name, sample_rate, recording)  # Save the recording
    return temp_file.name

def transcribe_audio(audio_file):
    # Transcribe speech from an audio file using Faster Whisper.
    result = whisper.transcribe(audio_file)
    print("Transribe audio Result: ", result)
    text = ""
    for segment in result[0]:
        print("Segment: ", segment)
        text += segment.text + " "
    return text

def speak(text):
    # Convert text to speech.
    tts_engine.say(text)
    tts_engine.runAndWait()

def continuous_listen():
    # Continuously listen for the start and stop words.
    while True:
        audio_file = record_audio_to_file(duration=5)  # Listen for 5 seconds
        transcription = transcribe_audio(audio_file)
        print(f"Transcribed: {transcription}")  # Print transcription for debugging
        os.unlink(audio_file)  # Clean up the temporary file

        if "hello computer" in transcription.lower():
            speak("Start word detected. I'm listening.")
            audio_file = record_audio_to_file()  # Record for a longer duration upon activation
            transcription = transcribe_audio(audio_file)
            print(f"I heard: {transcription}")
            os.unlink(audio_file)  # Clean up the temporary file after transcription
            speak(f"I heard: {transcription}")

        elif "thank you computer" in transcription.lower():
            speak("Stop word detected. Goodbye.")
            break  # Exit the loop and end the program

if __name__ == "__main__":
    speak("I am ready to chat.")
    continuous_listen()


""" 
# LMSTUDIO CONNECTED VERSION
import requests
import tempfile
import os
from scipy.io.wavfile import write
import sounddevice as sd
import pyttsx3
import threading
from faster_whisper import WhisperModel
from openai import OpenAI
import json

# Point to the local server
client = OpenAI(base_url="http://localhost:1235/v1", api_key="not-needed")

# Initialize Whisper model and text-to-speech engine
# whisper_model = WhisperModel()
model = "base.en"
whisper_compute_type = "int8"
whisper = WhisperModel(
  model,
  device="auto",
  compute_type=whisper_compute_type
)
tts_engine = pyttsx3.init()
# Set to use a female voice
# tts_engine.setProperty('voice', tts_engine.getProperty('voices')[1].id)
tts_engine.setProperty('voice', 'english+f4') 

def record_audio_to_file(duration=10, sample_rate=44100):
    # Record audio and save to a temporary file.
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
    sd.wait()
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    write(temp_file.name, sample_rate, recording)
    return temp_file.name

def transcribe_audio(audio_file):
    # Transcribe speech from an audio file using Faster Whisper.
    result = whisper.transcribe(audio_file)
    print("Transribe audio Result: ", result)
    text = ""
    for segment in result[0]:
        print("Segment: ", segment)
        text += segment.text + " "
    return text

def speak(text):
    # Voice the given text.
    tts_engine.say(text)
    tts_engine.runAndWait()

def query_llm(text, server_url="http://localhost:1235"):
    # Send text to the LLM via LMStudio and get a response.
    response = client.chat.completions.create(
                 model="junko-model",
                 messages=[
                   {"role": "system", "content": "You are providing quick short answers in 30 words max."},
                   {"role": "user", "content": f"{text}"},
                 ],
                 temperature=0.7,
               )

    answer = json.loads(response.json())
    
    return answer['choices'][0]['message']['content']

def continuous_listen():
    # Listen continuously for the start and stop words.
    while True:
        audio_file = record_audio_to_file(duration=5)
        transcription = transcribe_audio(audio_file)
        os.unlink(audio_file)  # Clean up the temporary file

        if "hello computer" in transcription.lower():
            speak("Hello, I am ready and listening.")
            audio_file = record_audio_to_file(duration=10)
            transcription = transcribe_audio(audio_file)
            os.unlink(audio_file)
            speak("Okay! I'll come back to you!")
            response = query_llm(transcription)
            speak(response)

        elif "thank you computer" in transcription.lower():
            speak("Stop word detected. Goodbye.")
            break

if __name__ == "__main__":
    speak("I am ready to chat.")
    continuous_listen_thread = threading.Thread(target=continuous_listen, daemon=True)
    continuous_listen_thread.start()
    continuous_listen_thread.join()


