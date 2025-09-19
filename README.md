# TensorPilot: LangGraph-based Agentic Math Reasoning

This repository implements an agentic AI stack for structured mathematical reasoning. It composes a ReAct planner, an agentic RAG (global + per-user), an in-memory conversational memory store, and a Model Context Protocol (MCP) math toolset. The code is organized to run locally for research and to be extended for Azure deployment.

## Key Components

- ReAct planner: decomposes math problems into stepwise plans and optionally verifies steps with computation tools.
- Agentic RAG: global and per-user document stores for formula sheets, proofs, and notes used to provide context.
- MemoryStore: in-memory conversation and profile memory with optional embedding support (Azure OpenAI embeddings if configured).
- MCP math tools: SymPy, NumPy, MathJS, WolframAlpha wrapper, and plotting utilities exposed via `src/llm/mcp.py`.
- LangGraph integration: optional wrapper that registers RAG and MCP tools into a LangGraph `Graph` when the `langgraph` package is available; otherwise the local orchestrator is used.

## Directory Highlights

- `src/workflow/graph.py` — LangGraphSystem and LangGraphWrapper (orchestration entrypoint).
- `src/workflow/react.py` — ReActPlanner that decomposes problems and calls MCP tools.
- `src/workflow/rag.py` — RAGManager for global and per-user documents.
- `src/workflow/memory.py` — MemoryStore (used by RAGManager in this layout).
- `src/llm/mcp.py` — Model Context Protocol math tools (SymPy, NumPy, MathJS, plotting).

## Quick Start (local)

1. Install Python (3.8+) and dependencies; a minimal set is listed in `requirements.txt`.

2. Create a virtual environment and install:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
```

3. Run the LangGraphSystem demo (uses local in-memory stores and MCP tools):

```powershell
python src\workflow\graph.py
```

4. Run unit tests:

```powershell
pytest -q
```

## Azure Notes

- The code includes optional scaffolding to call Azure OpenAI embeddings (see `src/workflow/memory.py` and `src/workflow/react.py`). To enable embeddings and Azure LLM usage you must set the appropriate environment variables and provide deployment names. Follow Azure OpenAI documentation for obtaining endpoints and keys.
- The repo also contains Terraform under `infrastructure/terraform` for deploying cloud services; follow that folder's README when you're ready to deploy.

## Development Notes & Next Steps

- The current memory and RAG implementations are in-memory and suitable for prototyping. For production, persist vectors and docs in a vector DB (FAISS, Pinecone, Weaviate) and a document DB.
- The LangGraph wrapper is best-effort; if you use a specific `langgraph` API version I can adapt the integration to its exact constructor and lifecycle.
- I can add more robust decomposition, proof step generation, and MCP server integration as next tasks.

# Credits

Developed by Evan Chou — associated with AI Club at Pasadena City College
