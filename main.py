import discord
import os
import json
import asyncio
import tiktoken
from openai import OpenAI

# Carregar variáveis de ambiente
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Validação do token
print(f"Token carregado: {DISCORD_TOKEN[:10] if DISCORD_TOKEN else 'Nenhum token encontrado'}...")
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN está vazio ou não foi configurado no ambiente da Railway.")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY está vazio ou não foi configurado no ambiente da Railway.")

openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Função para contar os tokens
def contar_tokens(messages):
    encoding = tiktoken.encoding_for_model("gpt-4.1-2025-04-14")
    total_tokens = 0
    for msg in messages:
        if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
            continue
        total_tokens += 4
        for key, value in msg.items():
            total_tokens += len(encoding.encode(str(value)))
        total_tokens += 2
    return total_tokens

# Configurações de memória
MEMORY_FILE = "memory.json"
MAX_MEMORY_MESSAGES = 100
MAX_TOKENS = 100_000

# Configurações do Discord
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)

# Carrega memória
try:
    with open(MEMORY_FILE, "r") as f:
        memory = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    memory = []

# Função para interagir com o OpenAI
async def ask_openai(memory):
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4.1-2025-04-14",  # Mantido conforme sua instrução
            messages=memory,
            temperature=0.7,
            max_tokens=2048
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Erro na API da OpenAI: {e}")
        return "Desculpe, ocorreu um erro ao processar sua solicitação."

@client.event
async def on_ready():
    print(f"Bot conectado como {client.user}")

@client.event
async def on_message(message):
    global memory
    print(f"Mensagem recebida: {message.content}")
    if message.author == client.user:
        return

    if client.user.mentioned_in(message) or client.user.name.lower() in message.content.lower():
        memory.append({"role": "user", "content": message.content})

        if len(memory) > MAX_MEMORY_MESSAGES:
            memory = memory[-MAX_MEMORY_MESSAGES:]

        while contar_tokens(memory) > MAX_TOKENS:
            memory = memory[1:]

        reply = await ask_openai(memory)
        memory.append({"role": "assistant", "content": reply})

        try:
            with open(MEMORY_FILE, "w") as f:
                json.dump(memory, f, indent=2)
        except IOError as e:
            print(f"Erro ao salvar memória: {e}")

        await message.channel.send(reply)

# Rodar o bot
client.run(DISCORD_TOKEN)
