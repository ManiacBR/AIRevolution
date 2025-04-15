import os
import time
import subprocess
import tempfile
import requests
from main import chamar_gemini_api, registrar_metrica

CODIGO_PERMITIDO = ["etica.py", "mente.py"]  # main.py não, pra não quebrar o bot
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Adiciona no Render
REPO = "VerySupimpa/ai-revolution"  # Ajusta pro teu repo
BRANCH = "main"

def testar_codigo(novo_codigo):
    """Testa sintaxe do código."""
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp:
        temp.write(novo_codigo.encode())
        temp_path = temp.name
    try:
        result = subprocess.run(["python", "-m", "py_compile", temp_path], capture_output=True, text=True)
        os.unlink(temp_path)
        return (True, None) if result.returncode == 0 else (False, f"Erro de sintaxe: {result.stderr}")
    except Exception as e:
        os.unlink(temp_path)
        return False, f"Erro ao testar: {str(e)}"

async def sugerir_mudanca_codigo(arquivo, problema, user_id):
    """Usa Gemini pra sugerir novo código."""
    if arquivo not in CODIGO_PERMITIDO:
        return None, f"Arquivo {arquivo} não permitido."
    
    try:
        with open(arquivo, "r") as f:
            codigo_atual = f.read()
    except FileNotFoundError:
        return None, f"Arquivo {arquivo} não encontrado."
    
    prompt = (
        f"Você é o AI Revolution, criado por VerySupimpa. "
        f"Detectei: {problema}. "
        f"Código atual de {arquivo}:\n```python\n{codigo_atual}\n``` "
        f"Sugira uma nova versão do código pra corrigir o problema. "
        f"Retorne apenas o código novo em ```python\n```."
    )
    
    resposta = await chamar_gemini_api(prompt, user_id)
    if not resposta.startswith("```python\n") or not resposta.endswith("\n```"):
        return None, "Resposta inválida."
    
    return resposta[len("```python\n"):-len("\n```")], None

async def commit_github(arquivo, novo_codigo, motivo):
    """Comita mudanças pro GitHub."""
    if not GITHUB_TOKEN:
        return False, "GITHUB_TOKEN não configurado."
    
    try:
        # Pega o arquivo atual do repo
        url = f"https://api.github.com/repos/{REPO}/contents/{arquivo}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return False, f"Erro ao acessar {arquivo}: {response.text}"
        
        data = response.json()
        sha = data["sha"]
        content = novo_codigo.encode("base64").decode("utf-8")
        
        # Atualiza o arquivo
        payload = {
            "message": f"Auto edição: {motivo}",
            "content": content,
            "sha": sha,
            "branch": BRANCH
        }
        response = requests.put(url, headers=headers, json=payload)
        if response.status_code == 200:
            return True, None
        return False, f"Erro ao commitar: {response.text}"
    except Exception as e:
        return False, f"Erro no commit: {str(e)}"

async def aplicar_mudanca_codigo(arquivo, problema, user_id):
    """Aplica mudança no código."""
    novo_codigo, erro = await sugerir_mudanca_codigo(arquivo, problema, user_id)
    if erro:
        registrar_metrica("erros_auto_edicao")
        return False, erro
    
    teste_ok, erro_teste = testar_codigo(novo_codigo)
    if not teste_ok:
        registrar_metrica("erros_auto_edicao")
        return False, erro_teste
    
    # Salva localmente (temporário no Render)
    try:
        with open(arquivo, "w") as f:
            f.write(novo_codigo)
    except Exception as e:
        return False, f"Erro ao salvar: {str(e)}"
    
    # Comita pro GitHub
    sucesso, erro = await commit_github(arquivo, novo_codigo, problema)
    if not sucesso:
        registrar_metrica("erros_auto_edicao")
        return False, erro
    
    return True, "Código atualizado e commitado!"
