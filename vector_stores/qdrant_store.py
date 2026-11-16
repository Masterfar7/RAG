"""
Qdrant Store - Основная база знаний (Company Knowledge Base).
Используется для поиска по регламентам, документации и статьям базы знаний
с поддержкой фильтрации по метаданным (payload filtering).
Поддерживает:
1. Qdrant Cloud (через QDRANT_URL + QDRANT_API_KEY)
2. Docker / Server (через host:port)
3. Локальный embedded режим (path="./data/qdrant_local") БЕЗ Docker!
"""
import os
from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models

class QdrantKnowledgeBase:
    COLLECTION_NAME = "company_knowledge_base"

    def __init__(self, host: str = "localhost", port: int = 6333):
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")

        if qdrant_url:
            print(f"[Qdrant] Подключение к Qdrant Cloud: {qdrant_url}")
            self.client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        else:
            try:
                # Пробуем подключиться к серверу/Docker
                client = QdrantClient(host=host, port=port, timeout=2.0)
                client.get_collections()
                self.client = client
                print(f"[Qdrant] Подключено к серверу {host}:{port}")
            except Exception:
                # Fallback: встроенный локальный режим хранения на диске (не требует Docker!)
                local_path = "./data/qdrant_local"
                os.makedirs(local_path, exist_ok=True)
                print(f"[Qdrant] Сервер не найден. Запуск во встроенном локальном режиме: {local_path}")
                self.client = QdrantClient(path=local_path)

        self._ensure_collection()

    def _ensure_collection(self, vector_size: int = 384):
        """Создает коллекцию, если она не существует."""
        collections = [c.name for c in self.client.get_collections().collections]
        if self.COLLECTION_NAME not in collections:
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE
                )
            )
            print(f"[Qdrant] Создана коллекция: {self.COLLECTION_NAME}")

    def add_documents(self, documents: List[Dict], vectors: List[List[float]]):
        """
        Загрузка документов в Qdrant.
        documents: список словарей с 'id', 'text', 'category', 'plan_tier'
        """
        points = []
        for i, (doc, vector) in enumerate(zip(documents, vectors)):
            points.append(
                models.PointStruct(
                    id=doc.get("id", i + 1),
                    vector=vector,
                    payload={
                        "text": doc["text"],
                        "category": doc.get("category", "general"),
                        "plan_tier": doc.get("plan_tier", "all"),
                        "updated_at": doc.get("updated_at", "2026-01-01")
                    }
                )
            )

        self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=points
        )
        print(f"[Qdrant] Загружено {len(points)} документов.")

    def search(
        self,
        query_vector: List[float],
        category: Optional[str] = None,
        plan_tier: Optional[str] = None,
        limit: int = 3
    ) -> List[Dict]:
        """
        Поиск по векторному сходству с фильтрацией по метаданным (Payload Filtering).
        """
        filter_conditions = []
        if category and category != "general":
            filter_conditions.append(
                models.FieldCondition(
                    key="category",
                    match=models.MatchValue(value=category)
                )
            )
        if plan_tier and plan_tier != "all":
            filter_conditions.append(
                models.FieldCondition(
                    key="plan_tier",
                    match=models.MatchValue(value=plan_tier)
                )
            )

        query_filter = None
        if filter_conditions:
            query_filter = models.Filter(must=filter_conditions)

        # Поддержка qdrant-client 1.20+ (query_points) и обратная совместимость
        if hasattr(self.client, "query_points"):
            response = self.client.query_points(
                collection_name=self.COLLECTION_NAME,
                query=query_vector,
                query_filter=query_filter,
                limit=limit
            )
            results = response.points
        else:
            results = self.client.search(
                collection_name=self.COLLECTION_NAME,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=limit
            )

        output = []
        for res in results:
            output.append({
                "id": res.id,
                "score": round(res.score, 4),
                "text": res.payload.get("text"),
                "category": res.payload.get("category"),
                "plan_tier": res.payload.get("plan_tier")
            })
        return output
