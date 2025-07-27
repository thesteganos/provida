#!/bin/sh

# Sair imediatamente se um comando falhar
set -e

# Espera o servidor MinIO ficar disponível tentando configurar o alias 'myminio'.
# As variáveis de ambiente são lidas do arquivo .env pelo docker-compose.
until /usr/bin/mc alias set myminio http://minio:9000 "$MINIO_ACCESS_KEY" "$MINIO_SECRET_KEY"; do
    echo "Aguardando o servidor MinIO..."
    sleep 1
done

echo "Servidor MinIO está pronto."

# Verifica se o bucket já existe. Se não, cria o bucket.
if /usr/bin/mc ls myminio/"$MINIO_BUCKET_NAME" > /dev/null 2>&1; then
    echo "Bucket '$MINIO_BUCKET_NAME' já existe."
else
    echo "Criando o bucket '$MINIO_BUCKET_NAME'..."
    /usr/bin/mc mb myminio/"$MINIO_BUCKET_NAME"
    echo "Bucket '$MINIO_BUCKET_NAME' criado com sucesso."
fi