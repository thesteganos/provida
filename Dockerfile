# Use uma imagem base oficial do Python
FROM python:3.10-slim

# Define a variável de ambiente para garantir que a saída do Python não seja bufferizada
ENV PYTHONUNBUFFERED 1

# Cria um usuário e grupo não-root para a aplicação
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app -s /sbin/nologin -c "Docker image user" appuser

# Define o diretório de trabalho no container
WORKDIR /app

# Define a variável de ambiente para que os módulos do projeto sejam encontrados
ENV PYTHONPATH=/app

# Copia o arquivo de dependências
COPY requirements.txt .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação
COPY . .

# Muda a propriedade do diretório da aplicação para o usuário não-root
RUN chown -R appuser:appgroup /app

# Muda para o usuário não-root
USER appuser

# Mantém o container rodando para que possamos usar `docker exec`
# Em um ambiente de produção, este CMD seria substituído para iniciar a API, por exemplo:
# CMD ["uvicorn", "src.app.api.main:app", "--host", "0.0.0.0", "--port", "80"]
CMD ["tail", "-f", "/dev/null"]