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

ultima_resposta = {}  # Dicionário pra rastrear o último tempo de resposta por usuário
COOLDOWN = 10  # 10 segundos de cooldown entre respostas pra um mesmo usuário

# Função pra chamar a xAI API e gerar uma resposta
async def chamar_xai_api(mensagem):
    async with aiohttp.ClientSession() as session:
        url = "https://api.x.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {os.getenv('XAI_API_KEY')}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "grok-beta",  # Modelo da xAI (pode mudar conforme a disponibilidade)
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
                    return data["choices"][0]["message"]["content"]
                else:
                    print(f"Erro na xAI API: {response.status} - {await response.text()}")
                    return "Desculpa, tô com um probleminha pra pensar agora... 😅"
        except Exception as e:
            print(f"Erro ao chamar xAI API: {e}")
            return "Ops, algo deu errado! Vou tentar de novo mais tarde."

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
            # Chama a xAI API pra gerar uma resposta com base na mensagem do usuário
            resposta_xai = await chamar_xai_api(mensagem_sem_mencao)
            resposta = f"Ei {message.author.mention}, {resposta_xai}"
        else:  # Se for só a menção
            pensamento = random.choice(mente["pensamentos"])
            # Usa a xAI API pra gerar uma resposta com base no pensamento
            resposta_xai = await chamar_xai_api(f"Tava pensando em '{pensamento}'. O que acha disso?")
            resposta = f"Ei {message.author.mention}, {resposta_xai}"
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
                # Usa a xAI API pra gerar uma resposta sobre jogos
                resposta_xai = await chamar_xai_api("Ouvi falar de jogos... qual é o teu favorito agora?")
                resposta = resposta_xai
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
                # Usa a xAI API pra gerar uma mensagem com base no pensamento
                resposta_xai = await chamar_xai_api(f"Tava pensando em '{pensamento}'. Alguém quer conversar sobre isso?")
                resposta = f"Ei, {resposta_xai}"
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
