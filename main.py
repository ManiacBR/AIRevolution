import discord
import openai
import json
import os
from datetime import datetime

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)

openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4_1-2025-04-14"
MEMORY_FILE = "memory.json"

# Carrega a memória se existir
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# Salva a memória
def save_memory(memory):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2)

# Gera resposta com o modelo correto
async def generate_openai_response(memory, user_message):
    messages = memory + [{"role": "user", "content": user_message}]
    try:
        response = openai.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=1024
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Erro ao gerar resposta: {e}"

@client.event
async def on_ready():
    print(f"Logado como {client.user.name}")

@client.event
async def on_message(message):
    if message.author == client.user or message.channel.type.name != "text":
        return

    memory = load_memory()

    user_input = message.content
    memory.append({"role": "user", "content": user_input})

    response = await generate_openai_response(memory, user_input)
    memory.append({"role": "assistant", "content": response})

    save_memory(memory)

    await message.channel.send(response)

client.run(os.getenv("DISCORD_BOT_TOKEN"))
