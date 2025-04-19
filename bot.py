import discord
import openai
import os

# Defina o seu token do Discord e a chave da OpenAI nas variáveis de ambiente
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Configura a chave da API da OpenAI
openai.api_key = OPENAI_API_KEY

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

async def generate_openai_response(prompt):
    try:
        # Correção: Usando a função correta para chat
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Modelo GPT-4
            messages=[{"role": "user", "content": prompt}],
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"Erro ao gerar resposta: {e}"

@client.event
async def on_ready():
    print(f'Logado como {client.user}')

@client.event
async def on_message(message):
    # Ignora as mensagens do próprio bot
    if message.author == client.user:
        return

    # Verifica se o bot foi mencionado
    if client.user in message.mentions:
        prompt = message.content
        response = await generate_openai_response(prompt)
        await message.channel.send(response)

client.run(DISCORD_TOKEN)
