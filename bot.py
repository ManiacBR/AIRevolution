import discord
import os
import openai

# Configura a chave da API OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Configura os limites de tokens
MAX_INPUT_TOKENS = 950000  # Limite máximo de tokens de input
MAX_OUTPUT_TOKENS = 950000  # Limite máximo de tokens de output

# Inicializa o contador de tokens
used_input_tokens = 0
used_output_tokens = 0

# Crie a instância do cliente do Discord
intents = discord.Intents.default()
intents.messages = True  # Permite que o bot leia mensagens
client = discord.Client(intents=intents)

# Evento quando o bot está pronto
@client.event
async def on_ready():
    print(f'Bot está conectado como {client.user}')

# Função para gerar resposta da OpenAI
async def generate_openai_response(prompt):
    global used_input_tokens, used_output_tokens

    # Verifica se o uso total de tokens ultrapassou o limite
    if used_input_tokens + used_output_tokens >= MAX_INPUT_TOKENS + MAX_OUTPUT_TOKENS:
        return "Limite de tokens atingido. Não posso mais responder."

    # Faz a requisição para o modelo GPT-4
    response = openai.Completion.create(
        model="gpt-4.1-2025-04-14",  # Usando o modelo específico
        prompt=prompt,
        max_tokens=100
    )

    # Calcula e atualiza os tokens usados
    input_tokens = len(prompt.split())  # Estima o número de tokens de input
    output_tokens = response.usage['total_tokens']  # Tokens de output
    used_input_tokens += input_tokens
    used_output_tokens += output_tokens

    # Retorna a resposta gerada
    return response.choices[0].text.strip()

# Evento quando o bot recebe uma mensagem
@client.event
async def on_message(message):
    # Ignora o bot respondendo a si mesmo
    if message.author == client.user:
        return

    # Verifica se o bot foi mencionado diretamente
    if client.user.mentioned_in(message):
        # Exclui a menção (o nome do bot) da mensagem para enviar a resposta limpa
        prompt = message.content.replace(f"@{client.user.name}", "").strip()

        # Se houver conteúdo após a menção, gera a resposta
        if prompt:
            print(f"Mensagem direcionada ao bot: {message.content}")  # Verifica se a mensagem foi direcionada ao bot
            response = await generate_openai_response(prompt)
            await message.channel.send(response)
        else:
            # Se não houver nada após a menção, o bot pode responder algo padrão
            await message.channel.send("Olá! Como posso ajudar?")

# Obtém o token do bot a partir das variáveis de ambiente
token = os.getenv('DISCORD_TOKEN')

# Inicia o bot
client.run(token)
