"""Retrieval Augmented Generation (RAG) Service."""

from app.ai.factory import AIProviderFactory

class RAGService:
    """Orchestrates document search, context retrieval, and generation."""

    def __init__(self, provider_name: str | None = None) -> None:
        self.provider = AIProviderFactory.get_provider(provider_name)

    async def answer_with_context(self, question: str, contexts: list[str]) -> str:
        """Answers a user question utilizing a set of retrieved text contexts."""
        context_str = "\n---\n".join(contexts)
        prompt = (
            "You are PersonaAI. Answer the user question strictly using the provided search context. "
            "If the context does not contain the answer, say 'I cannot find the answer in the provided documents.'\n\n"
            f"Context:\n{context_str}"
        )
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": question}
        ]
        return await self.provider.chat(messages)

    async def generate_query_embedding(self, query: str) -> list[float]:
        """Generates a query vector representation using the active provider embeddings API."""
        return await self.provider.embeddings(query)
