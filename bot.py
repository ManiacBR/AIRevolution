import discord
import os
import openai

# Configura a chave da API OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Crie a instância do cliente do Discord
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# Evento quando o bot está pronto
@client.event
async def on_ready():
    print(f'Bot está conectado como {client.user}')

# Função para gerar resposta da OpenAI
async def generate_openai_response(prompt):
    response = openai.Completion.create(
        model="gpt-4.1",  # Usando o modelo GPT-4.1
        prompt=prompt,
        max_tokens=100
    )
    return response.choices[0].text.strip()

# Evento quando o bot recebe uma mensagem
@client.event
async def on_message(message):
    if message.author == client.user:  # Ignora o bot enviando mensagens
        return

    # Responde a um comando simples
    if message.content.lower() == "!hello":
        await message.channel.send("Olá, como você está?")

    # Exemplo de comando para interagir com o GPT-4
    elif message.content.lower().startswith("!ask "):
        prompt = message.content[5:]  # Remove o comando '!ask ' do início da mensagem
        response = await generate_openai_response(prompt)
        await message.channel.send(response)

# Obtém o token do bot a partir das variáveis de ambiente
token = os.getenv('DISCORD_TOKEN')

# Inicia o bot
client.run(token)
