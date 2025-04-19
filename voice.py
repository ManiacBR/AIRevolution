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
                user_input = await self.listen(voice_client)
                if user_input:
                    if user_input.lower().startswith("sair") or "sai da voz" in user_input.lower():
                        await voice_client.disconnect()
                        await channel.send("Desconectado do canal de voz!")
                        break
                    response = await ai.generate_response(
                        user_input,
                        context=db.get_context(str(channel.guild.id), str(channel.guild.id)),
                        extra_instruction="Responda sempre em português."
                    )
                    await channel.send(response)
                    self.speak(response)
            except Exception as e:
                await channel.send(f"Erro na interação por voz: {str(e)}")
                break
