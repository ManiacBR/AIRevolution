import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def ask_openai(messages, model="gpt-4.1-2025-04-14"):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": m} for m in messages]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Ocorreu um erro: {e}"
