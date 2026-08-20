# Hospital Management System RAG

This is a simple, working Retrieval-Augmented Generation (RAG) project based on the 40-section Hospital Management System KT.

## Architecture

User
-> FastAPI web UI
-> create embedding for question
-> cosine similarity against KT embeddings
-> retrieve top sections
-> send retrieved context to GPT-5.6 Luna
-> answer + retrieved sections

## Local setup

### 1. Install Python
Use Python 3.10 or newer.

### 2. Install packages

```bash
pip install -r requirements.txt
```

### 3. Create `.env`

Copy `.env.example` to `.env` and set:

OPENAI_API_KEY=your_real_key
CHAT_MODEL=gpt-5.6-luna
EMBEDDING_MODEL=text-embedding-3-small

Never upload `.env` to GitHub.

### 4. Create the RAG index

```bash
python ingest.py
```

You should see:

SUCCESS: Created .../data/index.json with 40 sections.

### 5. Start the application

```bash
uvicorn app:app --reload
```

Open:

http://127.0.0.1:8000

## Example questions

- Who are the users of HMS?
- Explain the appointment management workflow.
- How does appointment validation work?
- What are the important database tables?
- Explain the laboratory workflow.
- What is the role of the service layer?
- What are common production issues?
- Explain the CI/CD pipeline.
- What happens during patient discharge?

## Render deployment

Use the included `render.yaml`.

In Render, create the Web Service from your GitHub repository and add:

OPENAI_API_KEY = your real OpenAI API key

The build command installs packages and creates the RAG index. The start command runs FastAPI.

The API key must be stored as a Render environment variable, not in the source code.

## Important

This is an educational RAG demo. It contains no real patient records. Do not put real patient medical information into this demo.
