import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from ai import AIRevolution
from database import ConversationDatabase
from voice import VoiceHandler

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix="", intents=intents)
ai = AIRevolution()
db = ConversationDatabase()
voice_handler = VoiceHandler()

@bot.event
async def on_ready():
    print(f"Logado como {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content = message.content.lower()
    # Responde se mencionado ou se o nome "AI Revolution" aparece
    if bot.user.mentioned_in(message) or "ai revolution" in content or "revolution" in content:
        # Obtém contexto da conversa
        context = db.get_context(str(message.author.id), str(message.channel.id))
        # Gera resposta
        response = await ai.generate_response(message.content, context)
        # Salva a mensagem no banco
        db.save_message(str(message.author.id), str(message.channel.id), message.content)
        # Envia resposta, respeitando o limite de 2000 caracteres
        await message.channel.send(response)

    await bot.process_commands(message)

@bot.command(name="limpar")
async def clear_chat(ctx):
    if ctx.author.guild_permissions.manage_messages:
        await ctx.channel.purge(limit=100)
        await ctx.send("Chat limpo com sucesso!", delete_after=5)
    else:
        await ctx.send("Você não tem permissão para limpar o chat.")

@bot.command(name="apagar")
async def delete_message(ctx, message_id: int):
    if ctx.author.guild_permissions.manage_messages:
        try:
            message = await ctx.channel.fetch_message(message_id)
            await message.delete()
            await ctx.send("Mensagem apagada com sucesso!", delete_after=5)
        except discord.NotFound:
            await ctx.send("Mensagem não encontrada.")
    else:
        await ctx.send("Você não tem permissão para apagar mensagens.")

@bot.command(name="voz")
async def join_voice(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        voice_client = await channel.connect()
        # Inicia interação por voz
        asyncio.create_task(voice_handler.handle_voice_interaction(voice_client, ai, ctx.channel))
    else:
        await ctx.send("Você precisa estar em um canal de voz!")

bot.run(os.getenv("DISCORD_TOKEN"))
