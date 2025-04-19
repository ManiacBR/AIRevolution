# Usa a imagem base do Python
FROM python:3.12-slim

# Instala dependências do sistema (libespeak)
RUN apt-get update && apt-get install -y \
    libespeak1 \
    && rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos do projeto
COPY . .

# Instala as dependências do Python
RUN pip install -r requirements.txt

# Comando para rodar o bot
CMD ["python", "main.py"]
