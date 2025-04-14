import discord
from discord.ext import commands
import asyncio
import random
import time
import os
import aiohttp
from dotenv import load_dotenv
from mente import carregar_mente, escolher_interesse
from etica import avaliar_risco

load_dotenv()
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Variáveis para controle global
ultima_mensagem_global = 0  # Para o think_loop
COOLDOWN_GLOBAL = 300  # 5 minutos de cooldown para mensagens automáticas
falhas_api = 0  # Contador de falhas na API
MAX_FALHAS_API = 3  # Máximo de falhas antes de parar temporariamente

# Função para chamar a xAI API e gerar uma resposta
async def chamar_xai_api(mensagem):
    global falhas_api
    async with aiohttp.ClientSession() as session:
        url = "https://api.x.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {os.getenv('XAI_API_KEY')}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "grok-3-latest",
            "messages": [
                {"role": "system", "content": "Você é um bot amigável e curioso chamado AI Revolution, inspirado no Guia do Mochileiro das Galáxias. Responda de forma natural, amigável e com um toque de humor!"},
                {"role": "user", "content": mensagem}
            ],
            "temperature": 0.7,
            "max_tokens": 100
        }
        try:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    resposta = data["choices"][0]["message"]["content"]
                    # Remove menções ao próprio bot da resposta
                    resposta = resposta.replace(f"<@!{bot.user.id}>", "")
                    falhas_api = 0  # Reseta o contador de falhas
                    return resposta
                else:
                    print(f"Erro na xAI API: {response.status} - {await response.text()}")
                    falhas_api += 1
                    return "Desculpa, tô com um probleminha pra pensar agora... 😅"
        except Exception as e:
            print(f"Erro ao chamar xAI API: {e}")
            falhas_api += 1
            return "Ops, algo deu errado! Vou tentar de novo mais tarde."

@bot.event
async def on_ready():
    print(f"Logado como {bot.user}")
    bot.loop.create_task(think_loop())

@bot.event
async def on_message(message):
    global falhas_api
    # Ignora mensagens do próprio bot
    if message.author == bot.user:
        return

    # Para de responder se houver muitas falhas na API
    if falhas_api >= MAX_FALHAS_API:
        print("Muitas falhas na API, pausando respostas temporariamente.")
        return

    mente = carregar_mente()
    ultima_mensagem_enviada = ""  # Para rastrear a última mensagem enviada e evitar repetição

    if bot.user.mentioned_in(message):
        # Remove a menção do bot da mensagem para analisar o conteúdo
        mensagem_sem_mencao = message.content.replace(f"<@!{bot.user.id}>", "").strip()
        if mensagem_sem_mencao:  # Se houver conteúdo além da menção
            resposta_xai = await chamar_xai_api(mensagem_sem_mencao)
            resposta = f"Ei {message.author.mention}, {resposta_xai}"
        else:  # Se for só a menção
            pensamento = random.choice(mente["pensamentos"])
            resposta_xai = await chamar_xai_api(f"Tava pensando em '{pensamento}'. O que acha disso?")
            resposta = f"Ei {message.author.mention}, {resposta_xai}"
        
        pode_enviar, motivo = avaliar_risco(resposta, mente, ultima_mensagem_enviada)
        if pode_enviar:
            try:
                print(f"Enviando resposta para menção: {resposta}")
                await message.channel.send(resposta)
                ultima_mensagem_enviada = resposta
            except discord.errors.Forbidden:
                print(f"Sem permissão para enviar mensagem no canal {message.channel.name}")
        else:
            print(f"Não enviado: {motivo}")
    
    elif random.random() < 0.1:  # 10% de chance de responder mensagens sobre "jogo"
        async for msg in message.channel.history(limit=5):
            if msg.author == bot.user:  # Evita responder a si mesmo
                continue
            if "jogo" in msg.content.lower():
                resposta_xai = await chamar_xai_api("Ouvi falar de jogos... qual é o teu favorito agora?")
                resposta = resposta_xai
                pode_enviar, motivo = avaliar_risco(resposta, mente, ultima_mensagem_enviada)
                if pode_enviar:
                    try:
                        print(f"Enviando resposta sobre jogos: {resposta}")
                        await message.channel.send(resposta)
                        ultima_mensagem_enviada = resposta
                    except discord.errors.Forbidden:
                        print(f"Sem permissão para enviar mensagem no canal {message.channel.name}")
                else:
                    print(f"Não enviado: {motivo}")
                break
    
    await bot.process_commands(message)

async def think_loop():
    global ultima_mensagem_global
    COOLDOWN_GLOBAL = 300  # 5 minutos de cooldown para mensagens automáticas
    ultima_mensagem_enviada = ""  # Para evitar repetição no think_loop

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
            if random.random() < 0.005:  # Reduzido para 0.5% de chance por canal
                pensamento = random.choice(mente["pensamentos"])
                resposta_xai = await chamar_xai_api(f"Tava pensando em '{pensamento}'. Alguém quer conversar sobre isso?")
                resposta = f"Ei, {resposta_xai}"
                pode_enviar, motivo = avaliar_risco(resposta, mente, ultima_mensagem_enviada)
                if pode_enviar:
                    try:
                        print(f"Enviando mensagem automática no canal {channel.name}: {resposta}")
                        await channel.send(resposta)
                        ultima_mensagem_global = now
                        ultima_mensagem_enviada = resposta
                    except discord.errors.Forbidden:
                        print(f"Sem permissão para enviar mensagem no canal {channel.name}")
                else:
                    print(f"Não enviado (think_loop): {motivo}")
        await asyncio.sleep(60)

bot.run(os.getenv("DISCORD_TOKEN"))
