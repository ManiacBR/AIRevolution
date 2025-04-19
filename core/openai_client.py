import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

def get_response(memory, language="pt"):
    prompt = [
        {
            "role": "system",
            "content": (
                f"Você é o Revolution, um assistente baseado no modelo GPT-4.1, com conhecimento atualizado até abril de 2025. "
                f"Fale em {language} e mantenha um tom natural e útil."
            )
        }
    ] + memory

    response = openai.ChatCompletion.create(
        model="gpt-4.1-2025-04-14",
        messages=prompt,
        temperature=0.7,
        max_tokens=2048
    )

    return response["choices"][0]["message"]["content"]
