import discord
import os
from discord.ext import commands
from utils.memory import MemoryManager
from core.openai_client import get_response
from core.voice import text_to_speech

# Tokens e Intents
TOKEN = os.getenv("DISCORD_TOKEN")
INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.messages = True
INTENTS.guilds = True

bot = commands.Bot(command_prefix="!", intents=INTENTS)
memory = MemoryManager()

AI_NAME = "revolution"

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content_lower = message.content.lower()
    mentioned = bot.user in message.mentions or AI_NAME in content_lower

    if mentioned:
        user_id = str(message.author.id)
        language = "pt"

        history = memory.get_history(user_id)
        history.append({"role": "user", "content": message.content})

        try:
            reply = get_response(history, language)
        except Exception as e:
            reply = f"Erro ao acessar a API da OpenAI: {e}"

        memory.save_user_message(user_id, message.content)
        memory.save_user_message(user_id, reply)

        await text_to_speech(reply)
        await message.channel.send(file=discord.File("resposta.mp3"))

    await bot.process_commands(message)

bot.run(TOKEN)
