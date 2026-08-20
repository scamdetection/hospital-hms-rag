import re
from pathlib import Path
from collections import Counter
from math import sqrt

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
DOC_FILE = BASE_DIR / "docs" / "hms_kt.md"

app = FastAPI(title="Hospital HMS RAG")

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static"
)


class AskRequest(BaseModel):
    question: str
    top_k: int = 4


STOPWORDS = set("""
a an the and or but if then than is are was were be been being
to of in on for with from by as at into about this that these those
it its they them their you your what which who when where why how
can could should would do does did has have had will shall may might
a patient system hospital management explain tell me
""".split())


def tokenize(text):
    return [
        word
        for word in re.findall(r"[a-zA-Z0-9_]+", text.lower())
        if word not in STOPWORDS and len(word) > 1
    ]


def load_sections():
    if not DOC_FILE.exists():
        raise HTTPException(
            status_code=500,
            detail="hms_kt.md file is missing."
        )

    text = DOC_FILE.read_text(encoding="utf-8")

    matches = list(
        re.finditer(
            r"(?m)^## (\d+)\.\s+(.+)$",
            text
        )
    )

    sections = []

    for i, match in enumerate(matches):

        start = match.start()

        end = (
            matches[i + 1].start()
            if i + 1 < len(matches)
            else len(text)
        )

        block = text[start:end].strip()

        sections.append({
            "number": int(match.group(1)),
            "title": match.group(2).strip(),
            "text": block
        })

    return sections


SECTIONS = load_sections()


def similarity(question, document):
    question_words = tokenize(question)
    document_words = tokenize(document)

    if not question_words or not document_words:
        return 0.0

    question_count = Counter(question_words)
    document_count = Counter(document_words)

    dot_product = sum(
        question_count[word] * document_count[word]
        for word in question_count
    )

    question_norm = sqrt(
        sum(value * value for value in question_count.values())
    )

    document_norm = sqrt(
        sum(value * value for value in document_count.values())
    )

    if question_norm == 0 or document_norm == 0:
        return 0.0

    return dot_product / (question_norm * document_norm)


def create_answer(question, selected_sections):

    question_words = set(tokenize(question))

    sentences = []

    for section_score, section in selected_sections:

        parts = re.split(
            r"(?<=[.!?])\s+|\n",
            section["text"]
        )

        for sentence in parts:

            sentence = sentence.strip()

            if not sentence:
                continue

            sentence_words = set(tokenize(sentence))

            overlap = len(
                question_words & sentence_words
            )

            if overlap > 0:

                sentences.append(
                    (
                        overlap,
                        section_score,
                        sentence
                    )
                )

    sentences.sort(
        key=lambda item: (
            item[0],
            item[1]
        ),
        reverse=True
    )

    answer_sentences = []
    seen = set()

    for _, _, sentence in sentences:

        key = sentence.lower()

        if key not in seen:

            seen.add(key)
            answer_sentences.append(sentence)

        if len(answer_sentences) >= 5:
            break

    if not answer_sentences:

        return (
            "I could not find that information in "
            "the Hospital HMS KT document."
        )

    return (
        "Based on the Hospital HMS KT document:\n\n"
        + " ".join(answer_sentences)
    )


@app.get("/")
def home():

    return FileResponse(
        BASE_DIR / "static" / "index.html"
    )


@app.get("/health")
def health():

    return {
        "status": "ok",
        "sections": len(SECTIONS),
        "mode": "free-local-rag"
    }


@app.post("/ask")
def ask(request: AskRequest):

    question = request.question.strip()

    if not question:

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    ranked_sections = sorted(
        [
            (
                similarity(
                    question,
                    section["text"]
                ),
                section
            )
            for section in SECTIONS
        ],
        key=lambda item: item[0],
        reverse=True
    )

    selected_sections = ranked_sections[
        :max(1, min(request.top_k, 8))
    ]

    if (
        not selected_sections
        or selected_sections[0][0] == 0
    ):

        return {
            "answer": (
                "I could not find that information in "
                "the Hospital HMS KT document."
            ),
            "sources": []
        }

    answer = create_answer(
        question,
        selected_sections
    )

    return {
        "answer": answer,
        "sources": [
            {
                "section": (
                    f"{section['number']}. "
                    f"{section['title']}"
                ),
                "similarity": round(
                    score,
                    4
                )
            }
            for score, section
            in selected_sections
        ]
    }
