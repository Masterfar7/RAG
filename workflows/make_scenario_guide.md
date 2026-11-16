# Make (Integromat) Scenario: Fulfillment & CRM Routing

Этот сценарий в **Make** получает данные от n8n или нашего FastAPI Hub и выполняет маршрутизацию в CRM и нотификации.

## Структура сценария (Blueprint):

1. **Custom Webhook (Триггер)**
   - Название: `Receive Processed Ticket`
   - URL: Вебхук адрес из Make
   - Принимает JSON:
     ```json
     {
       "ticket_id": "TICKET-105",
       "customer_id": "CUST-001",
       "source_used": "qdrant_and_pinecone",
       "suggested_action": "route_to_support_agent_with_ai_draft",
       "direct_answer": null,
       "context": { ... }
     }
     ```

2. **Router (Маршрутизатор по веткам)**
   - **Ветка А (Авто-ответ / FAQ Решено):**
     - Фильтр: `source_used` Equal to `chroma_faq`
     - Действие: **Gmail / SendGrid / Telegram** -> Отправить моментальный ответ клиенту без участия человека.
   - **Ветка Б (Сложный кейс / Эскалация):**
     - Фильтр: `source_used` Not Equal to `chroma_faq`
     - Модуль 1: **Google Sheets / Airtable** -> Создать запись в таблице тикетов с колонками:
       - `ID тикета`, `Клиент`, `Найденные статьи в Qdrant`, `История из Pinecone`
     - Модуль 2: **Telegram Bot / Slack** -> Отправить сообщение оператору поддержки:
       > ⚠️ *Новый тикет требуют внимания!*
       > **Клиент**: CUST-001
       > **Подсказка от Qdrant**: Статья о тарифах Enterprise
       > **История из Pinecone**: Ранее клиент обращался по вопросу биллинга (тикет #101).

3. **Webhook Response (Модуль ответа)**
   - Статус: `200 OK`
   - Body: `{"status": "delivered_to_crm"}`
