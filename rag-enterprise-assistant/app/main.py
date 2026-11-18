from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app import rag

app = FastAPI(title="RAG Enterprise Assistant")


class Question(BaseModel):
    question: str


@app.on_event("startup")
def startup():
    rag.ingest_folder()


@app.get("/")
def home():
    return FileResponse("app/static/index.html")


@app.post("/api/ask")
def ask(body: Question):
    if not body.question.strip():
        raise HTTPException(400, "Question vide")
    return rag.answer(body.question)


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".txt", ".md")):
        raise HTTPException(400, "Seuls les fichiers .txt et .md sont acceptes")
    text = (await file.read()).decode("utf-8", errors="ignore")
    rag.DOCS_DIR.mkdir(exist_ok=True)
    (rag.DOCS_DIR / file.filename).write_text(text, encoding="utf-8")
    return {"file": file.filename, "chunks": rag.ingest_text(file.filename, text)}


@app.get("/api/health")
def health():
    return {"status": "ok", "chunks": rag.get_collection().count()}


app.mount("/static", StaticFiles(directory="app/static"), name="static")
