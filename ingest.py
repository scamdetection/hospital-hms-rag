from pathlib import Path
import re

BASE_DIR = Path(__file__).resolve().parent
DOC_FILE = BASE_DIR / "docs" / "hms_kt.md"


def get_sections(text):
    pattern = re.compile(r"(?m)^## (\d+)\.\s+(.+)$")

    matches = list(pattern.finditer(text))

    sections = []

    for i, match in enumerate(matches):

        start = match.start()

        end = (
            matches[i + 1].start()
            if i + 1 < len(matches)
            else len(text)
        )

        block = text[start:end].strip()

        title = (
            f"{match.group(1)}. "
            f"{match.group(2).strip()}"
        )

        sections.append({
            "section": title,
            "text": block
        })

    return sections


if not DOC_FILE.exists():

    raise SystemExit(
        f"ERROR: Source document not found: {DOC_FILE}"
    )


text = DOC_FILE.read_text(
    encoding="utf-8"
)

sections = get_sections(text)


if not sections:

    raise SystemExit(
        "ERROR: No KT sections found."
    )


print(
    f"SUCCESS: Found {len(sections)} HMS KT sections."
)

print(
    "Free local RAG mode enabled."
)

print(
    "No OpenAI API key is required."
)

for section in sections:

    print(
        "Loaded:",
        section["section"]
    )
