from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any
from app.core.db.neo4j_manager import get_neo4j_driver, execute_query
from app.core.minio_client import MinIOClient
from app.config.settings import settings

app = FastAPI()

# Initialize MinIO client
minio_client = MinIOClient()

@app.get("/api/graph")
async def get_graph_data():
    """Retrieve all nodes and relationships from the Neo4j knowledge graph."""
    try:
        driver = get_neo4j_driver(settings.database.neo4j.knowledge)
        query = "MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 100"
        results = await execute_query(driver, settings.database.neo4j.knowledge.database, query)

        nodes = {}
        links = []

        for record in results:
            n = record["n"]
            m = record["m"]
            r = record["r"]

            nodes[n.id] = {"id": n.id, "labels": list(n.labels), "properties": dict(n)}
            nodes[m.id] = {"id": m.id, "labels": list(m.labels), "properties": dict(m)}
            links.append({"source": n.id, "target": m.id, "type": r.type, "properties": dict(r)})

        return {"nodes": list(nodes.values()), "links": links}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving graph data: {e}")

@app.get("/api/pdf/{object_name}")
async def get_pdf_presigned_url(object_name: str):
    """Generate a pre-signed URL for a PDF object in MinIO."""
    try:
        presigned_url = minio_client.get_presigned_url(object_name)
        return {"url": presigned_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating pre-signed URL: {e}")

@app.get("/api/hello")
async def hello():
    return {"message": "Hello from FastAPI!"}
