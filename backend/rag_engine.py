"""
RAG engine — TF-IDF retrieval + DeepSeek generation.
"""
import os
import json
import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI

from backend.config import (
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL,
    INDEX_PATH, SYSTEM_PROMPT,
)

_client: "OpenAI | None" = None
_vectorizer: "TfidfVectorizer | None" = None
_doc_matrix = None
_doc_metadata: list[dict] = []


def get_deepseek_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    return _client


def _ensure_index_loaded():
    global _vectorizer, _doc_matrix, _doc_metadata
    if _vectorizer is not None:
        return

    vec_path = os.path.join(INDEX_PATH, "vectorizer.pkl")
    matrix_path = os.path.join(INDEX_PATH, "doc_matrix.npy")
    meta_path = os.path.join(INDEX_PATH, "metadata.json")

    if os.path.exists(vec_path) and os.path.exists(matrix_path) and os.path.exists(meta_path):
        with open(vec_path, "rb") as f:
            _vectorizer = pickle.load(f)
        _doc_matrix = np.load(matrix_path)
        with open(meta_path, "r", encoding="utf-8") as f:
            _doc_metadata = json.load(f)


def retrieve_context(query: str, top_k: int = 5) -> list[dict]:
    _ensure_index_loaded()

    if _vectorizer is None or _doc_matrix is None or len(_doc_metadata) == 0:
        return []

    query_vec = _vectorizer.transform([query])
    similarities = cosine_similarity(query_vec, _doc_matrix).flatten()
    top_indices = np.argsort(similarities)[::-1][:top_k]

    docs = []
    for idx in top_indices:
        if similarities[idx] > 0:
            docs.append({
                "content": _doc_metadata[idx]["content"],
                "source": _doc_metadata[idx].get("source", "未知来源"),
                "date": _doc_metadata[idx].get("date", "未知日期"),
            })
    return docs


def build_prompt(query: str, context_docs: list[dict]) -> str:
    context_text = ""
    for i, doc in enumerate(context_docs, 1):
        context_text += f"\n[{i}] 来源: {doc['source']} | 日期: {doc['date']}\n{doc['content']}\n"

    if not context_text:
        context_text = "（暂无相关参考资料）"

    return f"""参考资料：
{context_text}

基于以上参考资料，请回答用户的问题。如果参考资料中没有相关信息，请明确说明。

用户问题：{query}"""


def query_rag(user_query: str, top_k: int = 5) -> dict:
    docs = retrieve_context(user_query, top_k=top_k)
    prompt = build_prompt(user_query, docs)

    client = get_deepseek_client()
    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=4096,
    )

    answer = response.choices[0].message.content

    return {
        "answer": answer,
        "sources": [{"source": d["source"], "date": d["date"]} for d in docs],
        "model": DEEPSEEK_MODEL,
    }
