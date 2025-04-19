import os
import discord
from discord.ext import commands
from core.memory import MemoryManager
from utils.detection import is_message_to_bot

TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)  # prefixo não será usado

memory = MemoryManager()

@bot.event
async def on_ready():
    print(f"{bot.user} está online!")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if await is_message_to_bot(message, bot.user):
        content = message.content.lower()
        await message.channel.send("Recebi sua mensagem! (resposta provisória)")
        memory.save_user_message(message.author.id, message.content)
    
    await bot.process_commands(message)

bot.run(TOKEN)
