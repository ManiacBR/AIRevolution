import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from ai import AIRevolution
from database import ConversationDatabase
from voice import VoiceHandler
import asyncio

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix="~", intents=intents)  # Prefixo fictício para evitar CommandNotFound
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
    ctx = await bot.get_context(message)

    # Processa comandos sem prefixo primeiro
    if content.startswith("limpar") or "limpa o chat" in content:
        if ctx.author.guild_permissions.manage_messages:
            try:
                limit = 100
                if len(content.split()) > 1 and content.split()[1].isdigit():
                    limit = min(int(content.split()[1]), 100)
                await ctx.channel.purge(limit=limit)
                await ctx.send(f"{limit} mensagens limpas com sucesso!", delete_after=5)
            except discord.HTTPException:
                await ctx.send("Erro ao limpar mensagens. Verifique minhas permissões ou tente novamente.")
        else:
            await ctx.send("Você precisa de permissão para gerenciar mensagens.")
        return  # Impede a IA de responder
    elif content.startswith("apagar") or "apaga essa" in content:
        if ctx.author.guild_permissions.manage_messages:
            try:
                if message.reference:
                    target_message = await ctx.channel.fetch_message(message.reference.message_id)
                    await target_message.delete()
                    await ctx.send("Mensagem apagada com sucesso!", delete_after=5)
                elif len(content.split()) > 1 and content.split()[1].isdigit():
                    message_id = int(content.split()[1])
                    target_message = await ctx.channel.fetch_message(message_id)
                    await target_message.delete()
                    await ctx.send("Mensagem apagada com sucesso!", delete_after=5)
                else:
                    await ctx.send("Por favor, forneça um ID de mensagem ou responda à mensagem que deseja apagar.")
            except discord.NotFound:
                await ctx.send("Mensagem não encontrada.")
            except discord.HTTPException:
                await ctx.send("Erro ao apagar a mensagem. Verifique minhas permissões.")
        else:
            await ctx.send("Você precisa de permissão para gerenciar mensagens.")
        return  # Impede a IA de responder
    elif content.startswith("voz"):
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            voice_client = await channel.connect()
            asyncio.create_task(voice_handler.handle_voice_interaction(voice_client, ai, ctx.channel))
            await ctx.send("Conectado ao canal de voz! Fale comigo!")
        else:
            await ctx.send("Você precisa estar em um canal de voz!")
        return  # Impede a IA de responder
    elif content.startswith("sair") or "sai da voz" in content:
        if ctx.guild.voice_client:
            await ctx.guild.voice_client.disconnect()
            await ctx.send("Desconectado do canal de voz!")
        else:
            await ctx.send("Não estou em nenhum canal de voz!")
        return  # Impede a IA de responder
    # Responde se mencionado ou se o nome "AI Revolution" aparece (exceto para comandos)
    elif bot.user.mentioned_in(message) or "ai revolution" in content or "revolution" in content:
        # Obtém contexto da conversa
        context = db.get_context(str(message.author.id), str(message.guild.id))
        # Gera resposta em português
        response = await ai.generate_response(
            message.content,
            context,
            extra_instruction="Responda sempre em português, independentemente do idioma da mensagem."
        )
        # Salva a mensagem no banco
        db.save_message(str(message.author.id), str(message.guild.id), message.content)
        # Envia resposta
        await message.channel.send(response)

    # Não processa comandos automáticos para evitar CommandNotFound
    # await bot.process_commands(message)

bot.run(os.getenv("DISCORD_TOKEN"))
