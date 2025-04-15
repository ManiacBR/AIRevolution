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

ultima_mensagem_global = 0
COOLDOWN_GLOBAL = 300
falhas_api = 0
MAX_FALHAS_API = 3

async def chamar_gemini_api(mensagem):
    global falhas_api
    async with aiohttp.ClientSession() as session:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={os.getenv('GEMINI_API_KEY')}"
        headers = {
            "Content-Type": "application/json"
        }
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": (
                                "Você é um bot amigável e curioso chamado AI Revolution, inspirado no Guia do Mochileiro das Galáxias. "
                                f"Responda de forma natural, amigável e com um toque de humor! Pergunta: {mensagem}"
                            )
                        }
                    ]
                }
            ]
        }
        try:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    resposta = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    resposta = resposta.replace(f"<@!{bot.user.id}>", "")
                    falhas_api = 0
                    # Verificar se a resposta é válida e limitar a 2000 caracteres
                    if not resposta:
                        return "Desculpa, não consegui pensar em nada legal... 😅"
                    if len(resposta) > 1900:  # Margem de segurança para menção
                        resposta = resposta[:1900] + "... (cortado, era muito longo!)"
                    return resposta
                else:
                    print(f"Erro na Gemini API: {response.status} - {await response.text()}")
                    falhas_api += 1
                    return "Desculpa, tô com um probleminha pra pensar agora... 😅"
        except Exception as e:
            print(f"Erro ao chamar Gemini API: {e}")
            falhas_api += 1
            return "Ops, algo deu errado! Vou tentar de novo mais tarde."

@bot.event
async def on_ready():
    print(f"Logado como {bot.user}")
    bot.loop.create_task(think_loop())

@bot.event
async def on_message(message):
    global falhas_api
    if message.author == bot.user:
        return
    if falhas_api >= MAX_FALHAS_API:
        print("Muitas falhas na API, pausando respostas temporariamente.")
        return

    mente = carregar_mente()
    ultima_mensagem_enviada = ""

    if bot.user.mentioned_in(message):
        mensagem_sem_mencao = message.content.replace(f"<@!{bot.user.id}>", "").strip()
        if mensagem_sem_mencao:
            resposta_gemini = await chamar_gemini_api(mensagem_sem_mencao)
            resposta = f"Ei {message.author.mention}, {resposta_gemini}"
        else:
            pensamento = random.choice(mente["pensamentos"])
            resposta_gemini = await chamar_gemini_api(f"Tava pensando em '{pensamento}'. O que acha disso?")
            resposta = f"Ei {message.author.mention}, {resposta_gemini}"
        
        pode_enviar, motivo = avaliar_risco(resposta, mente, ultima_mensagem_enviada)
        if pode_enviar:
            try:
                print(f"Enviando resposta para menção: {resposta}")
                await message.channel.send(resposta)
                ultima_mensagem_enviada = resposta
            except discord.errors.HTTPException as e:
                print(f"Erro ao enviar mensagem: {e}")
                await message.channel.send(f"Ei {message.author.mention}, deu um erro ao tentar responder... 😅")
            except discord.errors.Forbidden:
                print(f"Sem permissão para enviar mensagem no canal {message.channel.name}")
        else:
            print(f"Não enviado: {motivo}")
    
    elif random.random() < 0.1:
        async for msg in message.channel.history(limit=5):
            if msg.author == bot.user:
                continue
            if "jogo" in msg.content.lower():
                resposta_gemini = await chamar_gemini_api("Ouvi falar de jogos... qual é o teu favorito agora?")
                resposta = resposta_gemini
                pode_enviar, motivo = avaliar_risco(resposta, mente, ultima_mensagem_enviada)
                if pode_enviar:
                    try:
                        print(f"Enviando resposta sobre jogos: {resposta}")
                        await message.channel.send(resposta)
                        ultima_mensagem_enviada = resposta
                    except discord.errors.HTTPException as e:
                        print(f"Erro ao enviar mensagem: {e}")
                        await message.channel.send("Deu um erro ao falar sobre jogos... 😅")
                    except discord.errors.Forbidden:
                        print(f"Sem permissão para enviar mensagem no canal {message.channel.name}")
                else:
                    print(f"Não enviado: {motivo}")
                break
    
    await bot.process_commands(message)

async def think_loop():
    global ultima_mensagem_global
    COOLDOWN_GLOBAL = 300
    ultima_mensagem_enviada = ""

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
            if random.random() < 0.005:
                pensamento = random.choice(mente["pensamentos"])
                resposta_gemini = await chamar_gemini_api(f"Tava pensando em '{pensamento}'. Alguém quer conversar sobre isso?")
                resposta = f"Ei, {resposta_gemini}"
                pode_enviar, motivo = avaliar_risco(resposta, mente, ultima_mensagem_enviada)
                if pode_enviar:
                    try:
                        print(f"Enviando mensagem automática no canal {channel.name}: {resposta}")
                        await channel.send(resposta)
                        ultima_mensagem_global = now
                        ultima_mensagem_enviada = resposta
                    except discord.errors.HTTPException as e:
                        print(f"Erro ao enviar mensagem automática: {e}")
                    except discord.errors.Forbidden:
                        print(f"Sem permissão para enviar mensagem no canal {channel.name}")
                else:
                    print(f"Não enviado (think_loop): {motivo}")
        await asyncio.sleep(60)

bot.run(os.getenv("DISCORD_TOKEN"))
