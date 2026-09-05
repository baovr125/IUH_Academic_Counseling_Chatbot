# 🤖 Academic Chatbot Service

This is the core **Retrieval-Augmented Generation (RAG)** backend service for the IUH Academic Counseling Chatbot. Built with FastAPI, it powers the AI conversation system by combining Supabase Hybrid Search, local ONNX Machine Learning models, and the Gemini LLM to answer student queries accurately based on official IUH documents.

---

## 🏗️ Folder Structure

```text
services/academic_chatbot_service/
├── app/
│   ├── guardrails/           # Security & relevance filters
│   │   ├── academic_domain_centroid.npy  # Vector centroid representing the "Academic Domain"
│   │   └── query_filter.py               # Jailbreak regex & Cosine Similarity logic
│   ├── routers/              # FastAPI Endpoints
│   │   ├── chat.py                       # Streaming SSE chat endpoints
│   │   ├── sessions.py                   # Chat history / session management
│   │   └── cache.py                      # (Optional) Semantic caching endpoints
│   ├── schemas/              # Pydantic data validation models
│   │   └── chat.py
│   ├── services/             # Core Business Logic
│   │   ├── rag_service.py                # Embedding & Cross-Encoder Reranking pipeline
│   │   ├── llm_generation_service.py     # Gemini API integration & SSE formatting
│   │   ├── chat_service.py               # Supabase DB operations (fetching/saving messages)
│   │   └── log_utils.py                  # Saves daily Markdown logs of RAG chunks
│   ├── utils/
│   └── main.py               # FastAPI application entry point
├── Dockerfile                # Python 3.11-slim container with PyTorch CUDA support
└── requirements.txt          # Python dependencies (optimum, onnxruntime-gpu, fastapi, etc.)
```

---

## ⚙️ How the RAG Pipeline Works

When a student sends a message, it goes through a strict multi-stage pipeline designed for speed, accuracy, and security:

### 1. Guardrails & Topic Filtering (`guardrails/query_filter.py`)
Before touching the database, the query is checked against two layers of defense:
- **Jailbreak Regex:** Blocks attempts to override the system prompt (e.g., "ignore previous instructions").
- **Semantic Domain Guardrail:** The query is embedded and compared against an `academic_domain_centroid.npy` vector. If the Cosine Similarity drops below `0.20`, the system instantly rejects it as "Off-Topic" (e.g., "What is the weather?") without wasting database or LLM resources.

### 2. Stage 1: Hybrid Search (`rag_service.py`)
The query is converted into a vector embedding using the local `vietnamese-bi-encoder-onnx` model running on the GPU. It then calls a Supabase RPC (`match_chunks_hybrid_rrf`) which performs:
- **Dense Vector Search** (Cosine Similarity via `pgvector`)
- **Sparse Full-Text Search** (BM25 Keyword matching)

Both result sets are merged using **Reciprocal Rank Fusion (RRF)** to return a broad candidate pool of ~30 document chunks.

### 3. Stage 2: Cross-Encoder Reranking (`rag_service.py`)
The 30 candidate chunks are passed to the `bge-reranker-v2-m3-onnx` model (running via `CUDAExecutionProvider` on the GPU). The Cross-Encoder reads both the query and the chunk simultaneously to output a highly accurate relevance score (Sigmoid).
- Chunks scoring `< 0.65` are filtered out.
- The system guarantees at least the **Top 3** chunks are passed forward for context.

### 4. LLM Generation & Streaming (`llm_generation_service.py`)
The final filtered chunks are wrapped in a strict `<retrieved_context>` XML sandbox to prevent prompt-injection from the document text itself. The chunks, along with the conversation history, are sent to the Gemini API. 
The LLM's response is streamed back to the frontend chunk-by-chunk using **Server-Sent Events (SSE)** to provide a real-time typing effect.

### 5. Logging (`log_utils.py`)
For analytics and debugging, every RAG query is saved locally. It automatically creates a daily folder (e.g., `logs/academic_chatbot/2026-08-24/`) and saves a `.md` file containing the query, the retrieved chunks, and their exact rerank scores. The filename is cleanly slugified (e.g., `090630-thoi-gian-dong-hoc-phi.md`).

---

## ⚠️ Important: Local Machine Learning Models

To keep the Git repository size small and push/pull times fast, the local Machine Learning models (`hf_models/`) are ignored by Git. 
**The backend container will fail to start if you do not have these models installed locally.**

### Required Models
The service relies on two ONNX-optimized models:
1. `vietnamese-bi-encoder-onnx` (for embedding generation)
2. `bge-reranker-v2-m3-onnx` (for cross-encoder reranking)

### How Collaborators Can Get the Models

Before running `docker compose up -d`, collaborators must download the models into the root `hf_models/` folder.

**Option 1: Download from Shared Drive (Recommended)**
Ask the project maintainer for the Google Drive / OneDrive link to the pre-optimized `hf_models.zip` file.
1. Download the zip file.
2. Extract the contents directly into the root folder of this project so that the path looks like this:
   `IUH_Academic_Counseling_Chatbot/hf_models/vietnamese-bi-encoder-onnx/...`
3. Run `docker compose up -d`!

**Option 2: Download manually using the Python script**
If the models are publicly hosted on Hugging Face, you can easily download them using the provided script.
*Note: Make sure to edit `scripts/download_models.py` first to set the correct Hugging Face username where the ONNX models are hosted.*

```bash
# Run the automated download script
python scripts/download_models.py
```
