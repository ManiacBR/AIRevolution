import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from ai import AIRevolution
from database import ConversationDatabase
from voice import VoiceHandler
import asyncio
import logging

# Configura logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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
    logger.info(f"Logado como {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content = message.content.lower()
    ctx = await bot.get_context(message)
    logger.info(f"Processando mensagem: {content}")

    # Processa comandos sem prefixo primeiro
    try:
        if content.startswith("limpar") or "limpa o chat" in content:
            if ctx.author.guild_permissions.manage_messages:
                try:
                    limit = 100
                    if len(content.split()) > 1 and content.split()[1].isdigit():
                        limit = min(int(content.split()[1]), 100)
                    await ctx.channel.purge(limit=limit)
                    await ctx.send(f"{limit} mensagens limpas com sucesso!", delete_after=5)
                    logger.info(f"Limpou {limit} mensagens no canal {ctx.channel.id}")
                except discord.HTTPException as e:
                    await ctx.send("Erro ao limpar mensagens. Verifique minhas permissões ou tente novamente.")
                    logger.error(f"Erro ao limpar mensagens: {str(e)}")
            else:
                await ctx.send("Você precisa de permissão para gerenciar mensagens.")
                logger.warning(f"Usuário {ctx.author.id} sem permissão para limpar")
            return
        elif content.startswith("apagar") or "apaga essa" in content:
            if ctx.author.guild_permissions.manage_messages:
                try:
                    if message.reference:
                        target_message = await ctx.channel.fetch_message(message.reference.message_id)
                        await target_message.delete()
                        await ctx.send("Mensagem apagada com sucesso!", delete_after=5)
                        logger.info(f"Mensagem {message.reference.message_id} apagada")
                    elif len(content.split()) > 1 and content.split()[1].isdigit():
                        message_id = int(content.split()[1])
                        target_message = await ctx.channel.fetch_message(message_id)
                        await target_message.delete()
                        await ctx.send("Mensagem apagada com sucesso!", delete_after=5)
                        logger.info(f"Mensagem {message_id} apagada")
                    else:
                        await ctx.send("Por favor, forneça um ID de mensagem ou responda à mensagem que deseja apagar.")
                        logger.warning("Comando apagar sem ID ou referência")
                except discord.NotFound:
                    await ctx.send("Mensagem não encontrada.")
                    logger.error("Mensagem não encontrada para apagar")
                except discord.HTTPException as e:
                    await ctx.send("Erro ao apagar mensagem. Verifique minhas permissões.")
                    logger.error(f"Erro ao apagar mensagem: {str(e)}")
            else:
                await ctx.send("Você precisa de permissão para gerenciar mensagens.")
                logger.warning(f"Usuário {ctx.author.id} sem permissão para apagar")
            return
        elif content.startswith("voz"):
            if ctx.author.voice:
                channel = ctx.author.voice.channel
                voice_client = await channel.connect()
                asyncio.create_task(voice_handler.handle_voice_interaction(voice_client, ai, ctx.channel))
                await ctx.send("Conectado ao canal de voz! Fale comigo!")
                logger.info(f"Conectado ao canal de voz {channel.id}")
            else:
                await ctx.send("Você precisa estar em um canal de voz!")
                logger.warning(f"Usuário {ctx.author.id} não está em canal de voz")
            return
        elif content.startswith("sair") or "sai da voz" in content:
            if ctx.guild.voice_client:
                await ctx.guild.voice_client.disconnect()
                await ctx.send("Desconectado do canal de voz!")
                logger.info("Desconectado do canal de voz")
            else:
                await ctx.send("Não estou em nenhum canal de voz!")
                logger.warning("Comando sair sem conexão de voz ativa")
            return
        # Responde se mencionado ou se o nome "AI Revolution" aparece
        elif bot.user.mentioned_in(message) or "ai revolution" in content or "revolution" in content:
            # Verifica mensagem referenciada
            referenced_content = ""
            if message.reference:
                try:
                    referenced_message = await ctx.channel.fetch_message(message.reference.message_id)
                    referenced_content = f"Mensagem referenciada: {referenced_message.content}\n"
                    logger.info(f"Mensagem referenciada encontrada: {referenced_message.content}")
                except discord.NotFound:
                    logger.warning("Mensagem referenciada não encontrada")
            # Obtém contexto da conversa
            context = db.get_context(str(message.author.id), str(message.guild.id))
            # Inclui mensagem referenciada no prompt
            prompt = f"{referenced_content}{message.content}"
            response = await ai.generate_response(
                prompt,
                context,
                extra_instruction="Responda sempre em português, considerando o contexto da mensagem referenciada, se houver."
            )
            db.save_message(str(message.author.id), str(message.guild.id), message.content)
            await message.channel.send(response)
            logger.info(f"Respondeu à mensagem de {message.author.id}: {response[:50]}...")
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {str(e)}")
        await ctx.send(f"Erro inesperado: {str(e)}")

    # Não processa comandos automáticos
    # await bot.process_commands(message)

bot.run(os.getenv("DISCORD_TOKEN"))
