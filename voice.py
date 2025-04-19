import speech_recognition as sr
import pyttsx3
import discord
from discord.ext import audiorec
import asyncio
import logging
import io
import wave

# Configura logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class VoiceHandler:
    def __init__(self, db):
        logger.info("Inicializando VoiceHandler")
        self.db = db
        try:
            self.recognizer = sr.Recognizer()
            self.engine = pyttsx3.init()
        except Exception as e:
            logger.error(f"Erro ao inicializar VoiceHandler: {str(e)}")
            raise

    def speak(self, text):
        logger.info(f"Falando: {text}")
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            logger.error(f"Erro ao falar: {str(e)}")

    async def listen(self, voice_client, timeout=15):
        logger.info("Iniciando escuta de áudio via Discord")
        try:
            sink = audiorec.sinks.WaveSink()
            voice_client.start_recording(sink, self.callback, None)
            await asyncio.sleep(timeout)
