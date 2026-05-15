"""
Embedding service: generates and stores vector embeddings for code, PRs, issues, comments.
Supports OpenAI and Anthropic (via Voyage) providers.
"""
import asyncio
from typing import Optional
import httpx
from ..config import get_settings

settings = get_settings()

EMBEDDING_DIM = 1536


async def embed_texts(texts: list[str]) -> list[Optional[list[float]]]:
    """Returns embeddings for a batch of texts. Returns None items on failure."""
    if not texts:
        return []

    provider = settings.embedding_provider.lower()

    if provider == "openai" and settings.openai_api_key:
        return await _embed_openai(texts)
    elif provider == "anthropic" and settings.anthropic_api_key:
        return await _embed_voyage(texts)
    else:
        # Return None embeddings — system still works, just keyword-only retrieval
        return [None] * len(texts)


async def embed_text(text: str) -> Optional[list[float]]:
    results = await embed_texts([text])
    return results[0] if results else None


async def _embed_openai(texts: list[str]) -> list[Optional[list[float]]]:
    try:
        import openai
        client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        # Batch in groups of 100
        all_embeddings = []
        for i in range(0, len(texts), 100):
            batch = texts[i:i + 100]
            cleaned = [t[:8000] for t in batch]  # token limit safety
            response = await client.embeddings.create(
                model="text-embedding-3-small",
                input=cleaned,
            )
            all_embeddings.extend([r.embedding for r in response.data])
        # Pad to 1536 if needed or truncate
        result = []
        for emb in all_embeddings:
            if len(emb) < EMBEDDING_DIM:
                emb = emb + [0.0] * (EMBEDDING_DIM - len(emb))
            result.append(emb[:EMBEDDING_DIM])
        return result
    except Exception as e:
        print(f"OpenAI embedding error: {e}")
        return [None] * len(texts)


async def _embed_voyage(texts: list[str]) -> list[Optional[list[float]]]:
    """Voyage AI via Anthropic - uses voyage-code-2 for code."""
    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

        all_embeddings = []
        for i in range(0, len(texts), 128):  # Voyage batch limit
            batch = texts[i:i + 128]
            cleaned = [t[:32000] for t in batch]
            response = await client.beta.messages.batches  # voyage endpoint

            # Use httpx directly for Voyage API
            async with httpx.AsyncClient() as http:
                resp = await http.post(
                    "https://api.voyageai.com/v1/embeddings",
                    headers={
                        "Authorization": f"Bearer {settings.anthropic_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={"input": cleaned, "model": "voyage-code-2"},
                    timeout=60.0,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    embeddings = [item["embedding"] for item in data["data"]]
                    # Normalize to EMBEDDING_DIM
                    for emb in embeddings:
                        if len(emb) < EMBEDDING_DIM:
                            emb = emb + [0.0] * (EMBEDDING_DIM - len(emb))
                        all_embeddings.append(emb[:EMBEDDING_DIM])
                else:
                    all_embeddings.extend([None] * len(batch))

        return all_embeddings
    except Exception as e:
        print(f"Voyage embedding error: {e}")
        return [None] * len(texts)


def cosine_similarity_sql(embedding: list[float]) -> str:
    """Returns pgvector cosine distance operator expression."""
    return f"embedding <=> '{embedding}'"
