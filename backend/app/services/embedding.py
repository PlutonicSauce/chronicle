"""Embedding providers: Bedrock in production, deterministic locally."""

import hashlib
import json
import math
import re
from collections.abc import Iterable

from app.settings import Settings

_TOKEN = re.compile(r"[a-z0-9][a-z0-9_-]{1,}")
_SYNONYMS = {
    "authentication": ("auth", "identity", "login", "session", "saml", "oauth"),
    "authorization": ("auth", "permission", "role", "rbac"),
    "incident": ("outage", "alert", "rollback", "latency"),
    "database": ("schema", "migration", "query", "cockroach"),
    "deployment": ("release", "ci", "rollback", "production"),
    "performance": ("latency", "slow", "optimize", "cache"),
}


def _tokens(text: str) -> Iterable[str]:
    for token in _TOKEN.findall(text.lower()):
        yield token
        yield from _SYNONYMS.get(token, ())


def deterministic_embedding(text: str, dimensions: int = 512) -> list[float]:
    """A stable local retrieval signal, intentionally not represented as an AI model."""

    vector = [0.0] * dimensions
    for token in _tokens(text):
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] & 1 else -1.0
        vector[index] += sign
    magnitude = math.sqrt(sum(value * value for value in vector))
    return [value / magnitude for value in vector] if magnitude else vector


class Embedder:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client = None

    def _bedrock_client(self):
        if self._client is None:
            import boto3

            self._client = boto3.client("bedrock-runtime", region_name=self.settings.aws_region)
        return self._client

    def embed(self, text: str) -> list[float]:
        if not self.settings.use_bedrock:
            return deterministic_embedding(text, self.settings.embedding_dimensions)

        response = self._bedrock_client().invoke_model(
            modelId=self.settings.bedrock_embedding_model,
            body=json.dumps(
                {
                    "inputText": text,
                    "dimensions": self.settings.embedding_dimensions,
                    "normalize": True,
                    "embeddingTypes": ["float"],
                }
            ),
            accept="application/json",
            contentType="application/json",
        )
        payload = json.loads(response["body"].read())
        embedding = payload["embedding"]
        if len(embedding) != self.settings.embedding_dimensions:
            raise ValueError("Bedrock returned an embedding with an unexpected dimension count")
        return [float(value) for value in embedding]

    def answer(self, question: str, memories: list[dict[str, object]]) -> str | None:
        if not self.settings.use_bedrock:
            return None
        evidence = "\n\n".join(
            f"[{memory['id']}] {memory['title']}: {memory['summary']}" for memory in memories
        )
        response = self._bedrock_client().converse(
            modelId=self.settings.bedrock_text_model,
            system=[
                {
                    "text": (
                        "You are Chronicle, an engineering-memory analyst. Answer only from the "
                        "provided memories. Be concise, explain causality, and cite memory IDs in brackets."
                    )
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "text": f"Question: {question}\n\nEngineering memories:\n{evidence}",
                        }
                    ],
                }
            ],
            inferenceConfig={"maxTokens": 500, "temperature": 0.2, "topP": 0.9},
        )
        return response["output"]["message"]["content"][0]["text"]
