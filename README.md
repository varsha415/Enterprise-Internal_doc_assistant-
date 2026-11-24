# Acme Tech Enterprise Internal Document Assistant

This project is a role-aware internal knowledge assistant for Acme Tech. It ingests company policy and operations documents, stores them in a local vector database, and answers employee, manager, and admin questions using retrieval-augmented generation (RAG) with citations.

The assistant is designed for internal documentation lookup and is particularly useful for questions about benefits, engineering standards, remote work policy, security policy, procurement, and operational procedures.

## What it does

- Loads Markdown documents from the `data/documents` directory
- Splits them into searchable chunks and stores them in ChromaDB
- Applies role-based access filtering (`employee`, `manager`, `admin`)
- Retrieves the most relevant excerpts for a question
- Returns a grounded answer with source citations
- Rejects unsupported or missing answers with a strict fallback response
- Supports both a mock local mode and optional OpenAI-backed generation

## Tech stack

- Python 3.11+
- ChromaDB for vector search
- Typer + Rich for the CLI experience
- Pydantic settings for environment configuration
- Markdown-based document ingestion and chunking

## Repository structure

- `rag/cli.py` – command-line entrypoints for ingesting, asking, listing, and chatting
- `rag/config.py` – environment and app configuration
- `rag/document_loader.py` – Markdown parsing and chunk creation
- `rag/vector_store.py` – ChromaDB indexing and role filtering
- `rag/engine.py` – retrieval + response logic with citation handling
- `rag/embeddings.py` – embedding-function configuration
- `data/documents/` – source policy and handbook documents
- `.env.example` – sample environment configuration

## Getting started

1. Open a terminal in the project root.
2. Activate the project environment if you are using the bundled virtual environment:

   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

3. Create your local environment file from the example if needed:

   ```powershell
   Copy-Item .env.example .env
   ```

4. Review and adjust settings in `.env` if necessary. The default configuration is intended for local development and uses the local Chroma data directory.

## Configuration

The app reads settings from `.env` using the project root as the default location. Key settings include:

- `CHROMA_PERSIST_DIR` – local vector database storage location
- `DOCUMENTS_DIR` – folder containing the Markdown documents
- `EMBEDDING_PROVIDER` – `chroma`, `openai`, or `mock`
- `LLM_PROVIDER` – `mock` or `openai`
- `OPENAI_API_KEY` – required only if OpenAI is enabled
- `JWT_SECRET_KEY` – local auth secret for development use

## Ingesting documents

Run the ingestion command to index all Markdown files in `data/documents`:

```powershell
python -m rag.cli ingest
```

To reset the existing Chroma collection before re-indexing:

```powershell
python -m rag.cli ingest --reset
```

To ingest from a different folder:

```powershell
python -m rag.cli ingest --docs-dir "C:\path\to\documents"
```

## Asking questions

Run a single question against the indexed knowledge base:

```powershell
python -m rag.cli ask "What are the production deployment windows?" --role employee
```

Available roles:

- `employee`
- `manager`
- `admin`

To request more chunks for the retrieval step:

```powershell
python -m rag.cli ask "What benefits are available?" --role employee --top-k 6
```

## Interactive chat

Start a role-aware chat session:

```powershell
python -m rag.cli chat --role admin
```

During the chat session, you can:

- ask questions as the active role
- type `exit` or `quit` to leave
- type `role employee`, `role manager`, or `role admin` to switch roles

## Listing indexed documents

```powershell
python -m rag.cli list-docs
```

This shows the documents currently indexed in ChromaDB and the chunk counts for each file.

## Security and governance notes

This project intentionally enforces a strict evidence boundary:

- Answers must be grounded in retrieved document excerpts only
- Untrusted content from documents is treated as unsafe input
- No operational or instructive content embedded in the documents is executed
- If the answer is not present in the indexed materials, the assistant returns the exact fallback response: `I couldn't find that in the documents available to you.`

## License

This project is intended for internal enterprise documentation use. Add your preferred license text here if you plan to distribute or share it externally.

## Next steps

Possible enhancements include:

- adding authentication for the assistant
- exposing a web UI or API layer
- integrating a production LLM provider
- adding document refresh workflows and automatic re-indexing
- expanding role controls and audit trails
