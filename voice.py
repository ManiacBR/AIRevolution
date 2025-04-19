import speech_recognition as sr
import pyttsx3
import discord
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
            sink = discord.sinks.WaveSink()
            voice_client.start_recording(sink, self.callback, None)
            await asyncio.sleep(timeout)
            voice_client.stop_recording()
            
            if sink.file:
                audio_data = sink.file.getvalue()
                wav_file = io.BytesIO(audio_data)
                with wave.open(wav_file, 'rb') as wav:
                    audio_source = sr.AudioFile(wav)
                    with audio_source as source:
                        audio = self.recognizer.record(source)
                    text = self.recognizer.recognize_google(audio)
                    logger.info(f"Áudio transcrito: {text}")
                    return text
            return None
        except sr.UnknownValueError:
            logger.warning("Nenhum áudio compreendido")
            return None
        except sr.RequestError as e:
            logger.error(f"Erro na transcrição: {str(e)}")
            return f"Erro na transcrição: {str(e)}"
        except Exception as e:
            logger.error(f"Erro inesperado na escuta: {str(e)}")
            return f"Erro na escuta: {str(e)}"

    async def callback(self, sink, *args):
        logger.info("Callback de gravação chamado")

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
                        context=self.db.get_context(str(channel.guild.id), str(channel.guild.id)),
                        extra_instruction="Responda sempre em português."
                    )
                    await channel.send(response)
                    self.speak(response)
            except Exception as e:
                logger.error(f"Erro na interação por voz: {str(e)}")
                await channel.send(f"Erro na interação por voz: {str(e)}")
                break
