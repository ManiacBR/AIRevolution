import discord
import openai
import os
import json
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not DISCORD_TOKEN:
    raise ValueError("Variável DISCORD_BOT_TOKEN não encontrada.")
if not OPENAI_API_KEY:
    raise ValueError("Variável OPENAI_API_KEY não encontrada.")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

client = discord.Client(intents=intents)
openai.api_key = OPENAI_API_KEY

MEMORY_FILE = "memory.json"

# Carrega memória do arquivo
if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        memory = json.load(f)
else:
    memory = {}

def save_memory():
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

@client.event
async def on_ready():
    print(f"[INFO] Bot conectado como {client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    channel_id = str(message.channel.id)
    user_input = message.content.strip()

    # Adiciona a nova mensagem à memória
    if channel_id not in memory:
        memory[channel_id] = []
    memory[channel_id].append({"role": "user", "content": user_input})

    # Mantém até 20 mensagens na memória
    memory[channel_id] = memory[channel_id][-20:]

    try:
        response = openai.chat.completions.create(
            model="gpt-4_1-2025-04-14",
            messages=memory[channel_id],
            max_tokens=500,
            temperature=0.7,
        )

        ai_reply = response.choices[0].message.content

        # Adiciona resposta da IA à memória
        memory[channel_id].append({"role": "assistant", "content": ai_reply})
        save_memory()

        await message.channel.send(ai_reply)

    except Exception as e:
        print("[ERRO AO CHAMAR OPENAI]", e)
        await message.channel.send("Ocorreu um erro ao gerar a resposta da IA.")

client.run(DISCORD_TOKEN)
