# Use uma imagem base oficial do Python
FROM python:3.10-slim

# Define o diretório de trabalho no container
WORKDIR /app

# Define a variável de ambiente para garantir que a saída do Python não seja bufferizada
ENV PYTHONUNBUFFERED 1

# Define a variável de ambiente para que os módulos do projeto sejam encontrados
ENV PYTHONPATH=/app

# Copia o arquivo de dependências
COPY requirements.txt .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação para o diretório de trabalho
COPY . .

# Mantém o container rodando para que possamos usar `docker exec`
CMD ["tail", "-f", "/dev/null"]