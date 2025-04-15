import discord
from discord.ext import commands
import asyncio
import random
import time
import os
import aiohttp
from dotenv import load_dotenv
from mente import carregar_mente, escolher_interesse, adicionar_conversa, obter_conversas_recentes
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
# Rastrear a última mensagem enviada para evitar repetição
ultima_mensagem_enviada = {"texto": "", "timestamp": 0}

def determinar_tom(mensagem):
    palavras_formais = ["por favor", "obrigado", "necessito", "gostaria", "agradeço"]
    palavras_descontraidas = ["cara", "mano", "valeu", "hehe", "lol"]
    tem_emoji = any(ord(char) > 127 for char in mensagem)

    mensagem_lower = mensagem.lower()
    formal_score = sum(1 for palavra in palavras_formais if palavra in mensagem_lower)
    descontraido_score = sum(1 for palavra in palavras_descontraidas if palavra in mensagem_lower)
    if tem_emoji:
        descontraido_score += 1
    if len(mensagem) > 100:
        formal_score += 1
    elif len(mensagem) < 20:
        descontraido_score += 1

    if formal_score > descontraido_score:
        return "formal"
    elif descontraido_score > formal_score:
        return "descontraido"
    else:
        return "neutro"

async def chamar_gemini_api(mensagem, user_id):
    global falhas_api
    tom = determinar_tom(mensagem)
    
    if tom == "formal":
        instrucao_tom = "Responda de forma clara, direta e formal, sem usar gírias ou emojis."
    elif tom == "descontraido":
        instrucao_tom = "Responda de forma amigável e descontraída, podendo usar gírias e emojis, mas sem exagerar."
    else:
        instrucao_tom = "Responda de forma clara e amigável, sem exagerar em formalidade ou descontração."

    # Carregar conversas recentes para fornecer contexto
    mente = carregar_mente()
    conversas_recentes = obter_conversas_recentes(mente, user_id)
    contexto = "Contexto das últimas interações:\n"
    for conversa in conversas_recentes:
        contexto += f"- Pergunta: {conversa['pergunta']}\n  Resposta: {conversa['resposta']}\n"

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
                                f"Você é um bot chamado AI Revolution. {instrucao_tom} "
                                f"{contexto if conversas_recentes else ''}"
                                f"Pergunta: {mensagem}"
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
                    if not resposta:
                        return "Desculpa, não consegui responder."
                    if len(resposta) > 1900:
                        resposta = resposta[:1900] + "... (mensagem cortada, era muito longa)"
                    return resposta
                else:
                    print(f"Erro na Gemini API: {response.status} - {await response.text()}")
                    falhas_api += 1
                    return "Desculpa, houve um erro ao processar a resposta."
        except Exception as e:
            print(f"Erro ao chamar Gemini API: {e}")
            falhas_api += 1
            return "Erro ao tentar responder. Tente novamente mais tarde."

@bot.event
async def on_ready():
    print(f"Logado como {bot.user}")
    bot.loop.create_task(think_loop())

@bot.event
async def on_message(message):
    global falhas_api, ultima_mensagem_enviada
    if message.author == bot.user:
        return
    if falhas_api >= MAX_FALHAS_API:
        print("Muitas falhas na API, pausando respostas temporariamente.")
        return

    mente = carregar_mente()

    if bot.user.mentioned_in(message):
        mensagem_sem_mencao = message.content.replace(f"<@!{bot.user.id}>", "").strip()
        if mensagem_sem_mencao:
            resposta_gemini = await chamar_gemini_api(mensagem_sem_mencao, message.author.id)
            resposta = f"Ei {message.author.mention}, {resposta_gemini}"
        else:
            pensamento = random.choice(mente["pensamentos"])
            resposta_gemini = await chamar_gemini_api(f"Estou pensando em '{pensamento}'. O que você acha disso?", message.author.id)
            resposta = f"Ei {message.author.mention}, {resposta_gemini}"
        
        # Verificar se a mensagem é repetida
        now = time.time()
        if (ultima_mensagem_enviada["texto"] == resposta and 
            now - ultima_mensagem_enviada["timestamp"] < 5):  # 5 segundos de intervalo
            print(f"Mensagem repetida ignorada: {resposta}")
            return
        
        pode_enviar, motivo = avaliar_risco(resposta, mente, ultima_mensagem_enviada["texto"])
        if pode_enviar:
            try:
                print(f"Enviando resposta para menção: {resposta}")
                await message.channel.send(resposta)
                ultima_mensagem_enviada["texto"] = resposta
                ultima_mensagem_enviada["timestamp"] = now
                # Salvar a conversa na memória
                adicionar_conversa(mente, message.author.id, mensagem_sem_mencao, resposta_gemini)
            except discord.errors.HTTPException as e:
                print(f"Erro ao enviar mensagem: {e}")
                await message.channel.send(f"Ei {message.author.mention}, deu um erro ao tentar responder.")
            except discord.errors.Forbidden:
                print(f"Sem permissão para enviar mensagem no canal {message.channel.name}")
        else:
            print(f"Não enviado: {motivo}")
    
    elif random.random() < 0.1:
        async for msg in message.channel.history(limit=5):
            if msg.author == bot.user:
                continue
            if "jogo" in msg.content.lower():
                resposta_gemini = await chamar_gemini_api("Vi que você mencionou jogos. Qual é o seu favorito agora?", message.author.id)
                resposta = resposta_gemini
                now = time.time()
                if (ultima_mensagem_enviada["texto"] == resposta and 
                    now - ultima_mensagem_enviada["timestamp"] < 5):
                    print(f"Mensagem repetida ignorada: {resposta}")
                    return
                
                pode_enviar, motivo = avaliar_risco(resposta, mente, ultima_mensagem_enviada["texto"])
                if pode_enviar:
                    try:
                        print(f"Enviando resposta sobre jogos: {resposta}")
                        await message.channel.send(resposta)
                        ultima_mensagem_enviada["texto"] = resposta
                        ultima_mensagem_enviada["timestamp"] = now
                        adicionar_conversa(mente, message.author.id, "Mencionou jogos", resposta_gemini)
                    except discord.errors.HTTPException as e:
                        print(f"Erro ao enviar mensagem: {e}")
                        await message.channel.send("Deu um erro ao falar sobre jogos.")
                    except discord.errors.Forbidden:
                        print(f"Sem permissão para enviar mensagem no canal {message.channel.name}")
                else:
                    print(f"Não enviado: {motivo}")
                break
    
    await bot.process_commands(message)

async def think_loop():
    global ultima_mensagem_global, ultima_mensagem_enviada
    COOLDOWN_GLOBAL = 300

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
                resposta_gemini = await chamar_gemini_api(f"Estou pensando em '{pensamento}'. Alguém quer conversar sobre isso?", channel.id)
                resposta = f"Ei, {resposta_gemini}"
                if (ultima_mensagem_enviada["texto"] == resposta and 
                    now - ultima_mensagem_enviada["timestamp"] < 5):
                    print(f"Mensagem repetida ignorada: {resposta}")
                    continue
                
                pode_enviar, motivo = avaliar_risco(resposta, mente, ultima_mensagem_enviada["texto"])
                if pode_enviar:
                    try:
                        print(f"Enviando mensagem automática no canal {channel.name}: {resposta}")
                        await channel.send(resposta)
                        ultima_mensagem_global = now
                        ultima_mensagem_enviada["texto"] = resposta
                        ultima_mensagem_enviada["timestamp"] = now
                        adicionar_conversa(mente, channel.id, f"Pensamento: {pensamento}", resposta_gemini)
                    except discord.errors.HTTPException as e:
                        print(f"Erro ao enviar mensagem automática: {e}")
                    except discord.errors.Forbidden:
                        print(f"Sem permissão para enviar mensagem no canal {channel.name}")
                else:
                    print(f"Não enviado (think_loop): {motivo}")
        await asyncio.sleep(60)

@bot.command()
async def shutdown(ctx):
    if ctx.author.id == 793921498381287445:
        await ctx.send("Desligando o bot...")
        await bot.close()
    else:
        await ctx.send("Você não tem permissão para desligar o bot.")

@bot.command()
async def showcode(ctx, filename: str):
    if ctx.author.id != 793921498381287445:
        await ctx.send("Você não tem permissão para ver o código.")
        return
    
    allowed_files = ["Main.py", "Mente.py", "Etica.py", "Requirements.txt", ".gitignore"]
    if filename not in allowed_files:
        await ctx.send(f"Arquivo '{filename}' não encontrado ou não permitido.")
        return
    
    try:
        with open(filename, "r") as f:
            code = f.read()
        if len(code) > 1900:
            parts = [code[i:i + 1900] for i in range(0, len(code), 1900)]
            for i, part in enumerate(parts):
                await ctx.send(f"Parte {i + 1} do arquivo {filename}:\n```python\n
