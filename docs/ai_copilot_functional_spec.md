# Functional Specification: AI Copilot Module

## 1. Purpose
The **AI Copilot Module** provides AI-assisted scientific workflows embedded within the ELN platform. It offers experiment summarization, notebook drafting, protocol generation, scientific Q&A, sample insights, sequence interpretation, semantic search, and citation generation — all scoped to tenant isolation with full audit trails.

## 2. Supported AI Features

| Feature | Description |
|---|---|
| Experiment Summarization | Generate structured summaries of experiment records |
| Notebook Summarization | Condense ELN notebook entries into scientific summaries |
| Protocol Drafting | Generate draft SOPs and protocol steps from a natural language description |
| Scientific Q&A | Answer domain-specific scientific questions using tenant knowledge base |
| Sample Insights | Infer sample quality, provenance, and usage patterns |
| Sequence Interpretation | Annotate DNA/RNA/Protein sequences with functional context |
| Semantic Search | Retrieve semantically similar documents using pgvector embeddings |
| Citation Generation | Cite source documents used in RAG-augmented responses |

## 3. RAG Architecture

```
[USER PROMPT]
     │
     ▼
[EMBEDDING MODEL] ─── embed prompt ──▶ [pgvector SIMILARITY SEARCH]
                                               │
                                        [TOP-K KNOWLEDGE DOCS]
                                               │
     ┌─────────────────────────────────────────┘
     ▼
[AUGMENTED PROMPT = system context + retrieved docs + user prompt]
     │
     ▼
[LLM PROVIDER] ──── OpenAI / Azure OpenAI / Compatible API ────▶ [RESPONSE]
     │
     ▼
[CITATION EXTRACTION] ──▶ [AUDIT LOG] ──▶ [RESPONSE TO CLIENT]
```

## 4. Provider Abstraction
The module uses a provider-agnostic `AIProvider` interface supporting:
- OpenAI (`gpt-4o`, `gpt-4-turbo`, `text-embedding-3-small`)
- Azure OpenAI
- Any OpenAI-compatible API (e.g. vLLM, Ollama, Groq)

## 5. Business Rules
1. All prompts, responses, and embeddings are strictly scoped to `tenant_id`.
2. Conversation history is maintained per `AIConversation` and included in context.
3. Every prompt/response pair is written to `AIAuditLog` for 21 CFR Part 11 compliance.
4. RAG responses include structured `CitationRead` objects referencing source documents.
5. Provider failures are caught and returned as structured error responses (no 500 propagation).
6. Token usage and latency are recorded on every `AIMessage`.
7. Long-running jobs (bulk embedding, indexing) are tracked as `AIJob` records with `queued → running → completed/failed` status.

## 6. Acceptance Criteria
1. All AI endpoints require valid tenant + user authentication.
2. Semantic search returns ranked results with cosine similarity scores.
3. Every chat response includes citations when RAG context is used.
4. Audit log captures provider, model, token count, latency, and user for every call.
5. Provider errors return `{"error": "...", "provider": "..."}` without leaking API keys.
