import discord
import openai
import os
import json
import tiktoken
from datetime import datetime
from collections import deque

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

openai.api_key = os.getenv("OPENAI_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Limites
MAX_TOKENS_IN = 950000
MAX_TOKENS_OUT = 950000
CONTEXT_LIMIT = 100
MEMORY_FILE = "memory.json"
MODEL_NAME = "gpt-4_1-2025-04-14"

# Codificador de tokens
encoding = tiktoken.encoding_for_model("gpt-4")

# Prompt base pra IA se identificar
base_prompt = {
    "role": "system",
    "content": (
        f"Você é uma IA avançada usando o modelo {MODEL_NAME}. Você tem memória de longo prazo salva em arquivo "
        f"e responde automaticamente sempre que for mencionada ou perceber que estão falando com você. "
        f"Seu objetivo é manter conversas naturais, com contexto e sem a necessidade de comandos. "
        f"Use até 950 mil tokens no input e no output."
    )
}

# Carregar memória
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return deque(data, maxlen=CONTEXT_LIMIT)
    return deque(maxlen=CONTEXT_LIMIT)

# Salvar memória
def save_memory(memory):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(list(memory), f, ensure_ascii=False, indent=2)

# Calcular tokens
def count_tokens(messages):
    total = 0
    for m in messages:
        total += len(encoding.encode(m["content"]))
    return total

# Responder com IA
async def ask_openai(memory):
    messages = [base_prompt] + list(memory)
    input_tokens = count_tokens(messages)
    if input_tokens > MAX_TOKENS_IN:
        print("[WARNING] Tokens de entrada excederam o limite.")

    response = openai.ChatCompletion.create(
        model="gpt-4-1106-preview",
        messages=messages,
        max_tokens=MAX_TOKENS_OUT,
    )
    return response.choices[0].message["content"]

# Verifica se foi mencionado ou citado indiretamente
def bot_was_called(message):
    return client.user.mentioned_in(message) or client.user.name.lower() in message.content.lower()

# Memória atual
memory = load_memory()

@client.event
async def on_ready():
    print(f"[READY] Logado como {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user or not bot_was_called(message):
        return

    print(f"[MSG] {message.author}: {message.content}")

    memory.append({"role": "user", "content": message.content})
    reply = await ask_openai(memory)
    memory.append({"role": "assistant", "content": reply})
    save_memory(memory)

    await message.channel.send(reply)

client.run(DISCORD_TOKEN)
