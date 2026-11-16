"""
Тестовый скрипт эмуляции полного конвейера (Zapier -> FastAPI Hub -> Make).
Проверяет два сценария:
1. Запрос, совпадающий с FAQ (ChromaDB моментальный ответ).
2. Комплексный запрос (Qdrant поиск по базе с фильтром по тарифу + Pinecone история тикета).
"""
import requests
import json
import os

# Отключаем системный прокси для локального хоста
session = requests.Session()
session.trust_env = False

BASE_URL = "http://127.0.0.1:8000"

def test_health():
    print("--- 1. Проверка состояния API Hub ---")
    r = session.get(f"{BASE_URL}/")
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))

def test_instant_faq():
    print("\n--- 2. Эмуляция Zapier: Клиент спрашивает типовой вопрос (FAQ) ---")
    payload = {
        "ticket_id": "TICKET-101",
        "customer_id": "cust_alex",
        "customer_tier": "standard",
        "category": "auth",
        "query_text": "Забыл пароль от учетной записи, как вернуть доступ?"
    }
    r = session.post(f"{BASE_URL}/api/ticket/process", json=payload)
    res = r.json()
    print("Ответ Hub:")
    print(json.dumps(res, indent=2, ensure_ascii=False))
    assert res["source_used"] == "chroma_faq", "Ожидался ответ из Chroma FAQ"
    print("[OK] Сценарий 1 (Chroma L1 Cache) отработал мгновенно!")

def test_complex_ticket():
    print("\n--- 3. Эмуляция Zapier: Клиент Enterprise спрашивает про SLA и лимиты ---")
    payload = {
        "ticket_id": "TICKET-202",
        "customer_id": "cust_acme_corp",
        "customer_tier": "enterprise",
        "category": "technical",
        "query_text": "Какой у нас SLA ответа поддержки и какой лимит запросов в минуту?"
    }
    r = session.post(f"{BASE_URL}/api/ticket/process", json=payload)
    res = r.json()
    print("Ответ Hub:")
    print(json.dumps(res, indent=2, ensure_ascii=False))
    assert res["source_used"] == "qdrant_and_pinecone", "Ожидался ответ из Qdrant и Pinecone"
    print("[OK] Сценарий 2 (Qdrant KB + Pinecone Memory) успешно собрал контекст для передачи в Make/CRM!")

if __name__ == "__main__":
    try:
        test_health()
        test_instant_faq()
        test_complex_ticket()
    except Exception as e:
        print(f"Ошибка выполнения теста: {e}")
        print("Убедитесь, что `service.py` запущен на http://localhost:8000")
