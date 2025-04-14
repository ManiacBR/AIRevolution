def avaliar_risco(acao, mente, ultima_mensagem=""):
    if acao == ultima_mensagem:
        return False, "Mensagem repetida, pode ser um loop."
    if not mente["etica"]["evitar_spam"] and len(acao) > 200:
        return False, "Mensagem longa demais, pode ser spam."
    if any(palavra in acao.lower() for palavra in ["insulto", "ofensa"]):
        return False, "Isso pode ofender alguém, melhor não."
    return True, "Ação aprovada."
