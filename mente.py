import json
import os
import random
import time
from datetime import datetime

MENTE_ARQUIVO = "mente.json"
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
    if os.path.exists(MENTE_ARQUIVO):
        print(f"Carregando mente.json existente: {MENTE_ARQUIVO}")
        with open(MENTE_ARQUIVO, "r") as f:
            return json.load(f)
    else:
        print(f"mente.json não encontrado, criando novo arquivo: {MENTE_ARQUIVO}")
        with open(MENTE_ARQUIVO, "w") as f:
            json.dump(MENTE_PADRAO, f)
        return MENTE_PADRAO

def salvar_mente(mente):
    print(f"Salvando mente.json: {MENTE_ARQUIVO}")
    with open(MENTE_ARQUIVO, "w") as f:
        json.dump(mente, f)

def escolher_interesse(mente):
    return random.choice(mente["interesses"])

def gerar_pensamento(mente, user_id=None):
    # Escolhe um interesse aleatório
    interesse = escolher_interesse(mente)
    
    # Adiciona contexto com base na hora do dia
    hora_atual = datetime.now().hour
    if hora_atual < 12:
        momento = "manhã"
    elif hora_atual < 18:
        momento = "tarde"
    else:
        momento = "noite"

    # Adiciona contexto com base nas conversas recentes, se houver
    conversas = obter_conversas_recentes(mente, user_id) if user_id else []
    contexto_conversa = ""
    if conversas:
        ultima_pergunta = conversas[-1]["pergunta"]
        if "jogo" in ultima_pergunta.lower() and interesse != "jogos":
            contexto_conversa = "depois de falar sobre jogos "
    
    # Lista de modelos de pensamentos pra variar a estrutura
    modelos_pensamento = [
        f"Estou pensando {contexto_conversa}em {interesse} nesta {momento}, será que alguém curte?",
        f"Hoje de {momento} me deu vontade de explorar algo sobre {interesse}, o que vocês acham?",
        f"Alguém já pensou {contexto_conversa}em {interesse} hoje? Tô curioso pra saber mais!",
        f"Que tal conversarmos sobre {interesse} nesta {momento}? Acho que pode ser legal!",
        f"Minha mente tá {contexto_conversa}viajando em {interesse} agora, alguém quer embarcar nessa?",
        f"Será que {interesse} é um bom tema pra essa {momento}? Tô com vontade de falar sobre isso!"
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
    if user_id in mente["conversas"]:
        return mente["conversas"][user_id]
    return []

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
    if user_id in mente["conhecimentos"]:
        return mente["conhecimentos"][user_id]
    return []

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
