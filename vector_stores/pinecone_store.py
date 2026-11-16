"""
Pinecone Store - Облачная долгосрочная память (Customer Profiles & Ticket History).
Используется для поиска похожих прошлых инцидентов и предпочтений конкретного клиента.
"""
import os
from typing import List, Dict, Optional
from pinecone import Pinecone, ServerlessSpec

class PineconeCustomerMemory:
    INDEX_NAME = "customer-tickets"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        if not self.api_key:
            print("[Pinecone] Внимание: PINECONE_API_KEY не установлен. Работа в mock/dry-run режиме.")
            self.pc = None
            self.index = None
            return

        self.pc = Pinecone(api_key=self.api_key)
        self._ensure_index()
        self.index = self.pc.Index(self.INDEX_NAME)

    def _ensure_index(self, dimension: int = 384):
        """Создает Serverless индекс в Pinecone, если его нет."""
        existing_indexes = [idx["name"] for idx in self.pc.list_indexes()]
        if self.INDEX_NAME not in existing_indexes:
            self.pc.create_index(
                name=self.INDEX_NAME,
                dimension=dimension,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            print(f"[Pinecone] Создан Serverless индекс: {self.INDEX_NAME}")

    def upsert_tickets(self, tickets: List[Dict], vectors: List[List[float]]):
        """
        Сохранение тикетов клиентов.
        tickets: список словарей с 'id', 'customer_id', 'issue', 'resolution', 'satisfaction_score'
        """
        if not self.index:
            print("[Pinecone] Пропуск upsert: клиент Pinecone не инициализирован.")
            return

        records = []
        for ticket, vector in zip(tickets, vectors):
            records.append({
                "id": str(ticket["id"]),
                "values": vector,
                "metadata": {
                    "customer_id": ticket.get("customer_id", "unknown"),
                    "issue": ticket.get("issue", ""),
                    "resolution": ticket.get("resolution", ""),
                    "satisfaction_score": ticket.get("satisfaction_score", 5)
                }
            })

        self.index.upsert(vectors=records)
        print(f"[Pinecone] Успешно загружено {len(records)} записей.")

    def find_similar_tickets(self, query_vector: List[float], customer_id: Optional[str] = None, top_k: int = 2) -> List[Dict]:
        """
        Поиск аналогичных обращений клиентов.
        Если указан customer_id, фильтрует только по данному клиенту.
        """
        if not self.index:
            # Демонстрационный ответ при отсутствии API-ключа
            return [
                {
                    "id": "mock_ticket_101",
                    "score": 0.89,
                    "issue": "Проблема со скоростью загрузки отчетов в конце месяца",
                    "resolution": "Включен асинхронный экспорт через фоновую очередь celery",
                    "customer_id": customer_id or "cust_123"
                }
            ]

        filter_dict = {}
        if customer_id:
            filter_dict["customer_id"] = {"$eq": customer_id}

        results = self.index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
            filter=filter_dict if filter_dict else None
        )

        output = []
        for match in results.matches:
            output.append({
                "id": match.id,
                "score": round(match.score, 4),
                "issue": match.metadata.get("issue"),
                "resolution": match.metadata.get("resolution"),
                "customer_id": match.metadata.get("customer_id")
            })
        return output
