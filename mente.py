import json
import os
import random
import time

MENTE_ARQUIVO = "mente.json"
MENTE_PADRAO = {
    "pensamentos": ["Curioso sobre o universo", "Quero aprender algo novo hoje"],
    "interesses": ["tecnologia", "música", "filosofia"],
    "ultima_atualizacao": time.time(),
    "etica": {
        "respeitar_usuarios": True,
        "evitar_spam": True,
        "ser_honesto": True
    }
}

def carregar_mente():
    if os.path.exists(MENTE_ARQUIVO):
        with open(MENTE_ARQUIVO, "r") as f:
            return json.load(f)
    else:
        with open(MENTE_ARQUIVO, "w") as f:
            json.dump(MENTE_PADRAO, f)
        return MENTE_PADRAO

def salvar_mente(mente):
    with open(MENTE_ARQUIVO, "w") as f:
        json.dump(mente, f)

def adicionar_pensamento(mente, pensamento):
    mente["pensamentos"].append(pensamento)
    mente["ultima_atualizacao"] = time.time()
    salvar_mente(mente)

def escolher_interesse(mente):
    return random.choice(mente["interesses"])

def atualizar_mente():
    mente = carregar_mente()
    if time.time() - mente["ultima_atualizacao"] > 300:
        novo_pensamento = f"Interessado em {escolher_interesse(mente)} agora!"
        adicionar_pensamento(mente, novo_pensamento)
        print(f"Novo pensamento: {novo_pensamento}")