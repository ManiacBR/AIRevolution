import discord
import openai
import json
import os

# Variáveis do ambiente
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Inicializa cliente
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Configura OpenAI
openai.api_key = OPENAI_API_KEY
MODEL = "gpt-4.1-2025-04-14"

# Carrega memória
try:
    with open("memory.json", "r") as f:
        memory = json.load(f)
except FileNotFoundError:
    memory = []

# Salva memória
def save_memory():
    with open("memory.json", "w") as f:
        json.dump(memory[-20:], f, indent=4)  # mantém últimas 20 interações

# Gera resposta com OpenAI
async def generate_response(user_message):
    memory.append({"role": "user", "content": user_message})
    try:
        response = openai.chat.completions.create(
            model=MODEL,
            messages=memory[-20:],  # mantemos só o contexto mais recente
            max_tokens=1000
        )
        reply = response.choices[0].message.content
        memory.append({"role": "assistant", "content": reply})
        save_memory()
        return reply
    except Exception as e:
        return f"Erro ao gerar resposta: {e}"

# Evento de mensagem
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if client.user.mentioned_in(message) or message.channel.type.name == "private":
        await message.channel.typing()
        response = await generate_response(message.content)
        await message.reply(response)

# Inicia bot
client.run(DISCORD_TOKEN)
