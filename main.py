import discord
import os
import json
import asyncio
from datetime import datetime, timedelta
from openai import OpenAI
from collections import defaultdict
import tiktoken

# Carregar variáveis de ambiente
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Validação do token
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN está vazio ou não foi configurado no ambiente.")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY está vazio ou não foi configurado no ambiente.")

openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Função para contar os tokens
def contar_tokens(messages):
    try:
        encoding = tiktoken.get_encoding("o200k_base")
    except:
        encoding = tiktoken.get_encoding("cl100k_base")
    total_tokens = 0
    for msg in messages:
        if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
            continue
        total_tokens += 4
        for key, value in msg.items():
            total_tokens += len(encoding.encode(str(value)))
        total_tokens += 2
    return total_tokens

# Função para resumir memória
async def summarize_memory(memory):
    if len(memory) < 10:
        return memory
    prompt = [{"role": "system", "content": "Resuma o seguinte histórico de conversa em até 200 palavras, mantendo o contexto essencial."}, {"role": "user", "content": json.dumps(memory)}]
    response = openai_client.chat.completions.create(
        model="gpt-4.1-2025-04-14",
        messages=prompt,
        temperature=0.5,
        max_tokens=500
    )
    summary = response.choices[0].message.content
    return [{"role": "system", "content": f"Resumo do histórico: {summary}"}]

# Função para interagir com o OpenAI
async def ask_openai(memory, language="pt"):
    try:
        prompt = [
            {
                "role": "system",
                "content": (
                    f"Você é o Revolution, um assistente virtual baseado no modelo gpt-4.1-2025-04-14, criado para ajudar no Discord. "
                    f"Seu conhecimento é atualizado até abril de 2025, permitindo respostas precisas e recentes. "
                    f"Responda em {language}, mantendo um tom natural e amigável. "
                    f"Se perguntado sobre seu modelo ou identidade, informe que você é o Revolution, baseado no gpt-4.1-2025-04-14."
                )
            }
        ] + memory
        response = openai_client.chat.completions.create(
            model="gpt-4.1-2025-04-14",
            messages=prompt,
            temperature=0.7,
            max_tokens=2048
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Erro na API da OpenAI: {e}")
        return f"Erro ao chamar a API: {str(e)}"

# Configurações
MEMORY_FILE = "memory.json"
CONFIG_FILE = "config.json"
MAX_MEMORY_MESSAGES = 100
MAX_TOKENS = 100_000
COOLDOWN_SECONDS = 60
MAX_MESSAGES_PER_COOLDOWN = 5

# Configurações do Discord
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)

# Carrega memória e configuração
try:
    with open(MEMORY_FILE, "r") as f:
        memory = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    memory = []

try:
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
except FileNotFoundError:
    config = {"allowed_channels": [], "user_languages": {}}

# Cooldowns
user_cooldowns = defaultdict(lambda: {"count": 0, "last_time": None})

# Função para verificar intenção de deleção
async def is_delete_intent(message_content, language="pt"):
    try:
        prompt = [
            {"role": "system", "content": f"Determine se a mensagem indica uma intenção de deletar uma mensagem no Discord. Responda apenas 'sim' ou 'não' em {language}."},
            {"role": "user", "content": message_content}
        ]
        response = openai_client.chat.completions.create(
            model="gpt-4.1-2025-04-14",
            messages=prompt,
            temperature=0.3,
            max_tokens=10
        )
        return response.choices[0].message.content.lower() == "sim"
    except Exception as e:
        print(f"Erro ao verificar intenção de deleção: {e}")
        return False

@client.event
async def on_ready():
    print(f"Bot conectado como {client.user}")

@client.event
async def on_message(message):
    global memory
    print(f"Mensagem recebida: {message.content}")
    if message.author == client.user:
        return

    # Verificar cooldown
    user_id = str(message.author.id)
    now = datetime.now()
    if user_cooldowns[user_id]["last_time"] and now - user_cooldowns[user_id]["last_time"] < timedelta(seconds=COOLDOWN_SECONDS):
        if user_cooldowns[user_id]["count"] >= MAX_MESSAGES_PER_COOLDOWN:
            await message.channel.send("Você está enviando mensagens rápido demais. Tente novamente em um minuto.")
            return
        user_cooldowns[user_id]["count"] += 1
    else:
        user_cooldowns[user_id] = {"count": 1, "last_time": now}

    # Verifica se a mensagem é uma menção
    if client.user.mentioned_in(message) or "revolution" in message.content.lower():
        if not config["allowed_channels"] or message.channel.id in config["allowed_channels"]:
            try:
                msg_content = message.content.lower()
                channel = message.channel
                language = config["user_languages"].get(user_id, "pt")  # Default para português

                # Verificar intenção de deleção
                if await is_delete_intent(message.content, language) and message.reference:
                    try:
                        referenced_message = await message.channel.fetch_message(message.reference.message_id)
                        permissions = message.channel.permissions_for(message.guild.me)
                        if not permissions.manage_messages:
                            await channel.send("Não tenho permissão para deletar mensagens neste canal. Por favor, verifique se tenho a permissão 'Gerenciar Mensagens'.")
                            return
                        await referenced_message.delete()
                        await channel.send("Mensagem referenciada deletada!")
                    except discord.errors.Forbidden:
                        await channel.send("Não tenho permissão para deletar mensagens neste canal. Por favor, verifique se tenho a permissão 'Gerenciar Mensagens'.")
                    except discord.errors.NotFound:
                        await channel.send("A mensagem referenciada não foi encontrada.")
                    except Exception as e:
                        print(f"Erro ao deletar mensagem referenciada: {e}")
                        await channel.send("Erro ao tentar deletar a mensagem referenciada.")
                    return
                elif await is_delete_intent(message.content, language):
                    await channel.send("Por favor, responda à mensagem que deseja apagar.")
                    return

                # Resposta padrão
                memory.append({"role": "user", "content": message.content})
                if len(memory) > MAX_MEMORY_MESSAGES:
                    memory = await summarize_memory(memory[-MAX_MEMORY_MESSAGES:])
                while contar_tokens(memory) > MAX_TOKENS:
                    memory = memory[1:]
                reply = await ask_openai(memory, language)
                memory.append({"role": "assistant", "content": reply})

                try:
                    with open(MEMORY_FILE, "w") as f:
                        json.dump(memory, f, indent=2)
                except IOError as e:
                    print(f"Erro ao salvar memória: {e}")
                await channel.send(reply)
            except Exception as e:
                print(f"Erro no processamento da mensagem: {e}")
                await channel.send("Desculpe, ocorreu um erro ao processar sua mensagem.")
        else:
            await channel.send("Por favor, use este bot em um canal permitido.")

# Rodar o bot
client.run(DISCORD_TOKEN)
