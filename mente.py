import json
import random
import time
import requests
import base64
import os  # Adicionado pra corrigir o erro
from datetime import datetime

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

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "ManiacBR/AIRevolution"  # Teu repo
MENTE_PATH = "data/mente.json"  # Caminho no repo
BRANCH = "main"

def github_request(method, endpoint, data=None):
    """Faz requisições pra API do GitHub."""
    url = f"https://api.github.com/repos/{REPO}/{endpoint}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.request(method, url, headers=headers, json=data)
    return response

def carregar_mente():
    """Carrega mente.json do GitHub."""
    response = github_request("GET", f"contents/{MENTE_PATH}")
    if response.status_code == 200:
        print(f"Carregando {MENTE_PATH} do GitHub...")
        data = response.json()
        content = base64.b64decode(data["content"]).decode("utf-8")
        return json.loads(content)
    else:
        print(f"Criando {MENTE_PATH} no GitHub...")
        # Cria arquivo inicial
        payload = {
            "message": "Inicia mente.json",
            "content": base64.b64encode(json.dumps(MENTE_PADRAO).encode()).decode(),
            "branch": BRANCH
        }
        github_request("PUT", f"contents/{MENTE_PATH}", payload)
        return MENTE_PADRAO

def salvar_mente(mente):
    """Salva mente.json no GitHub."""
    print(f"Salvando {MENTE_PATH} no GitHub...")
    # Pega o SHA atual
    response = github_request("GET", f"contents/{MENTE_PATH}")
    sha = response.json()["sha"] if response.status_code == 200 else None
    # Atualiza arquivo
    payload = {
        "message": f"Atualiza mente.json em {time.ctime()}",
        "content": base64.b64encode(json.dumps(mente).encode()).decode(),
        "branch": BRANCH
    }
    if sha:
        payload["sha"] = sha
    response = github_request("PUT", f"contents/{MENTE_PATH}", payload)
    if response.status_code not in (200, 201):
        print(f"Erro ao salvar mente.json: {response.text}")

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
    user_id = str(user_id)
    return mente.get("ultimos_tons", {}).get(user_id, None)

def atualizar_tom(user_id, tom):
    mente = carregar_mente()
    user_id = str(user_id)
    if "ultimos_tons" not in mente:
        mente["ultimos_tons"] = {}
    mente["ultimos_tons"][user_id] = tom
    salvar_mente(mente)
