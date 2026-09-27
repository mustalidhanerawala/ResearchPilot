# ResearchPilot — Agentic Document Intelligence Platform

**Engineered by Mustali Dhanerawala | Computer Engineer**

ResearchPilot is an autonomous Agentic AI document intelligence and research platform engineered from scratch with **FastAPI**, **ChromaDB**, **Sentence Transformers**, and a context-grounded multi-agent reasoning architecture.

Upload PDF research papers or technical documentation, perform semantic chunking with boundary preservation, generate dense high-dimensional vector representations, execute cosine similarity retrieval, and synthesize verifiable, cited answers grounded strictly in document evidence.

---

## Architecture Overview

```
ResearchPilot/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py             # Centralized settings & path resolution
│   │   ├── main.py               # FastAPI application entrypoint
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── documents.py      # PDF upload & indexing endpoint
│   │   │   └── research.py       # Query & research QA endpoint
│   │   ├── rag/
│   │   │   ├── __init__.py
│   │   │   ├── pdf_processor.py  # PyMuPDF page-by-page text extraction
│   │   │   ├── chunker.py        # Text chunking with overlap
│   │   │   ├── embeddings.py     # SentenceTransformers vector generation
│   │   │   ├── vector_store.py   # ChromaDB persistent storage & upsert
│   │   │   └── retriever.py      # Semantic chunk retrieval
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── llm.py            # Google Gemini client & answer generation
│   │       └── research.py       # Orchestration service for RAG + QA
│   ├── data/
│   │   ├── chroma/               # Persistent ChromaDB vector data
│   │   └── uploads/              # Uploaded PDF files
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── test_gemini.py
│   └── test_pdf.py
├── frontend/
│   ├── css/
│   │   └── style.css             # Responsive styling
│   ├── js/
│   │   └── app.js                # Frontend application logic
│   └── index.html                # Research UI
├── docker-compose.yml
├── .env                          # Environment variables (API keys)
└── README.md
```

---

## Getting Started

### 1. Prerequisites
- Python 3.10+
- A Google Gemini API key (from Google AI Studio)

### 2. Configure Environment Variables
Create a `.env` file in the project root:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.1-flash-lite
```

### 3. Install Dependencies
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r backend/requirements.txt
```

### 4. Run the Backend API
You can run the server from either the project root or the `backend` directory:
```bash
# From project root:
uvicorn backend.app.main:app --reload --port 8000

# Or from backend/:
cd backend
uvicorn app.main:app --reload --port 8000
```
- API Documentation (Swagger UI): `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`

### 5. Run the Frontend
Simply open `frontend/index.html` in your web browser, or serve it using any HTTP server:
```bash
# Example with Python's built-in HTTP server:
cd frontend
python -m http.server 3000
```
Open `http://localhost:3000` in your browser.

---

## Running Verification Tests
Execute the standalone test scripts directly:

```bash
# Test Gemini LLM generation directly:
python backend/test_gemini.py

# Test RAG retrieval and question answering on indexed PDFs:
python backend/test_pdf.py
```

---

## Docker Deployment
Run using Docker Compose:
```bash
docker-compose up --build
```
The API will be available on `http://localhost:8000`.
