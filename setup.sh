#!/bin/sh

# Sair imediatamente se um comando falhar
set -e

# Espera o servidor MinIO ficar disponível tentando configurar o alias 'myminio'.
# As variáveis de ambiente são lidas do arquivo .env pelo docker-compose.
until /usr/bin/mc alias set myminio http://minio:9000 "$MINIO_ACCESS_KEY" "$MINIO_SECRET_KEY"; do
    echo "[INFO] Aguardando o servidor MinIO..."
    sleep 1
done

echo "[INFO] Servidor MinIO está pronto. Tentando configurar o alias 'myminio'..."

# Verifica se o bucket já existe. Se não, cria o bucket.
if /usr/bin/mc ls myminio/"$MINIO_BUCKET_NAME" > /dev/null 2>&1; then
    echo "[INFO] Bucket '$MINIO_BUCKET_NAME' já existe."
else
    echo "[INFO] Criando o bucket '$MINIO_BUCKET_NAME'..."
    /usr/bin/mc mb myminio/"$MINIO_BUCKET_NAME"
    echo "[INFO] Bucket '$MINIO_BUCKET_NAME' criado com sucesso."
fi

echo "[INFO] Configuração do MinIO concluída."