# AI Customer Intelligence Suite

Сквозной проект интеграции векторных баз данных (**ChromaDB**, **Qdrant**, **Pinecone**) и платформ автоматизации (**n8n**, **Make**, **Zapier**).

## 🏛 Архитектура

1. **Точка входа (Ingestion)**:
   - **Zapier**: Перехватывает входящие заявки/тикеты из форм, почты или CRM и передает стандартизированный JSON вебхуком.
2. **Векторный слой (Multi-Vector Storage)**:
   - **ChromaDB (L1 FAQ Cache)**: Быстрый локальный кэш типовых вопросов. Если схожесть высока — моментальный авто-ответ.
   - **Qdrant (Knowledge Base)**: База регламентов и документации с поддержкой сложной фильтрации по метаданным (`payload`: `category`, `plan_tier`).
   - **Pinecone (Long-term Customer Memory)**: Облачное хранилище истории инцидентов клиентов для нахождения похожих прошлых решений.
3. **Оркестрация и AI**:
   - **n8n / FastAPI**: Принимает вебхук, координирует поиск по трем базам и формирует контекст для LLM.
4. **Пост-обработка и маршрутизация (Fulfillment)**:
   - **Make (Integromat)**: Роутинг, создание карточки в CRM (Airtable / Google Sheets), отправка уведомлений агентам поддержки в Slack / Telegram.

---

## 🚀 Быстрый старт

### 1. Наполнение баз тестовыми данными
```bash
.\venv\Scripts\python seed_data.py
```

### 2. Запуск единого API Hub
```bash
.\venv\Scripts\python service.py
```
Документация Swagger будет доступна по адресу: `http://localhost:8000/docs`

### 3. Автоматизация:
* `workflows/n8n_workflow.json` — готовый JSON для импорта в n8n (`Import from JSON`).
* `workflows/make_scenario_guide.md` — гайд по настройке сценария в Make.
* `workflows/zapier_zap_guide.md` — гайд по настройке триггера в Zapier.
