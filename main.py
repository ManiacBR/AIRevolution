import discord
import os
from dotenv import load_dotenv
from ai import ask_openai
from database import ConversationDatabase

load_dotenv()

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True

client = discord.Client(intents=intents)
db = ConversationDatabase()

BOT_NAME = "Revolution"

def is_message_to_bot(message: discord.Message):
    return (
        message.author != client.user and (
            client.user.mentioned_in(message) or
            message.content.lower().startswith(BOT_NAME.lower())
        )
    )

@client.event
async def on_ready():
    print(f'Bot {client.user.name} conectado com sucesso.')

@client.event
async def on_message(message):
    if not is_message_to_bot(message):
        return

    user_input = message.content.replace(f"<@{client.user.id}>", "").replace(BOT_NAME, "").strip()

    # Pega contexto anterior da conversa
    context = db.get_context(str(message.author.id), str(message.guild.id))
    context.append(user_input)

    # Envia para o OpenAI
    response = await ask_openai(context)

    # Salva no banco de dados
    db.save_message(str(message.author.id), str(message.guild.id), user_input)
    db.save_message(str(message.author.id), str(message.guild.id), response)

    await message.channel.send(response)

if __name__ == "__main__":
    client.run(os.getenv("DISCORD_TOKEN"))
