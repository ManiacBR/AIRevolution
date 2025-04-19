# Usa a imagem base do Python 3.11
FROM python:3.11

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    libespeak1 \
    portaudio19-dev \
    libasound-dev \
    ffmpeg \
    libsodium-dev \
    build-essential \
    gcc \
    python3-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Instala setuptools (caso precise do distutils)
RUN pip install setuptools

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos do projeto
COPY . .

# Instala as dependências normais
RUN pip install --no-cache-dir -r requirements.txt

# Instala o discord-ext-audiorec direto do repositório GitHub (sem colchetes ou markdown)
RUN pip install git+https://github.com/Silver-Ture/discord-ext-audiorec.git

# Comando para rodar o bot
CMD ["python", "main.py"]
