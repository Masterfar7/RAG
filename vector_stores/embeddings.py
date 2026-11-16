"""
Утилита генерации векторных эмбеддингов.
Поддерживает локальные легкие модели или OpenAI text-embedding-3-small.
"""
import os
import math
import hashlib
from typing import List

class EmbeddingService:
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.openai_key = os.getenv("OPENAI_API_KEY")

    def get_embedding(self, text: str) -> List[float]:
        """
        Возвращает нормализованный вектор для строки.
        Если задан OPENAI_API_KEY, можно использовать API OpenAI,
        иначе используется детерминированный локальный эмбеддинг для тестирования.
        """
        if self.openai_key:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=self.openai_key)
                response = client.embeddings.create(
                    input=text,
                    model="text-embedding-3-small"
                )
                return response.data[0].embedding[:self.dimension]
            except Exception as e:
                print(f"[Embeddings] Ошибка OpenAI: {e}. Используем fallback.")

        # Fallback: генерация псевдо-семантического вектора фиксированной размерности
        # на основе хеширования n-грамм и слов
        words = text.lower().split()
        vector = [0.0] * self.dimension

        for i, word in enumerate(words):
            h = int(hashlib.md5(word.encode()).hexdigest(), 16)
            idx = h % self.dimension
            vector[idx] += 1.0 / (i + 1)

        # Нормализация вектора (L2-норма)
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [x / norm for x in vector]
        else:
            vector[0] = 1.0

        return vector

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        return [self.get_embedding(t) for t in texts]
