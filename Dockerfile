# Maya HopeCann - Dockerfile para Railway
FROM python:3.11-slim

# Configurar variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório de trabalho
WORKDIR /app

# Copiar arquivos de configuração
COPY pyproject.toml requirements.txt ./

# Instalar dependências Python
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt && \
    pip install -e .

# Copiar código fonte
COPY . .

# Criar diretórios necessários
RUN mkdir -p mensagens_recebidas logs temp

# Criar usuário não-root
RUN useradd --create-home --shell /bin/bash maya && \
    chown -R maya:maya /app
USER maya

# Expor porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Comando de inicialização
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
