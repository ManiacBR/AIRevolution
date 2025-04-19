import edge_tts
import asyncio

async def text_to_speech(text, filename="resposta.mp3"):
    communicate = edge_tts.Communicate(text, "pt-BR-AntonioNeural")
    await communicate.save(filename)
