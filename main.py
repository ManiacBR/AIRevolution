import discord
import openai
import os
import json
import asyncio

from discord.ext import commands

# Configurações
MODEL = "gpt-4_1-2025-04-14"
MAX_INPUT_TOKENS = 950_000
MAX_OUTPUT_TOKENS = 950_000
MEMORY_FILE = "memory.json"
MEMORY_LIMIT = 100

# Carregar memória do arquivo
if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        memory = json.load(f)
else:
    memory = []

# Salvar memória no arquivo
def save_memory():
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2)

# Inicializar bot
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = commands.Bot(command_prefix="!", intents=intents)

openai.api_key = os.getenv("OPENAI_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

if not DISCORD_TOKEN:
    raise ValueError("Variável DISCORD_TOKEN não encontrada.")

# Verifica se o bot foi mencionado ou chamado pelo nome
def bot_foi_chamado(message: discord.Message):
    if client.user is None:
        return False
    chamado_direto = client.user in message.mentions
    chamado_por_nome = client.user.name.lower() in message.content.lower()
    return chamado_direto or chamado_por_nome

# Gerar resposta com OpenAI
async def gerar_resposta():
    context = memory[-MEMORY_LIMIT:]
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=context,
        max_tokens=MAX_OUTPUT_TOKENS,
    )
    return response.choices[0].message.content

@client.event
async def on_ready():
    print(f"Logado como {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if bot_foi_chamado(message):
        print(f"[+] Mensagem detectada: {message.content}")
        memory.append({"role": "user", "content": message.content})
        memory[:] = memory[-MEMORY_LIMIT:]  # Limitar memória

        try:
            resposta = await gerar_resposta()
            memory.append({"role": "assistant", "content": resposta})
            memory[:] = memory[-MEMORY_LIMIT:]
            save_memory()
            await message.channel.send(resposta)
        except Exception as e:
            await message.channel.send(f"Erro ao gerar resposta: {str(e)}")

client.run(DISCORD_TOKEN)
