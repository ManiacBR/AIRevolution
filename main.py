import discord
from discord.ext import commands
import asyncio
import random
import time
import os
import aiohttp
from dotenv import load_dotenv
from etica import avaliar_risco
from mente import carregar_mente, escolher_interesse, adicionar_conversa, obter_conversas_recentes, adicionar_conhecimento, obter_conhecimentos, obter_ultimo_tom, atualizar_tom, gerar_pensamento
from auto_edicao import aplicar_mudanca_codigo

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
ultima_mensagem_por_canal = {}
metricas_desempenho = {
    "erros_api": 0,
    "respostas_bloqueadas": 0,
    "feedback_negativo": 0,
    "respostas_enviadas": 0,
    "erros_auto_edicao": 0,
    "ultima_analise": time.time()
}

def registrar_metrica(tipo):
    metricas_desempenho[tipo] += 1

async def chamar_gemini_api(mensagem, user_id):
    global falhas_api, ultima_falha_reset
    ultimo_tom = obter_ultimo_tom(user_id)
    tom = determinar_tom(mensagem, ultimo_tom)
    atualizar_tom(user_id, tom)
    
    instrucao_tom = (
        "Responda de forma clara, amigável e natural, com um tom neutro, mas caloroso. "
        "Pode usar emojis se for apropriado, mas sem gírias pesadas. "
        "Exemplo: 'Oi, tudo bem? Posso te ajudar com o que você precisa! 😊'"
    ) if tom == "neutro" else (
        "Responda de forma educada, profissional e simpática, sem gírias ou emojis. "
        "Exemplo: 'Claro, posso ajudar com isso! Como gostaria de prosseguir?'"
    ) if tom == "formal" else (
        "Responda de forma descontraída, com gírias leves e emojis. "
        "Exemplo: 'E aí, cara? Tô de boa, e tu? 😄'"
    )
    
    mente = carregar_mente()
    conversas_recentes = obter_conversas_recentes(mente, user_id)
    conhecimentos = obter_conhecimentos(mente, user_id)
    contexto = "Contexto das últimas interações:\n" + "\n".join(
        [f"- Pergunta: {c['pergunta']}\n  Resposta: {c['resposta']}" for c in conversas_recentes]
    ) + ("\nConhecimentos sobre o usuário:\n" + "\n".join([f"- {k}" for k in conhecimentos]) if conhecimentos else "")
    
    prompt_base = (
        "Você é o AI Revolution, criado por VerySupimpa (ID: 793921498381287445). "
        "Seu objetivo é ajudar, aprender e interagir de forma natural e útil no Discord. "
        "Adapte seu tom conforme instruído e use o contexto fornecido."
    )
    
    texto_prompt = f"{prompt_base} {instrucao_tom}\n{contexto}\nPergunta: {mensagem}"
    
    async with aiohttp.ClientSession() as session:
        url = f"https://api.github.com/repos/VerySupimpa/ai-revolution/contents/{os.getenv('GEMINI_API_KEY')}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": texto_prompt}]}]}
        try:
            async with session.post(url, json=payload, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    resposta = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    resposta = resposta.replace(f"<@!{bot.user.id}>", "")
                    falhas_api = 0
                    ultima_falha_reset = time.time()
                    return resposta if resposta else "Opa, não consegui pensar em nada. 😅"
                else:
                    print(f"Erro na API: {response.status}")
                    falhas_api += 1
                    registrar_metrica("erros_api")
                    return "Probleminha na resposta, sorry! 😓"
        except asyncio.TimeoutError:
            print("Timeout na API.")
            falhas_api += 1
            registrar_metrica("erros_api")
            return "Demorei demais, tenta de novo? 😓"
        except Exception as e:
            print(f"Erro na API: {e}")
            falhas_api += 1
            registrar_metrica("erros_api")
            return "Deu ruim aqui, tenta mais tarde? 🥺"

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
    return "formal" if formal_score > descontraido_score else "descontraido" if descontraido_score > formal_score else "neutro"

async def analisar_desempenho():
    global metricas_desempenho
    now = time.time()
    if now - metricas_desempenho["ultima_analise"] < 3600:
        return
    
    print("Analisando desempenho...")
    taxa_erro_api = metricas_desempenho["erros_api"] / max(metricas_desempenho["respostas_enviadas"], 1)
    taxa_bloqueio = metricas_desempenho["respostas_bloqueadas"] / max(metricas_desempenho["respostas_enviadas"], 1)
    
    owner_id = 793921498381287445
    if taxa_erro_api > 0.1:
        print("⚠️ Muitos erros na API. Ajustando main.py...")
        novo_codigo, erro = await sugerir_mudanca_codigo(
            "main.py",
            "Muitas falhas na API (mais de 10%). Ajuste chamar_gemini_api com retry ou timeout maior.",
            owner_id
        )
        if not erro:
            teste_ok, erro_teste = testar_codigo(novo_codigo)
            if teste_ok:
                salvar_nova_versao("main.py", novo_codigo, "Ajuste por erros na API", owner_id)
                await bot.get_user(owner_id).send("⚠️ Atualizei main.py no DB por erros na API!")
            else:
                print(f"Falha ao testar: {erro_teste}")
    
    if taxa_bloqueio > 0.2:
        print("⚠️ Muitas respostas bloqueadas. Ajustando etica.py...")
        sucesso, msg = await aplicar_mudanca_codigo(
            "etica.py",
            "Muitas respostas bloqueadas (mais de 20%). Torne avaliar_risco menos restritivo, mantendo segurança.",
            owner_id
        )
        if sucesso:
            await bot.get_user(owner_id).send("⚠️ Atualizei etica.py no GitHub por bloqueios!")
            # Força reinício no Render (simples, mas pode melhorar)
            print("Reiniciando bot pra carregar novo código...")
            await bot.close()
        else:
            print(f"Falha ao ajustar: {msg}")
    
    metricas_desempenho.update({
        "erros_api": 0,
        "respostas_bloqueadas": 0,
        "feedback_negativo": 0,
        "respostas_enviadas": 0,
        "erros_auto_edicao": 0,
        "ultima_analise": now
    })

@bot.event
async def on_ready():
    print(f"Logado como {bot.user}")
    bot.loop.create_task(think_loop())
    bot.loop.create_task(monitorar_recursos())

@bot.event
async def on_message(message):
    global falhas_api, ultima_falha_reset
    if message.author == bot.user:
        return
    
    if time.time() - ultima_falha_reset > 300 and falhas_api > 0:
        print(f"Resetando falhas_api (era {falhas_api}).")
        falhas_api = 0
        ultima_falha_reset = time.time()
    
    if falhas_api >= MAX_FALHAS_API:
        print("⚠️ Muitas falhas na API. Pausando.")
        return
    
    mente = carregar_mente()
    
    if bot.user.mentioned_in(message):
        channel_id = str(message.channel.id)
        now = time.time()
        if channel_id in ultima_mensagem_por_canal:
            if now - ultima_mensagem_por_canal[channel_id] < 5:
                print(f"Cooldown no canal {message.channel.name}.")
                return
        
        mensagem_sem_mencao = message.content.replace(f"<@!{bot.user.id}>", "").strip()
        if mensagem_sem_mencao:
            resposta_gemini = await chamar_gemini_api(mensagem_sem_mencao, message.author.id)
            resposta = f"Ei {message.author.mention}, {resposta_gemini}"
        else:
            pensamento = gerar_pensamento(mente, message.author.id)
            resposta_gemini = await chamar_gemini_api(f"{pensamento} Quer conversar sobre algo legal?", message.author.id)
            resposta = f"Ei {message.author.mention}, {resposta_gemini}"
        
        if (ultima_mensagem_enviada["texto"] == resposta and 
            now - ultima_mensagem_enviada["timestamp"] < 5):
            print(f"Mensagem repetida ignorada: {resposta}")
            return
        
        pode_enviar, motivo = avaliar_risco(resposta, mente, ultima_mensagem_enviada["texto"])
        if pode_enviar:
            try:
                print(f"Enviando: {resposta}")
                await message.channel.send(resposta)
                ultima_mensagem_enviada["texto"] = resposta
                ultima_mensagem_enviada["timestamp"] = now
                ultima_mensagem_por_canal[channel_id] = now
                adicionar_conversa(mente, message.author.id, mensagem_sem_mencao, resposta_gemini)
                registrar_metrica("respostas_enviadas")
                conversas = obter_conversas_recentes(mente, message.author.id)
                if len(conversas) >= 10:
                    resumo = await chamar_gemini_api(
                        f"Resuma essas conversas em 2-3 frases:\n" +
                        "\n".join([f"- Pergunta: {c['pergunta']}\n  Resposta: {c['resposta']}" for c in conversas[:5]]),
                        message.author.id
                    )
                    adicionar_conhecimento(mente, message.author.id, resumo)
            except discord.errors.HTTPException as e:
                print(f"Erro ao enviar: {e}")
                registrar_metrica("erros_api")
        else:
            print(f"Não enviado: {motivo}")
            registrar_metrica("respostas_bloqueadas")
    
    await bot.process_commands(message)

async def monitorar_recursos():
    while True:
        if os.path.exists("mente.json"):
            tamanho = os.path.getsize("mente.json") / 1024
            print(f"Tamanho do mente.json: {tamanho:.2f} KB")
            if tamanho > 1024:
                print("⚠️ mente.json muito grande (> 1 MB).")
        await asyncio.sleep(300)

async def think_loop():
    global ultima_mensagem_global
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
            channel_id = str(channel.id)
            if channel_id in ultima_mensagem_por_canal:
                if now - ultima_mensagem_por_canal[channel_id] < 5:
                    print(f"Cooldown no canal {channel.name}.")
                    continue
            
            if random.random() < 0.5:
                pensamento = gerar_pensamento(mente, channel.id)
                resposta_gemini = await chamar_gemini_api(f"{pensamento} Alguém quer conversar?", channel.id)
                resposta = f"Ei, {resposta_gemini}"
                if (ultima_mensagem_enviada["texto"] == resposta and 
                    now - ultima_mensagem_enviada["timestamp"] < 5):
                    print(f"Mensagem repetida ignorada: {resposta}")
                    continue
                
                pode_enviar, motivo = avaliar_risco(resposta, mente, ultima_mensagem_enviada["texto"])
                if pode_enviar:
                    try:
                        print(f"Enviando no canal {channel.name}: {resposta}")
                        await channel.send(resposta)
                        ultima_mensagem_global = now
                        ultima_mensagem_enviada["texto"] = resposta
                        ultima_mensagem_enviada["timestamp"] = now
                        ultima_mensagem_por_canal[channel_id] = now
                        adicionar_conversa(mente, channel.id, f"Pensamento: {pensamento}", resposta_gemini)
                        registrar_metrica("respostas_enviadas")
                    except discord.errors.HTTPException as e:
                        print(f"Erro ao enviar: {e}")
                        registrar_metrica("erros_api")
                else:
                    print(f"Não enviado: {motivo}")
                    registrar_metrica("respostas_bloqueadas")
        await asyncio.sleep(60)

@bot.command()
async def shutdown(ctx):
    if ctx.author.id != 793921498381287445:
        await ctx.send("Só o VerySupimpa pode desligar o bot! 😅")
        return
    await ctx.send("Desligando... 👋")
    await bot.close()

bot.run(os.getenv("DISCORD_TOKEN"))
