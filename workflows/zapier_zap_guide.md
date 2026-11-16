# Zapier Zap: Ingestion & Trigger Pipeline

В этом сценарии **Zapier** выступает точкой сбора входящих лидов и обращений из внешних источников (формы на сайте, входящие письма, мессенджеры).

## Структура Zap:

### 1. Trigger (Источник события)
* **App**: Typeform / Google Forms / Gmail / Slack / Webhook
* **Event**: *New Form Submission* (или *New Incoming Email*)
* **Поля данных**:
  * `Email / Customer ID`
  * `Текст обращения (message)`
  * `Тариф клиента (tier)`

### 2. Action 1: Formatter by Zapier (Опционально)
* Очистка текста от лишних символов, приведение email к нижнему регистру, извлечение ключевых слов.

### 3. Action 2: Webhooks by Zapier (POST)
* **App**: Webhooks by Zapier
* **Event**: `Custom Request` или `POST`
* **URL**: Эндпоинт n8n (`http://<ваш-сервер-n8n>:5678/webhook/incoming-ticket`) или нашего Hub (`http://localhost:8000/api/ticket/process`)
* **Payload Type**: `json`
* **Data**:
  ```json
  {
    "ticket_id": "{{zap_meta_human_now}}",
    "customer_id": "{{1.customer_email}}",
    "customer_tier": "{{1.tier}}",
    "query_text": "{{1.message}}"
  }
  ```
* **Headers**:
  * `Content-Type`: `application/json`

### 4. Результат:
Zapier полностью абстрагирует источники обращений, передавая стандартизированный JSON в цепочку векторного анализа.
