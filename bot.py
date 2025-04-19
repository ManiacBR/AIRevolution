# bot.py

import os
import discord
from openai import OpenAI

# Carrega tokens das variáveis de ambiente
DISCORD_TOKEN   = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY")

# Instancia o client da OpenAI (v1.0.0+)
oai = OpenAI(api_key=OPENAI_API_KEY)

# Configurações do Discord
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

async def generate_openai_response(prompt: str) -> str:
    try:
        resp = oai.chat.completions.create(
            model="gpt-4.1-2025-04-14",      # ou "gpt-4.1" se não usar data-specific
            messages=[{"role": "user", "content": prompt}],
        )
        # retorna só o conteúdo da mensagem
        return resp.choices[0].message.content
    except Exception as e:
        return f"Erro ao gerar resposta: {e}"

@bot.event
async def on_ready():
    print(f"🔌 Conectado como {bot.user} (id: {bot.user.id})")

@bot.event
async def on_message(message):
    # ignora bots (incluindo ele mesmo)
    if message.author.bot:
        return

    # verifica se foi mencionado
    if bot.user in message.mentions:
        # retira todas as formas de menção ao bot do conteúdo
        prompt = (
            message.content
            .replace(f"<@{bot.user.id}>", "")
            .replace(f"<@!{bot.user.id}>", "")
            .strip()
        )

        if not prompt:
            await message.channel.send("Olá! Como posso ajudar?")
        else:
            resposta = await generate_openai_response(prompt)
            await message.channel.send(resposta)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
