import json
import os
import random
import time
from datetime import datetime

# Disco persistente no Render
MENTE_ARQUIVO = "/opt/render/project/data/mente.json"
MENTE_PADRAO = {
    "interesses": ["tecnologia", "música", "filosofia", "jogos", "ciência", "arte", "esportes", "culinária", "viagens", "história"],
    "ultima_atualizacao": time.time(),
    "etica": {
        "respeitar_usuarios": True,
        "evitar_spam": True,
        "ser_honesto": True
    },
    "conversas": {},
    "conhecimentos": {},
    "ultimos_tons": {}
}

def carregar_mente():
    os.makedirs(os.path.dirname(MENTE_ARQUIVO), exist_ok=True)
    if os.path.exists(MENTE_ARQUIVO):
        print(f"Carregando {MENTE_ARQUIVO}...")
        with open(MENTE_ARQUIVO, "r") as f:
            return json.load(f)
    else:
        print(f"Criando {MENTE_ARQUIVO}...")
        with open(MENTE_ARQUIVO, "w") as f:
            json.dump(MENTE_PADRAO, f)
        return MENTE_PADRAO

def salvar_mente(mente):
    print(f"Salvando {MENTE_ARQUIVO}...")
    with open(MENTE_ARQUIVO, "w") as f:
        json.dump(mente, f)

def escolher_interesse(mente):
    return random.choice(mente["interesses"])

def gerar_pensamento(mente, user_id=None):
    interesse = escolher_interesse(mente)
    hora_atual = datetime.now().hour
    momento = "manhã" if hora_atual < 12 else "tarde" if hora_atual < 18 else "noite"
    conversas = obter_conversas_recentes(mente, user_id) if user_id else []
    contexto_conversa = ""
    if conversas:
        ultima_pergunta = conversas[-1]["pergunta"]
        if "jogo" in ultima_pergunta.lower() and interesse != "jogos":
            contexto_conversa = "depois de falar sobre jogos "
    modelos_pensamento = [
        f"Estou pensando {contexto_conversa}em {interesse} nesta {momento}, será que alguém curte?",
        f"Hoje de {momento} me deu vontade de explorar algo sobre {interesse}, o que vocês acham?",
        f"Alguém já pensou {contexto_conversa}em {interesse} hoje? Tô curioso pra saber mais!"
    ]
    return random.choice(modelos_pensamento)

def atualizar_mente():
    mente = carregar_mente()
    if time.time() - mente["ultima_atualizacao"] > 300:
        mente["ultima_atualizacao"] = time.time()
        salvar_mente(mente)

def adicionar_conversa(mente, user_id, pergunta, resposta):
    user_id = str(user_id)
    if user_id not in mente["conversas"]:
        mente["conversas"][user_id] = []
    mente["conversas"][user_id].append({
        "pergunta": pergunta[:100],
        "resposta": resposta[:100],
        "timestamp": time.time()
    })
    if len(mente["conversas"][user_id]) > 10:
        mente["conversas"][user_id] = mente["conversas"][user_id][-10:]
    salvar_mente(mente)

def obter_conversas_recentes(mente, user_id):
    user_id = str(user_id)
    return mente["conversas"].get(user_id, [])

def adicionar_conhecimento(mente, user_id, conhecimento):
    user_id = str(user_id)
    if user_id not in mente["conhecimentos"]:
        mente["conhecimentos"][user_id] = []
    mente["conhecimentos"][user_id].append(conhecimento)
    if len(mente["conhecimentos"][user_id]) > 5:
        mente["conhecimentos"][user_id] = mente["conhecimentos"][user_id][-5:]
    salvar_mente(mente)

def obter_conhecimentos(mente, user_id):
    user_id = str(user_id)
    return mente["conhecimentos"].get(user_id, [])

def obter_ultimo_tom(user_id):
    mente = carregar_mente()
    user_id = str(user_id)
    return mente.get("ultimos_tons", {}).get(user_id, None)

def atualizar_tom(user_id, tom):
    mente = carregar_mente()
    user_id = str(user_id)
    if "ultimos_tons" not in mente:
        mente["ultimos_tons"] = {}
    mente["ultimos_tons"][user_id] = tom
    salvar_mente(mente)
