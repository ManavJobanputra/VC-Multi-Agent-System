import speech_recognition as sr
from gtts import gTTS
import base64
import io
import os

class VoiceProcessor:
    def __init__(self):
        self.recognizer = sr.Recognizer()

    def transcribe_audio(self, audio_base64: str) -> str:
        try:
            audio_bytes = base64.b64decode(audio_base64)
            audio_file = io.BytesIO(audio_bytes)
            
            with sr.AudioFile(audio_file) as source:
                audio_data = self.recognizer.record(source)
            
            # Use Google Web Speech API for transcription (requires internet)
            # For local models, other libraries like Vosk or Whisper (local setup) would be needed
            text = self.recognizer.recognize_google(audio_data)
            return text
        except sr.UnknownValueError:
            return "Could not understand audio"
        except sr.RequestError as e:
            return f"Speech recognition service error: {e}"
        except Exception as e:
            return f"Error transcribing audio: {e}"

    def generate_audio(self, text: str) -> str:
        try:
            tts = gTTS(text=text, lang='en')
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            audio_base64 = base64.b64encode(audio_buffer.read()).decode('utf-8')
            return audio_base64
        except Exception as e:
            return f"Error generating audio: {e}"


