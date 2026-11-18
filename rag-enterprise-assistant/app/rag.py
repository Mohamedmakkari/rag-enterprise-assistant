"""Coeur du RAG : decoupage, indexation (ChromaDB), recherche, generation."""
import os
from pathlib import Path

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
import chromadb
from dotenv import load_dotenv

load_dotenv()

DOCS_DIR = Path(os.getenv("DOCS_DIR", "documents"))
DB_DIR = os.getenv("CHROMA_DIR", "chroma_db")
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

_collection = None


def get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=DB_DIR)
        _collection = client.get_or_create_collection("documents")
    return _collection


def split_text(text, size=800, overlap=100):
    """Decoupe le texte en chunks qui se chevauchent legerement."""
    text = text.strip()
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start:start + size])
        start += size - overlap
    return chunks


def ingest_text(source, text):
    """Indexe un document (remplace l'ancienne version du meme fichier)."""
    col = get_collection()
    col.delete(where={"source": source})
    chunks = split_text(text)
    if not chunks:
        return 0
    col.add(
        ids=[f"{source}-{i}" for i in range(len(chunks))],
        documents=chunks,
        metadatas=[{"source": source} for _ in chunks],
    )
    return len(chunks)


def ingest_folder():
    """Indexe tous les .txt / .md du dossier documents/."""
    DOCS_DIR.mkdir(exist_ok=True)
    total = {}
    for path in sorted(DOCS_DIR.iterdir()):
        if path.suffix.lower() in (".txt", ".md"):
            total[path.name] = ingest_text(path.name, path.read_text(encoding="utf-8"))
    return total


def retrieve(question, k=4):
    col = get_collection()
    if col.count() == 0:
        return []
    res = col.query(query_texts=[question], n_results=min(k, col.count()))
    return [
        {"source": m["source"], "text": d}
        for d, m in zip(res["documents"][0], res["metadatas"][0])
    ]


def answer(question):
    passages = retrieve(question)
    if not passages:
        return {"answer": "Aucun document indexe. Ajoutez des fichiers dans documents/.",
                "sources": [], "mode": "empty"}

    sources = sorted({p["source"] for p in passages})
    key = os.getenv("ANTHROPIC_API_KEY")

    if not key:
        text = "\n\n".join(f"[{p['source']}] {p['text']}" for p in passages)
        return {"answer": "Mode sans LLM : voici les passages les plus pertinents.\n\n" + text,
                "sources": sources, "mode": "extractive"}

    import anthropic

    context = "\n\n".join(f"[{p['source']}]\n{p['text']}" for p in passages)
    client = anthropic.Anthropic(api_key=key)
    msg = client.messages.create(
        model=MODEL,
        max_tokens=800,
        system=("Tu reponds uniquement a partir des extraits fournis. "
                "Si la reponse n'y figure pas, dis-le. Cite le nom du fichier source."),
        messages=[{"role": "user",
                   "content": f"Extraits :\n{context}\n\nQuestion : {question}"}],
    )
    return {"answer": msg.content[0].text, "sources": sources, "mode": "llm"}
