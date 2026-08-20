import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DOC_FILE = BASE_DIR / "docs" / "hms_kt.md"
DATA_DIR = BASE_DIR / "data"
INDEX_FILE = DATA_DIR / "index.json"

MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")


def get_sections(text):
    pattern = re.compile(r"(?m)^## (\d+)\.\s+(.+)$")
    matches = list(pattern.finditer(text))
    sections = []

    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[start:end].strip()
        title = f"{match.group(1)}. {match.group(2).strip()}"
        sections.append({"section": title, "text": block})

    return sections


api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise SystemExit("ERROR: OPENAI_API_KEY is missing.")

if not DOC_FILE.exists():
    raise SystemExit(f"ERROR: Source document not found: {DOC_FILE}")

client = OpenAI(api_key=api_key)
sections = get_sections(DOC_FILE.read_text(encoding="utf-8"))

if not sections:
    raise SystemExit("ERROR: No KT sections found.")

DATA_DIR.mkdir(exist_ok=True)

items = []
for section in sections:
    result = client.embeddings.create(
        model=MODEL,
        input=section["text"]
    )
    items.append({
        "section": section["section"],
        "text": section["text"],
        "embedding": result.data[0].embedding
    })
    print("Embedded:", section["section"])

INDEX_FILE.write_text(
    json.dumps(items, ensure_ascii=False),
    encoding="utf-8"
)

print(f"SUCCESS: Created {INDEX_FILE} with {len(items)} sections.")
