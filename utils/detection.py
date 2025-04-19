async def is_message_to_bot(message, bot_user):
    content = message.content.lower()
    if bot_user.mentioned_in(message):
        return True
    if "revolution" in content or "ai revolution" in content:
        return True
    return False
