from openai import AsyncOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

class AIRevolution:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4.1-2025-04-14"

    async def generate_response(self, prompt, context=[]):
        messages = [
            {"role": "system", "content": "You are AI Revolution, a highly intelligent and friendly Discord bot inspired by Jarvis from Iron Man. Be concise, witty, and helpful. Keep responses under 2000 characters."}
        ]
        # Adiciona o contexto da conversa
        for msg in context:
            messages.append({"role": "user", "content": msg})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            text = response.choices[0].message.content.strip()
            # Garante que a resposta não exceda 2000 caracteres
            if len(text) > 2000:
                text = text[:1997] + "..."
            return text
        except Exception as e:
            return f"Erro ao processar a solicitação: {str(e)}"
