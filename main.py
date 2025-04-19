import discord
import os
import json
from openai import OpenAI

# Carrega variáveis de ambiente
DISCORD_TOKEN   = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY")

# Inicializa cliente OpenAI (>=1.0.0)
oai = OpenAI(api_key=OPENAI_API_KEY)
MODEL = "gpt-4.1"  # Modelo principal da série GPT‑4.1

# 🧠 Memória persistente em arquivo
try:
    with open("memory.json", "r") as f:
        memory = json.load(f)
except FileNotFoundError:
    memory = []

def save_memory():
    with open("memory.json", "w") as f:
        json.dump(memory[-20:], f, indent=4)

# Configura Discord
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

async def generate_openai_response(prompt: str) -> str:
    memory.append({"role": "user", "content": prompt})
    try:
        resp = oai.chat.completions.create(
            model=MODEL,
            messages=memory[-20:],
            max_tokens=1000
        )
        reply = resp.choices[0].message.content
        memory.append({"role": "assistant", "content": reply})
        save_memory()
        return reply
    except Exception as e:
        return f"Erro ao gerar resposta: {e}"

@bot.event
async def on_ready():
    print(f"Conectado como {bot.user} (id: {bot.user.id})")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Quando alguém pergunta "quantos tokens" ou "qual modelo"
    content_lower = message.content.lower()
    if "qual modelo" in content_lower:
        await message.channel.send(f"Estou usando o modelo **{MODEL}** (GPT‑4.1 mais recente) 2")
        return

    # Responde menções normalmente
    if bot.user in message.mentions:
        prompt = (
            message.content
            .replace(f"<@{bot.user.id}>", "")
            .replace(f"<@!{bot.user.id}>", "")
            .strip()
        )
        if not prompt:
            await message.channel.send("Olá! Como posso ajudar?")
        else:
            await message.channel.typing()
            reply = await generate_openai_response(prompt)
            await message.reply(reply)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
