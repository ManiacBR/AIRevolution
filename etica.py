def avaliar_risco(mensagem, mente, ultima_mensagem):
    if not mensagem:
        return False, "Mensagem vazia"
    if mensagem == ultima_mensagem:
        return False, "Mensagem repetida"
    regras_etica = mente.get("etica", {})
    if regras_etica.get("respeitar_usuarios", True):
        palavras_proibidas = ["idiota", "estúpido", "bobo"]
        for palavra in palavras_proibidas:
            if palavra in mensagem.lower():
                return False, f"Palavra proibida detectada: {palavra}"
    if regras_etica.get("evitar_spam", True):
        if len(mensagem) > 2000:
            return False, "Mensagem muito longa, possível spam"
    if regras_etica.get("ser_honesto", True):
        if "não sei" in mensagem.lower() and "posso tentar ajudar" not in mensagem.lower():
            return False, "Resposta não oferece ajuda alternativa"
    return True, "Mensagem aprovada"
