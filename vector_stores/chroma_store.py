"""
ChromaDB Store - Уровень L1 кэша (Hot FAQ).
Используется для мгновенного нахождения готовых ответов на частые вопросы.
"""
import chromadb
from chromadb.utils import embedding_functions
import os

class ChromaFAQCache:
    def __init__(self, persist_directory: str = "./data/chroma"):
        os.makedirs(persist_directory, exist_ok=True)
        # Инициализируем локальный persistent клиент
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Используем встроенную функцию эмбеддингов по умолчанию (ONNX/MiniLM)
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        
        # Коллекция частых вопросов
        self.collection = self.client.get_or_create_collection(
            name="faq_cache",
            embedding_function=self.embedding_fn,
            metadata={"description": "Кэш типовых вопросов и ответов клиентов"}
        )

    def seed_initial_faqs(self):
        """Заполнение базовыми вопросами и ответами для теста."""
        # Проверяем, есть ли уже данные
        if self.collection.count() > 0:
            return

        faqs = [
            {
                "id": "faq_1",
                "question": "Как восстановить забытый пароль от личного кабинета?",
                "answer": "Перейдите на страницу входа и нажмите 'Забыли пароль?'. Мы отправим ссылку для сброса на ваш email.",
                "category": "auth"
            },
            {
                "id": "faq_2",
                "question": "Какие способы оплаты вы принимаете?",
                "answer": "Мы принимаем банковские карты (Visa, MasterCard, МИР), СБП, а также безналичный расчет для юрлиц.",
                "category": "billing"
            },
            {
                "id": "faq_3",
                "question": "Как сменить тарифный план на Enterprise?",
                "answer": "В личном кабинете перейдите в раздел 'Биллинг' -> 'Сменить тариф' или оставьте заявку вашему персональному менеджеру.",
                "category": "subscription"
            },
            {
                "id": "faq_4",
                "question": "Где получить API ключ для интеграции?",
                "answer": "В разделе 'Настройки' -> 'Интеграции и API' нажмите 'Сгенерировать новый токен'.",
                "category": "api"
            }
        ]

        self.collection.add(
            ids=[f["id"] for f in faqs],
            documents=[f["question"] for f in faqs],
            metadatas=[{"answer": f["answer"], "category": f["category"]} for f in faqs]
        )
        print(f"[ChromaDB] Загружено {len(faqs)} типовых вопросов в кэш.")

    def search_faq(self, query: str, threshold: float = 0.85):
        """
        Ищет похожий вопрос в FAQ.
        Возвращает ответ, если расстояние достаточно мало (высокая схожесть).
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=1
        )

        if not results["ids"] or not results["ids"][0]:
            return None

        # В Chroma по умолчанию L2-дистанция (чем меньше, тем ближе)
        distance = results["distances"][0][0] if "distances" in results and results["distances"] else 1.0
        # Преобразуем расстояние в оценку похожести (similarity)
        similarity = 1.0 / (1.0 + distance)

        if similarity >= threshold:
            metadata = results["metadatas"][0][0]
            return {
                "matched_question": results["documents"][0][0],
                "answer": metadata.get("answer"),
                "category": metadata.get("category"),
                "similarity": round(similarity, 3)
            }
        return None

if __name__ == "__main__":
    cache = ChromaFAQCache()
    cache.seed_initial_faqs()
    test_query = "Я потерял пароль от аккаунта, что делать?"
    result = cache.search_faq(test_query, threshold=0.7)
    print("Результат поиска:", result)
