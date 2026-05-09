"""
Build the knowledge base from raw text files in data/raw/.
Uses TF-IDF vectorization and stores the index to disk.
"""
import os
import re
import json
import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from backend.config import DATA_DIR, INDEX_PATH


def chunk_text(text: str, chunk_size: int = 800) -> list[str]:
    """Split text into chunks at paragraph boundaries."""
    paragraphs = text.split("\n\n")
    chunks = []
    current = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(current) + len(para) < chunk_size:
            current = (current + "\n\n" + para).strip()
        else:
            if current:
                chunks.append(current)
            current = para

    if current:
        chunks.append(current)

    return chunks


def parse_metadata_from_filename(filename: str) -> dict:
    """Extract source and date info from filename."""
    base = os.path.splitext(filename)[0]
    parts = base.split("_", 1)
    source = parts[0] if parts else "unknown"
    date_match = re.search(r"(\d{8})", base)
    date_str = date_match.group(1) if date_match else "2026-01-01"
    formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    return {"source": source, "date": formatted_date}


def build_knowledge_base(data_dir: str = None):
    """Read all text files, chunk them, build TF-IDF index, and save to disk."""
    if data_dir is None:
        data_dir = DATA_DIR

    if not os.path.exists(data_dir):
        print(f"Data directory not found: {data_dir}")
        return 0

    txt_files = [f for f in os.listdir(data_dir) if f.endswith(".txt")]
    if not txt_files:
        print(f"No .txt files found in {data_dir}")
        return 0

    # Collect all chunks and their metadata
    all_chunks = []
    all_metadata = []

    for filename in txt_files:
        filepath = os.path.join(data_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        chunks = chunk_text(text)
        if not chunks:
            continue

        meta = parse_metadata_from_filename(filename)
        for chunk in chunks:
            all_chunks.append(chunk)
            all_metadata.append({
                "content": chunk,
                "source": meta["source"],
                "date": meta["date"],
            })

        print(f"Loaded {filename}: {len(chunks)} chunks (source: {meta['source']}, date: {meta['date']})")

    if not all_chunks:
        print("No chunks found")
        return 0

    # Build TF-IDF vectorizer with Chinese-friendly parameters
    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        analyzer="char_wb",
    )
    doc_matrix = vectorizer.fit_transform(all_chunks)

    # Save to disk
    os.makedirs(INDEX_PATH, exist_ok=True)
    with open(os.path.join(INDEX_PATH, "vectorizer.pkl"), "wb") as f:
        pickle.dump(vectorizer, f)
    np.save(os.path.join(INDEX_PATH, "doc_matrix.npy"), doc_matrix.toarray())
    with open(os.path.join(INDEX_PATH, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(all_metadata, f, ensure_ascii=False, indent=2)

    print(f"\nKnowledge base built: {len(all_chunks)} chunks indexed")
    return len(all_chunks)


if __name__ == "__main__":
    build_knowledge_base()
