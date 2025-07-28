# Updates for `.env.example`

## Instructions for Setting Up API Keys and Passwords

### Google API Key
- **Key:** `GOOGLE_API_KEY`
- **Value:** Replace `SUA_CHAVE_API_DO_GOOGLE_AQUI` with your actual Google Gemini API key.

### Docker Service Credentials
- **Neo4j Password:** `NEO4J_PASSWORD`
  - **Value:** Replace `senha_super_segura_para_neo4j` with a secure password for Neo4j.
- **MinIO Access Key:** `MINIO_ACCESS_KEY`
  - **Value:** Replace `minioadmin` with a secure access key for MinIO.
- **MinIO Secret Key:** `MINIO_SECRET_KEY`
  - **Value:** Replace `minio_senha_super_segura` with a secure secret key for MinIO.
- **MinIO Bucket Name:** `MINIO_BUCKET_NAME`
  - **Value:** Name of the bucket to be created in MinIO (e.g., `provida-bucket`).

### Database Configurations
- **Neo4j Knowledge URI:** `DATABASE__NEO4J_KNOWLEDGE__URI`
  - **Value:** `bolt://neo4j:7687`
- **Neo4j Knowledge User:** `DATABASE__NEO4J_KNOWLEDGE__USER`
  - **Value:** `neo4j`
- **Neo4j Knowledge Password:** `DATABASE__NEO4J_KNOWLEDGE__PASSWORD`
  - **Value:** `${NEO4J_PASSWORD}`
- **Neo4j Knowledge Database:** `DATABASE__NEO4J_KNOWLEDGE__DATABASE`
  - **Value:** `provida-knowledge`

- **Neo4j Memory Agents URI:** `DATABASE__NEO4J_MEMORY_AGENTS__URI`
  - **Value:** `bolt://neo4j:7687`
- **Neo4j Memory Agents User:** `DATABASE__NEO4J_MEMORY_AGENTS__USER`
  - **Value:** `neo4j`
- **Neo4j Memory Agents Password:** `DATABASE__NEO4J_MEMORY_AGENTS__PASSWORD`
  - **Value:** `${NEO4J_PASSWORD}`
- **Neo4j Memory Agents Database:** `DATABASE__NEO4J_MEMORY_AGENTS__DATABASE`
  - **Value:** `provida-memory`