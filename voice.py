import os
import pyttsx3
import speech_recognition as sr
import tempfile
import discord

class VoiceHandler:
    def __init__(self, database):
        self.db = database
        self.engine = pyttsx3.init(driverName='espeak')  # Especifica o driver do TTS
        self.engine.setProperty('rate', 160)
        self.engine.setProperty('volume', 1.0)
        print("Inicializando VoiceHandler")

    def speak(self, text, filename='response.mp3'):
        """Converte texto em fala e salva como arquivo"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tf:
            temp_path = tf.name
        self.engine.save_to_file(text, temp_path)
        self.engine.runAndWait()

        # Converte para mp3 se ffmpeg estiver disponível
        mp3_path = filename
        os.system(f"ffmpeg -y -loglevel quiet -i {temp_path} {mp3_path}")
        os.remove(temp_path)
        return mp3_path

    def transcribe_audio(self, audio_path):
        """Transcreve fala de um arquivo de áudio"""
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio, language='pt-BR')
            return text
        except sr.UnknownValueError:
            return "Não entendi o que você disse."
        except sr.RequestError:
            return "Erro ao se comunicar com o serviço de reconhecimento de voz."

    async def send_voice_response(self, interaction: discord.Interaction, text: str):
        """Gera resposta em áudio e envia no canal de texto"""
        file_path = self.speak(text)
        await interaction.channel.send(file=discord.File(file_path))
        os.remove(file_path)
