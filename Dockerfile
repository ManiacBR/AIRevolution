# Usa imagem base com Python
FROM python:3.10-slim

# Define diretório de trabalho
WORKDIR /app

# Instala dependências de sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libasound-dev \
    portaudio19-dev \
    libportaudio2 \
    libportaudiocpp0 \
    libffi-dev \
    libnacl-dev \
    libpulse-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copia os arquivos para o container
COPY . .

# Instala as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Comando para rodar o bot
CMD ["python", "main.py"]
