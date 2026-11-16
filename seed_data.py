"""
Скрипт начального наполнения (Seeding) и валидации:
- ChromaDB (L1 FAQ Cache)
- Qdrant (Knowledge Base с фильтрацией)
- Pinecone (История клиентов и тикетов)
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

from vector_stores.chroma_store import ChromaFAQCache
from vector_stores.qdrant_store import QdrantKnowledgeBase
from vector_stores.pinecone_store import PineconeCustomerMemory
from vector_stores.embeddings import EmbeddingService

def main():
    print("=== [1/4] Инициализация сервиса эмбеддингов ===")
    embedding_svc = EmbeddingService(dimension=384)

    print("\n=== [2/4] Заполнение ChromaDB (FAQ Cache) ===")
    chroma = ChromaFAQCache()
    chroma.seed_initial_faqs()

    test_query = "Забыл пароль от кабинета"
    hit = chroma.search_faq(test_query, threshold=0.7)
    print(f"Тестовый запрос в Chroma: '{test_query}'")
    print(f"Результат Chroma (L1 Cache): {hit}")

    print("\n=== [3/4] Заполнение Qdrant (Knowledge Base) ===")
    qdrant = QdrantKnowledgeBase()

    kb_articles = [
        {
            "id": 1,
            "text": "Для тарифа Standard лимит обращений в API составляет 60 запросов в минуту. Поддержка оказывается только по email в течение 24 часов.",
            "category": "technical",
            "plan_tier": "standard"
        },
        {
            "id": 2,
            "text": "Для тарифа Enterprise доступен выделенный канал в Slack, лимит API 5000 запросов в минуту и SLA ответа 15 минут 24/7.",
            "category": "technical",
            "plan_tier": "enterprise"
        },
        {
            "id": 3,
            "text": "Политика возврата средств: возврат возможен в течение 14 дней с момента оплаты при условии использования менее 10% лимита токенов.",
            "category": "billing",
            "plan_tier": "all"
        },
        {
            "id": 4,
            "text": "Настройка Single Sign-On (SSO / SAML 2.0 / Okta) доступна клиентам уровня Pro и Enterprise в разделе Безопасность.",
            "category": "security",
            "plan_tier": "enterprise"
        }
    ]

    texts = [a["text"] for a in kb_articles]
    vectors = embedding_svc.get_embeddings(texts)
    qdrant.add_documents(kb_articles, vectors)

    # Тестируем поиск в Qdrant с фильтром по тарифу Enterprise
    search_query = "Какой у нас SLA и сколько запросов в минуту разрешено?"
    q_vec = embedding_svc.get_embedding(search_query)
    qdrant_results = qdrant.search(
        query_vector=q_vec,
        plan_tier="enterprise",
        limit=1
    )
    print(f"Тестовый запрос в Qdrant с фильтром (plan_tier=enterprise): '{search_query}'")
    print(f"Результат Qdrant: {qdrant_results}")

    print("\n=== [4/4] Заполнение Pinecone (История тикетов) ===")
    pinecone = PineconeCustomerMemory()
    tickets = [
        {
            "id": "tick_901",
            "customer_id": "cust_acme_corp",
            "issue": "Медленно формируются ежемесячные финансовые отчеты за прошлый квартал",
            "resolution": "Переключили формирование в фоновый режим и настроили индекс по дате",
            "satisfaction_score": 5
        },
        {
            "id": "tick_902",
            "customer_id": "cust_beta_tech",
            "issue": "Ошибка 403 при вызове webhook интеграции",
            "resolution": "Обновили токен аутентификации в настройках Webhook",
            "satisfaction_score": 4
        }
    ]

    ticket_texts = [f"{t['issue']}. Решение: {t['resolution']}" for t in tickets]
    ticket_vectors = embedding_svc.get_embeddings(ticket_texts)
    pinecone.upsert_tickets(tickets, ticket_vectors)

    sim_tickets = pinecone.find_similar_tickets(
        query_vector=embedding_svc.get_embedding("Тормозит выгрузка отчетов"),
        customer_id="cust_acme_corp"
    )
    print(f"Результат поиска похожих тикетов в Pinecone: {sim_tickets}")

    print("\n[SUCCESS] ВСЕ БАЗЫ УСПЕШНО НАПОЛНЕНЫ И ПРОТЕСТИРОВАНЫ!")

if __name__ == "__main__":
    main()
