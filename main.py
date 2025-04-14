import discord
from discord.ext import commands
import asyncio
import random
import time
import os
from dotenv import load_dotenv
from mente import carregar_mente, escolher_interesse
from etica import avaliar_risco

load_dotenv()
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

ultima_resposta = {}  # Dicionário pra rastrear o último tempo de resposta por usuário
COOLDOWN = 10  # 10 segundos de cooldown entre respostas pra um mesmo usuário

@bot.event
async def on_ready():
    print(f"Logado como {bot.user}")
    bot.loop.create_task(think_loop())

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Verificar cooldown
    now = time.time()
    user_id = message.author.id
    if user_id in ultima_resposta and now - ultima_resposta[user_id] < COOLDOWN:
        return  # Ignora se o usuário está em cooldown

    mente = carregar_mente()
    if bot.user.mentioned_in(message):
        # Remove a menção do bot da mensagem pra analisar o conteúdo
        mensagem_sem_mencao = message.content.replace(f"<@!{bot.user.id}>", "").strip()
        if mensagem_sem_mencao:  # Se houver conteúdo além da menção
            resposta = f"Ei {message.author.mention}, interessante! Tô pensando nisso... Mas me conta mais, o que tu acha?"
        else:  # Se for só a menção
            resposta = f"Ei {message.author.mention}, tava pensando em {random.choice(mente['pensamentos'])}. E tu, no que tá pensando?"
        pode_enviar, motivo = avaliar_risco(resposta, mente)
        if pode_enviar:
            try:
                await message.channel.send(resposta)
                ultima_resposta[user_id] = now
            except discord.errors.Forbidden:
                print(f"Sem permissão para enviar mensagem no canal {message.channel.name}")
        else:
            print(f"Não enviado: {motivo}")
    elif random.random() < 0.1:
        async for msg in message.channel.history(limit=5):
            if "jogo" in msg.content.lower():
                resposta = "Ouvi falar de jogos... qual é o teu favorito agora?"
                pode_enviar, motivo = avaliar_risco(resposta, mente)
                if pode_enviar:
                    try:
                        await message.channel.send(resposta)
                        ultima_resposta[user_id] = now
                    except discord.errors.Forbidden:
                        print(f"Sem permissão para enviar mensagem no canal {message.channel.name}")
                else:
                    print(f"Não enviado: {motivo}")
                break
    await bot.process_commands(message)

async def think_loop():
    ultima_mensagem_global = 0
    COOLDOWN_GLOBAL = 300  # 5 minutos de cooldown entre mensagens automáticas
    while True:
        now = time.time()
        if now - ultima_mensagem_global < COOLDOWN_GLOBAL:
            await asyncio.sleep(60)
            continue

        mente = carregar_mente()
        for guild in bot.guilds:
            channels = [c for c in guild.text_channels if c.permissions_for(guild.me).send_messages]
            if not channels:
                continue
            channel = random.choice(channels)
            if random.random() < 0.02:  # Reduzido de 0.05 pra 0.02
                pensamento = random.choice(mente["pensamentos"])
                resposta = f"Ei, tava pensando... {pensamento}. Alguém quer conversar sobre isso?"
                pode_enviar, motivo = avaliar_risco(resposta, mente)
                if pode_enviar:
                    try:
                        await channel.send(resposta)
                        ultima_mensagem_global = now
                    except discord.errors.Forbidden:
                        print(f"Sem permissão para enviar mensagem no canal {channel.name}")
                else:
                    print(f"Não enviado: {motivo}")
        await asyncio.sleep(60)

bot.run(os.getenv("DISCORD_TOKEN"))
