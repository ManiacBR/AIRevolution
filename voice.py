import speech_recognition as sr
import pyttsx3
import discord
import asyncio
import logging

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
    def __init__(self):
        logger.info("Inicializando VoiceHandler")
        try:
            self.recognizer = sr.Recognizer()
            self.engine = pyttsx3.init()
        except Exception as e:
            logger.error(f"Erro ao inicializar VoiceHandler: {str(e)}")
            raise

    async def listen(self, voice_client, timeout=15):
        logger.info("Iniciando escuta de áudio")
        loop = asyncio.get_event_loop()
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source)
            try:
                audio = await loop.run_in_executor(None, lambda: self.recognizer.listen(source, timeout=timeout))
                text = await loop.run_in_executor(None, lambda: self.recognizer.recognize_google(audio))
                logger.info(f"Áudio transcrito: {text}")
                return text
            except sr.UnknownValueError:
                logger.warning("Nenhum áudio compreendido")
                return None
            except sr.RequestError as e:
                logger.error(f"Erro na transcrição: {str(e)}")
                return f"Erro na transcrição: {str(e)}"
            except Exception as e:
                logger.error(f"Erro inesperado na escuta: {str(e)}")
                return f"Erro na escuta: {str(e)}"

    def speak(self, text):
        logger.info(f"Falando: {text}")
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            logger.error(f"Erro ao falar: {str(e)}")

    async def handle_voice_interaction(self, voice_client, ai, channel):
        logger.info("Iniciando interação por voz")
        while voice_client.is_connected():
            try:
                user_input = await self.listen(voice_client)
                if user_input:
                    user_input_lower = user_input.lower()
                    exit_phrases = [
                        "sair", "sai da voz", "sai da vos", "sair da voz",
                        "sair voz", "sai voz", "desconectar", "sair do canal",
                        "sair do voz", "sai do canal", "para de falar"
                    ]
                    if any(phrase in user_input_lower for phrase in exit_phrases):
                        logger.info("Comando sair detectado, desconectando")
                        await voice_client.disconnect()
                        await channel.send("Desconectado do canal de voz!")
                        break
                    logger.info(f"Processando entrada do usuário: {user_input}")
                    response = await ai.generate_response(
                        user_input,
                        context=db.get_context(str(channel.guild.id), str(channel.guild.id)),
                        extra_instruction="Responda sempre em português."
                    )
                    await channel.send(response)
                    self.speak(response)
            except Exception as e:
                logger.error(f"Erro na interação por voz: {str(e)}")
                await channel.send(f"Erro na interação por voz: {str(e)}")
                break
