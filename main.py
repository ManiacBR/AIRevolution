import discord
import os
import json
import asyncio
import tiktoken
from openai import OpenAI

# Definir variáveis diretamente no código
DISCORD_TOKEN = "seu_token_do_discord"  # Coloque o seu token do Discord aqui
OPENAI_API_KEY = "sua_chave_da_openai"  # Coloque sua chave da API da OpenAI aqui

if not DISCORD_TOKEN:
    raise ValueError("Variável DISCORD_TOKEN não encontrada.")
if not OPENAI_API_KEY:
    raise ValueError("Variável OPENAI_API_KEY não encontrada.")

openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Função para contar os tokens
def contar_tokens(messages):
    encoding = tiktoken.encoding_for_model("gpt-4")
    total_tokens = 0
    for msg in messages:
        total_tokens += 4  # tokens fixos por mensagem
        for key, value in msg.items():
            total_tokens += len(encoding.encode(value))
        total_tokens += 2  # priming tokens
    return total_tokens

# Configurações de memória
MEMORY_FILE = "memory.json"
MAX_MEMORY_MESSAGES = 100
MAX_TOKENS = 950_000

# Configurações do Discord
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)

# Carrega memória
try:
    with open(MEMORY_FILE, "r") as f:
        memory = json.load(f)
except FileNotFoundError:
    memory = []

# Função para interagir com o OpenAI
async def ask_openai(memory):
    response = openai_client.chat.completions.create(
        model="gpt-4_1-2025-04-14",
        messages=memory,
        temperature=0.7,
        max_tokens=2048
    )
    return response.choices[0].message.content

@client.event
async def on_ready():
    print(f"Bot conectado como {client.user}")

@client.event
async def on_message(message):
    global memory
    if message.author == client.user:
        return

    # Verifica se o bot foi mencionado ou se está no texto
    if client.user.mentioned_in(message) or client.user.name.lower() in message.content.lower():
        memory.append({"role": "user", "content": message.content})

        # Reduz memória se passar o limite de mensagens
        if len(memory) > MAX_MEMORY_MESSAGES:
            memory = memory[-MAX_MEMORY_MESSAGES:]

        # Reduz memória se passar limite de tokens
        while contar_tokens(memory) > MAX_TOKENS:
            memory = memory[1:]

        # Resposta da IA
        reply = await ask_openai(memory)
        memory.append({"role": "assistant", "content": reply})

        # Salva memória
        with open(MEMORY_FILE, "w") as f:
            json.dump(memory, f, indent=2)

        # Envia a resposta
        await message.channel.send(reply)

# Rodar o bot
client.run(DISCORD_TOKEN)
