# Usa a imagem base do Python
FROM python:3.12-slim

# Instala dependências do sistema (libespeak, portaudio e distutils)
RUN apt-get update && apt-get install -y \
    libespeak1 \
    portaudio19-dev \
    build-essential \
    gcc \
    python3-dev \
    python3-distutils \
    && rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos do projeto
COPY . .

# Instala as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Comando para rodar o bot
CMD ["python", "main.py"]
