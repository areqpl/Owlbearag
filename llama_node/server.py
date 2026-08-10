import os
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.core import Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("owlbearag.server")

# Configure embedding and LLM (GPU if available)
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-large")
Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.0)

# Load persisted index (ensure path exists)
storage_dir = os.getenv("LLAMA_INDEX_STORAGE", "./storage")
query_engine = None

if os.path.isdir(storage_dir):
    try:
        storage_context = StorageContext.from_defaults(persist_dir=storage_dir)
        index = load_index_from_storage(storage_context)
        query_engine = index.as_query_engine(similarity_top_k=5, response_mode="compact", streaming=True)
        logger.info(f"Successfully loaded index from {storage_dir}")
    except Exception as err:
        logger.error(f"Failed to load index from {storage_dir}: {err}")
else:
    logger.warning(f"Index storage directory not found: {storage_dir}")

app = FastAPI(title="Owlbearag LlamaIndex RAG Node")

class QueryRequest(BaseModel):
    query: str
    stream: Optional[bool] = True

@app.post("/query")
async def query_endpoint(request: QueryRequest):
    if not query_engine:
        raise HTTPException(status_code=500, detail="RAG index storage is not loaded")
    
    try:
        if request.stream:
            streaming_response = query_engine.query(request.query)
            
            def token_generator():
                for token in streaming_response.response_gen:
                    yield token

            return StreamingResponse(token_generator(), media_type="text/plain")
        else:
            response = query_engine.query(request.query)
            return {"answer": str(response), "response": str(response)}
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "ok", "indexed": query_engine is not None}

if __name__ == "__main__":
    host = os.getenv("RAG_HOST", "0.0.0.0")
    port = int(os.getenv("RAG_PORT", "8000"))
    import uvicorn
    uvicorn.run(app, host=host, port=port)
