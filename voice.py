import speech_recognition as sr
import pyttsx3
import discord
import asyncio

class VoiceHandler:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()

    async def listen(self, voice_client, timeout=10):
        loop = asyncio.get_event_loop()
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source)
            try:
                audio = await loop.run_in_executor(None, lambda: self.recognizer.listen(source, timeout=timeout))
                text = await loop.run_in_executor(None, lambda: self.recognizer.recognize_google(audio))
                return text
            except sr.UnknownValueError:
                return None
            except sr.RequestError as e:
                return f"Erro na transcrição: {str(e)}"

    def speak(self, text):
        self.engine.say(text)
        self.engine.runAndWait()

    async def handle_voice_interaction(self, voice_client, ai, channel):
        while voice_client.is_connected():
            try:
                # Escuta o usuário
                user_input = await self.listen(voice_client)
                if user_input:
                    # Gera resposta com IA
                    response = await ai.generate_response(user_input)
                    # Envia resposta por texto no canal
                    await channel.send(response)
                    # Fala a resposta
                    self.speak(response)
            except Exception as e:
                await channel.send(f"Erro na interação por voz: {str(e)}")
                break
