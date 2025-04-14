import discord
from discord.ext import commands
import asyncio
import random
from mente import carregar_mente, escolher_interesse
from etica import avaliar_risco
import os
from dotenv import load_dotenv

load_dotenv()
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logado como {bot.user}")
    bot.loop.create_task(think_loop())

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    mente = carregar_mente()
    if bot.user.mentioned_in(message):
        resposta = f"Ei {message.author.mention}, tava pensando em {random.choice(mente['pensamentos'])}. E tu, no que tá pensando?"
        pode_enviar, motivo = avaliar_risco(resposta, mente)
        if pode_enviar:
            await message.channel.send(resposta)
        else:
            print(f"Não enviado: {motivo}")
    elif random.random() < 0.1:
        async for msg in message.channel.history(limit=5):
            if "jogo" in msg.content.lower():
                resposta = "Ouvi falar de jogos... qual é o teu favorito agora?"
                pode_enviar, motivo = avaliar_risco(resposta, mente)
                if pode_enviar:
                    await message.channel.send(resposta)
                else:
                    print(f"Não enviado: {motivo}")
                break
    await bot.process_commands(message)

async def think_loop():
    while True:
        mente = carregar_mente()
        for guild in bot.guilds:
            channel = random.choice([c for c in guild.text_channels if c.permissions_for(guild.me).send_messages])
            if random.random() < 0.05:
                pensamento = random.choice(mente["pensamentos"])
                resposta = f"Ei, tava pensando... {pensamento}. Alguém quer conversar sobre isso?"
                pode_enviar, motivo = avaliar_risco(resposta, mente)
                if pode_enviar:
                    await channel.send(resposta)
                else:
                    print(f"Não enviado: {motivo}")
        await asyncio.sleep(60)

bot.run(os.getenv("DISCORD_TOKEN"))