import json
import math
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
INDEX_FILE = BASE_DIR / "data" / "index.json"

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-5.6-luna")

app = FastAPI(title="Hospital HMS RAG")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


class AskRequest(BaseModel):
    question: str
    top_k: int = 4


def get_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY is missing. Add it to .env or Render environment variables."
        )
    return OpenAI(api_key=api_key)


def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def load_index():
    if not INDEX_FILE.exists():
        raise HTTPException(
            status_code=500,
            detail="RAG index is missing. Run: python ingest.py"
        )
    return json.loads(INDEX_FILE.read_text(encoding="utf-8"))


@app.get("/")
def home():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "index_ready": INDEX_FILE.exists()
    }


@app.post("/ask")
def ask(request: AskRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    client = get_client()
    index = load_index()

    query_embedding = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=question
    ).data[0].embedding

    ranked = []
    for item in index:
        score = cosine_similarity(query_embedding, item["embedding"])
        ranked.append((score, item))

    ranked.sort(key=lambda x: x[0], reverse=True)
    selected = ranked[:max(1, min(request.top_k, 8))]

    context = "\n\n".join(
        f"SECTION: {item['section']}\n{item['text']}"
        for _, item in selected
    )

    instructions = """You are a Knowledge Transfer assistant for a Hospital Management System.
Answer only using the supplied KT context.
If the answer is not available in the context, say:
"I could not find that information in the Hospital HMS KT document."
Do not invent patient data, hospital policies, medical advice, or unsupported technical details.
For technical questions, explain clearly for a new project team member."""

    response = client.responses.create(
        model=CHAT_MODEL,
        instructions=instructions,
        input=f"KT CONTEXT:\n{context}\n\nQUESTION:\n{question}"
    )

    return {
        "answer": response.output_text,
        "sources": [
            {
                "section": item["section"],
                "similarity": round(score, 4)
            }
            for score, item in selected
        ]
    }
