# Usa uma imagem oficial do Python como base
FROM python:3.10-slim

# Define o diretório de trabalho no container
WORKDIR /app

# Copia os arquivos do projeto para o container
COPY . .

# Instala dependências do sistema (para PyAudio, pyttsx3 e speech recognition)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    espeak \
    libasound-dev \
    portaudio19-dev \
    libportaudio2 \
    libportaudiocpp0 \
    libffi-dev \
    libnacl-dev \
    libpulse-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Instala as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Comando para rodar o bot
CMD ["python", "main.py"]
