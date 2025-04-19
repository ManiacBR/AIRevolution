import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from database import Database
from ai import OpenAIHandler

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
INTENTS = discord.Intents.default()
INTENTS.messages = True
INTENTS.message_content = True

bot = commands.Bot(command_prefix="!", intents=INTENTS)
db = Database()
ai_handler = OpenAIHandler()

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if bot.user in message.mentions:
        user_input = message.content.replace(f"<@{bot.user.id}>", "").strip()
        response = await ai_handler.get_response(user_input)
        await message.channel.send(response)

bot.run(TOKEN)
