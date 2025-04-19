# Usa a imagem base do Python 3.11 para incluir distutils
FROM python:3.11

# Instala dependências do sistema (libespeak para pyttsx3, portaudio e alsa para áudio)
RUN apt-get update && apt-get install -y \
    libespeak1 \
    portaudio19-dev \
    libasound-dev \
    build-essential \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Instala setuptools para compatibilidade com distutils
RUN pip install setuptools

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos do projeto
COPY . .

# Instala as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Comando para rodar o bot
CMD ["python", "main.py"]
