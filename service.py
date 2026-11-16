"""
FastAPI Hub - Единый оркестратор взаимодействия всех векторных баз и платформ автоматизации.
Zapier -> FastAPI -> [Chroma / Qdrant / Pinecone] -> Make -> CRM/Slack
"""
import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

load_dotenv()

from vector_stores.chroma_store import ChromaFAQCache
from vector_stores.qdrant_store import QdrantKnowledgeBase
from vector_stores.pinecone_store import PineconeCustomerMemory
from vector_stores.embeddings import EmbeddingService

app = FastAPI(
    title="Customer Intelligence AI Hub",
    description="Объединенный API для Chroma, Qdrant, Pinecone с поддержкой n8n, Make, Zapier"
)

# Инициализация сервисов
faq_cache = ChromaFAQCache()
faq_cache.seed_initial_faqs()

embedding_service = EmbeddingService(dimension=384)

try:
    qdrant_kb = QdrantKnowledgeBase(
        host=os.getenv("QDRANT_HOST", "localhost"),
        port=int(os.getenv("QDRANT_PORT", 6333))
    )
except Exception as e:
    print(f"[Warning] Ошибка Qdrant ({e})")
    qdrant_kb = None

pinecone_memory = PineconeCustomerMemory(api_key=os.getenv("PINECONE_API_KEY"))

# Модели запросов/ответов
class TicketRequest(BaseModel):
    ticket_id: str
    customer_id: str
    customer_tier: Optional[str] = "standard"  # standard, pro, enterprise
    category: Optional[str] = "general"
    query_text: str

class PipelineResponse(BaseModel):
    ticket_id: str
    customer_id: str
    source_used: str  # "chroma_faq", "qdrant_kb", "pinecone_history"
    direct_answer: Optional[str] = None
    retrieved_context: Dict[str, Any]
    suggested_action: str

# Раздача веб-дашборда
@app.get("/")
def get_dashboard():
    return FileResponse("frontend/index.html")

@app.get("/api/health")
def read_root():
    return {
        "status": "online",
        "vector_stores": {
            "chroma": "ready (in-memory/file)",
            "qdrant": "ready" if qdrant_kb else "not_connected (start via docker)",
            "pinecone": "ready" if pinecone_memory.index else "mock_mode"
        }
    }

@app.post("/api/ticket/process", response_model=PipelineResponse)
def process_ticket(req: TicketRequest):
    """
    Главный конвейер обработки входящего обращения:
    1. Проверка быстрого FAQ в Chroma (L1 Cache). Если есть точное совпадение -> отдаем сразу!
    2. Поиск релевантных статей в Qdrant с фильтром по тарифу клиента.
    3. Поиск исторических инцидентов этого клиента в Pinecone.
    """
    # 1. Проверяем L1 Cache в ChromaDB
    faq_hit = faq_cache.search_faq(req.query_text, threshold=0.65)
    if faq_hit:
        return PipelineResponse(
            ticket_id=req.ticket_id,
            customer_id=req.customer_id,
            source_used="chroma_faq",
            direct_answer=faq_hit["answer"],
            retrieved_context={"faq": faq_hit},
            suggested_action="auto_reply_to_customer"
        )

    # Получаем эмбеддинг запроса для векторного поиска
    query_vector = embedding_service.get_embedding(req.query_text)

    # 2. Ищем в базе знаний Qdrant с учетом тарифа
    kb_docs = []
    if qdrant_kb:
        try:
            kb_docs = qdrant_kb.search(
                query_vector=query_vector,
                plan_tier=req.customer_tier,
                limit=2
            )
        except Exception as e:
            print(f"[Qdrant Search Error] {e}")

    # 3. Ищем историю тикетов в Pinecone
    history = pinecone_memory.find_similar_tickets(
        query_vector=query_vector,
        customer_id=req.customer_id,
        top_k=2
    )

    return PipelineResponse(
        ticket_id=req.ticket_id,
        customer_id=req.customer_id,
        source_used="qdrant_and_pinecone",
        direct_answer=None,
        retrieved_context={
            "knowledge_base_articles": kb_docs,
            "previous_similar_tickets": history
        },
        suggested_action="route_to_support_agent_with_ai_draft"
    )

@app.post("/api/faq/check")
def check_faq(query: str):
    """Прямой эндпоинт для проверки вопроса в ChromaDB FAQ кэше."""
    result = faq_cache.search_faq(query)
    return {"query": query, "hit": result}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("service:app", host="0.0.0.0", port=8000, reload=True)
