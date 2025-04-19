import discord
import openai
import json
import os

from openai import OpenAIError
from discord.ext import commands

# Token de segurança
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY
client_openai = openai.OpenAI()

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Limite total de tokens
MAX_INPUT_TOKENS = 950000
MAX_OUTPUT_TOKENS = 950000

total_input_tokens = 0
total_output_tokens = 0

# Memória
MEMORY_FILE = "memory.json"
if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        memory = json.load(f)
else:
    memory = []

def save_memory():
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2, ensure_ascii=False)

async def generate_openai_response(prompt):
    global total_input_tokens, total_output_tokens

    messages = memory[-20:] + [{"role": "user", "content": prompt}]

    try:
        response = client_openai.chat.completions.create(
            model="o4-mini-2025-04-16",
            messages=messages,
            max_completion_tokens=500,
            temperature=0.7,
        )
        reply = response.choices[0].message.content.strip()
        total_input_tokens += response.usage.prompt_tokens
        total_output_tokens += response.usage.completion_tokens
        return reply

    except OpenAIError as e:
        print(f"[Erro o4-mini] {e}")

        try:
            response = client_openai.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=messages,
                max_tokens=500,
                temperature=0.7,
            )
            reply = response.choices[0].message.content.strip()
            total_input_tokens += response.usage.prompt_tokens
            total_output_tokens += response.usage.completion_tokens
            return reply
        except Exception as fallback_error:
            return f"Erro ao gerar resposta: {fallback_error}"

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}!')

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.lower()
    mentioned = bot.user in message.mentions
    has_name = bot.user.name.lower() in content

    if mentioned or has_name:
        prompt = message.content.replace(f"<@{bot.user.id}>", "").strip()
        
        if "quantos tokens" in prompt:
            await message.channel.send(f"Uso atual:\nInput: {total_input_tokens} / 950000\nOutput: {total_output_tokens} / 950000")
            return

        response = await generate_openai_response(prompt)
        memory.append({"role": "user", "content": prompt})
        memory.append({"role": "assistant", "content": response})
        save_memory()

        await message.channel.send(response)

bot.run(DISCORD_TOKEN)
