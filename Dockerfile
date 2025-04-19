# Usa a imagem base do Python 3.11
FROM python:3.11

# Instala dependências do sistema para áudio, compilação e Rust
RUN apt-get update && apt-get install -y \
    libespeak1 \
    portaudio19-dev \
    libasound-dev \
    ffmpeg \
    libsodium-dev \
    libffi-dev \
    libnacl-dev \
    build-essential \
    gcc \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instala o compilador Rust
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Instala setuptools (caso necessário para distutils)
RUN pip install --upgrade pip setuptools

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos do projeto
COPY . .

# Instala as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Comando para rodar o bot
CMD ["python", "main.py"]
