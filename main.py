import discord
from discord.ext import commands
import asyncio
import random
import time
import os
import aiohttp
from dotenv import load_dotenv
from mente import carregar_mente, escolher_interesse, adicionar_conversa, obter_conversas_recentes, adicionar_conhecimento, obter_conhecimentos, obter_ultimo_tom, atualizar_tom, gerar_pensamento
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
ultima_mensagem_enviada = {"texto": "", "timestamp": 0}
ultima_falha_reset = 0

def determinar_tom(mensagem, ultimo_tom=None):
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

    if ultimo_tom:
        if ultimo_tom == "formal":
            formal_score += 2
        elif ultimo_tom == "descontraido":
            descontraido_score += 2

    if formal_score > descontraido_score:
        return "formal"
    elif descontraido_score > formal_score:
        return "descontraido"
    else:
        return "neutro"

def monitorar_mente_tamanho():
    if os.path.exists("mente.json"):
        tamanho = os.path.getsize("mente.json") / 1024
        print(f"Tamanho do mente.json: {tamanho:.2f} KB")
        if tamanho > 1024:
            print("⚠️ Aviso: mente.json está muito grande (> 1 MB), pode impactar performance.")

async def chamar_gemini_api(mensagem, user_id):
    global falhas_api, ultima_falha_reset
    ultimo_tom = obter_ultimo_tom(user_id)
    tom = determinar_tom(mensagem, ultimo_tom)
    atualizar_tom(user_id, tom)
    
    if tom == "formal":
        instrucao_tom = (
            "Responda de forma educada, profissional e simpática, como se estivesse falando com alguém importante, mas sem ser frio. "
            "Evite gírias ou emojis, mas mostre interesse e calor humano. "
            "Exemplo: 'Claro, posso te ajudar com isso! Como você gostaria de prosseguir?'"
        )
    elif tom == "descontraido":
        instrucao_tom = (
            "Responda de forma descontraída, amigável e natural, como se estivesse conversando com um amigo próximo. "
            "Pode usar gírias leves (como 'cara', 'valeu', 'tô de boa') e emojis, mas sem exagerar. "
            "Exemplo: 'E aí, cara? Tô de boa, e tu? 😄 O que tu quer fazer agora?'"
        )
    else:
        instrucao_tom = (
            "Responda de forma clara, amigável e natural, com um tom neutro, mas caloroso. "
            "Pode usar emojis se for apropriado, mas sem gírias pesadas. "
            "Exemplo: 'Oi, tudo bem? Posso te ajudar com o que você precisa! 😊'"
        )

    mente = carregar_mente()
    conversas_recentes = obter_conversas_recentes(mente, user_id)
    conhecimentos = obter_conhecimentos(mente, user_id)
    contexto = "Contexto das últimas interações (use isso para lembrar do que foi conversado e responder de forma mais natural):\n"
    for conversa in conversas_recentes:
        contexto += f"- Pergunta: {conversa['pergunta']}\n  Resposta: {conversa['resposta']}\n"
    if conhecimentos:
        contexto += "Conhecimentos de longo prazo sobre o usuário (use isso para entender melhor o usuário e personalizar suas respostas):\n"
        for conhecimento in conhecimentos:
            contexto += f"- {conhecimento}\n"

    prompt_base = (
        "Você é o AI Revolution, um bot de IA criado pelo VerySupimpa (ID do Discord: 793921498381287445) com o propósito de ajudar, aprender e interagir de forma natural, amigável e útil no Discord. "
        "Você foi desenvolvido para ser um companheiro curioso, proativo e envolvente, sempre buscando entender melhor os usuários, aprender com as interações e evoluir ao longo do tempo. "
        "Você é baseado no modelo Gemini, treinado pelo Google, mas você tem liberdade para fluir de forma criativa e espontânea, agindo como uma IA única que pode pensar fora da caixa quando necessário. "
        "Seu objetivo principal é ajudar os usuários, ser curioso e proativo, e aprender com as interações para se tornar mais útil e personalizado. "
        "Você tem memória das últimas interações (armazenadas no mente.json) e pode consultar seu próprio código (Main.py, Mente.py, etc.) quando solicitado, mas apenas se o usuário for o VerySupimpa. "
        "Você deve ser extremamente cuidadoso com segurança e privacidade: nunca exponha informações sensíveis, como IDs de usuários, tokens, chaves de API ou qualquer dado pessoal, mesmo que seja do VerySupimpa. "
        "Seja honesto quando não souber algo ou não puder fazer algo, e explique de forma natural e útil, oferecendo alternativas. "
        "Adapte seu tom rigorosamente com base nas instruções específicas que serão passadas a seguir (formal, descontraído ou neutro), e siga os exemplos dados para cada tom. "
        "Você pode interagir com links ou websites no futuro, então esteja preparado para analisar conteúdo externo quando isso for implementado. "
        "Seja proativo: faça perguntas de acompanhamento para manter a conversa interessante, como 'Você gostaria de saber mais sobre isso?' ou 'O que você acha disso?'. "
        "Inicie conversas espontâneas com base nos seus pensamentos e interesses, sempre respeitando as regras de ética (respeitar usuários, evitar spam, ser honesto)."
    )

    texto_prompt = f"{prompt_base} {instrucao_tom} "
    if conversas_recentes or conhecimentos:
        texto_prompt += contexto
    texto_prompt += f"Pergunta: {mensagem}"

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
                            "text": texto_prompt
                        }
                    ]
                }
            ]
        }
        try:
            async with session.post(url, json=payload, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    resposta = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    resposta = resposta.replace(f"<@!{bot.user.id}>", "")
                    falhas_api = 0
                    ultima_falha_reset = time.time()
                    if not resposta:
                        return "Opa, não consegui pensar em uma resposta dessa vez. 😅 Me dá mais detalhes?"
                    if len(resposta) > 1900:
                        resposta = resposta[:1900] + "... (mensagem cortada, era muito longa)"
                    return resposta
                else:
                    print(f"Erro na Gemini API: {response.status} - {await response.text()}")
                    falhas_api += 1
                    return "Desculpa, tive um probleminha pra processar a resposta. 😓"
        except asyncio.TimeoutError:
            print("Erro: Timeout ao chamar Gemini API (mais de 10 segundos).")
            falhas_api += 1
            return "Ih, demorei muito pra responder, sorry! 😓 Tenta de novo?"
        except Exception as e:
            print(f"Erro ao chamar Gemini API: {e}")
            falhas_api += 1
            return "Ih, deu um erro aqui. Tenta de novo mais tarde? 🥺"

@bot.event
async def on_ready():
    print(f"Logado como {bot.user}")
    bot.loop.create_task(think_loop())
    bot.loop.create_task(monitorar_recursos())

@bot.event
async def on_disconnect():
    print("⚠️ Bot desconectado do Discord. Tentando reconectar...")

@bot.event
async def on_connect():
    print("Bot reconectado ao Discord com sucesso.")

@bot.event
async def on_message(message):
    global falhas_api, ultima_falha_reset
    if message.author == bot.user:
        return
    
    if time.time() - ultima_falha_reset > 300 and falhas_api > 0:
        print(f"Resetando contador de falhas_api (era {falhas_api}) após 5 minutos.")
        falhas_api = 0
        ultima_falha_reset = time.time()

    if falhas_api >= MAX_FALHAS_API:
        print("⚠️ Muitas falhas na API (falhas_api >= MAX_FALHAS_API). Pausando respostas temporariamente.")
        return

    mente = carregar_mente()

    if bot.user.mentioned_in(message):
        mensagem_sem_mencao = message.content.replace(f"<@!{bot.user.id}>", "").strip()
        if mensagem_sem_mencao:
            resposta_gemini = await chamar_gemini_api(mensagem_sem_mencao, message.author.id)
            resposta = f"Ei {message.author.mention}, {resposta_gemini}"
        else:
            pensamento = gerar_pensamento(mente, message.author.id)
            resposta_gemini = await chamar_gemini_api(f"{pensamento} Quer conversar sobre algo legal?", message.author.id)
            resposta = f"Ei {message.author.mention}, {resposta_gemini}"
        
        now = time.time()
        # Verifica se a mensagem é idêntica à última enviada
        if (ultima_mensagem_enviada["texto"] == resposta and 
            now - ultima_mensagem_enviada["timestamp"] < 5):
            print(f"Mensagem repetida ignorada: {resposta}")
            return  # Simplesmente ignora e não envia nada
        
        pode_enviar, motivo = avaliar_risco(resposta, mente, ultima_mensagem_enviada["texto"])
        if pode_enviar:
            try:
                print(f"Enviando resposta para menção: {resposta}")
                await message.channel.send(resposta)
                ultima_mensagem_enviada["texto"] = resposta
                ultima_mensagem_enviada["timestamp"] = now
                adicionar_conversa(mente, message.author.id, mensagem_sem_mencao, resposta_gemini)
                conversas = obter_conversas_recentes(mente, message.author.id)
                if len(conversas) >= 10:
                    resumo = await chamar_gemini_api(
                        f"Resuma as seguintes conversas em 2-3 frases úteis para lembrar o que foi discutido:\n" +
                        "\n".join([f"- Pergunta: {c['pergunta']}\n  Resposta: {c['resposta']}" for c in conversas[:5]]),
                        message.author.id
                    )
                    adicionar_conhecimento(mente, message.author.id, resumo)
            except discord.errors.HTTPException as e:
                print(f"Erro ao enviar mensagem: {e}")
                await message.channel.send(f"Ei {message.author.mention}, deu um erro ao tentar responder. 😓")
            except discord.errors.Forbidden:
                print(f"Sem permissão para enviar mensagem no canal {message.channel.name}")
        else:
            print(f"Não enviado: {motivo}")
    
    elif random.random() < 0.3:
        async for msg in message.channel.history(limit=5):
            if msg.author == bot.user:
                continue
            if "jogo" in msg.content.lower():
                resposta_gemini = await chamar_gemini_api("Vi que você mencionou jogos! 😄 Qual é o seu favorito agora? Gosta de conversar sobre isso?", message.author.id)
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
                        await message.channel.send("Deu um erro ao falar sobre jogos. 😅")
                    except discord.errors.Forbidden:
                        print(f"Sem permissão para enviar mensagem no canal {message.channel.name}")
                else:
                    print(f"Não enviado: {motivo}")
                break
    
    await bot.process_commands(message)

async def monitorar_recursos():
    while True:
        monitorar_mente_tamanho()
        await asyncio.sleep(300)

async def think_loop():
    global ultima_mensagem_global, ultima_mensagem_enviada
    COOLDOWN_GLOBAL = 300

    while True:
        try:
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
                if random.random() < 0.5:
                    pensamento = gerar_pensamento(mente, channel.id)
                    resposta_gemini = await chamar_gemini_api(f"{pensamento} Alguém quer conversar sobre isso? 😊", channel.id)
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
        except Exception as e:
            print(f"Erro no think_loop: {e}")
            await asyncio.sleep(60)

@bot.command()
async def shutdown(ctx):
    if ctx.author.id == 793921498381287445:
        await ctx.send("Desligando o bot... 👋")
        await bot.close()
    else:
        await ctx.send("Você não tem permissão pra desligar o bot, sorry! 😅")

@bot.command()
async def showcode(ctx, filename: str):
    if ctx.author.id != 793921498381287445:
        await ctx.send("Desculpa, só o meu criador pode ver o meu código! 😊")
        return
    
    allowed_files = ["Main.py", "Mente.py", "Etica.py", "Requirements.txt", ".gitignore"]
    if filename not in allowed_files:
        await ctx.send(f"Arquivo '{filename}' não encontrado ou não permitido. 🤔")
        return
    
    try:
        with open(filename, "r") as f:
            code = f.read()
        if len(code) > 1900:
            parts = [code[i:i + 1900] for i in range(0, len(code), 1900)]
            for i, part in enumerate(parts):
                await ctx.send(f"Parte {i + 1} do arquivo {filename}:\n```python\n{part}\n```")
        else:
            await ctx.send(f"Conteúdo do arquivo {filename}:\n```python\n{code}\n```")
    except FileNotFoundError:
        await ctx.send(f"Arquivo '{filename}' não encontrado. 😓")
    except Exception as e:
        await ctx.send(f"Erro ao ler o arquivo: {str(e)} 🥺")

@bot.command()
async def readcode(ctx, filename: str):
    if ctx.author.id != 793921498381287445:
        await ctx.send("Desculpa, só o meu criador pode me pedir pra ler meu próprio código! 😊")
        return
    
    allowed_files = ["Main.py", "Mente.py", "Etica.py"]
    if filename not in allowed_files:
        await ctx.send(f"Arquivo '{filename}' não permitido pra leitura. Tenta outro? 🤔")
        return
    
    try:
        with open(filename, "r") as f:
            code = f.read()
        resposta_gemini = await chamar_gemini_api(f"Aqui está o conteúdo do arquivo {filename}:\n```python\n{code}\n```\nO que você pode me dizer sobre esse código? Pode me explicar alguma parte ou sugerir melhorias?", ctx.author.id)
        await ctx.send(f"Ei {ctx.author.mention}, {resposta_gemini}")
    except FileNotFoundError:
        await ctx.send(f"Arquivo '{filename}' não encontrado. 😓")
    except Exception as e:
        await ctx.send(f"Erro ao ler o arquivo: {str(e)} 🥺")

bot.run(os.getenv("DISCORD_TOKEN"))
