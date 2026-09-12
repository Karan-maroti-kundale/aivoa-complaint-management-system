# AIVOA architecture

Browser → React UI → Redux Toolkit → FastAPI → LangGraph → Groq or deterministic fallback → validated structured complaint → PostgreSQL → UI → QMS commit + audit event.

The application intentionally keeps the LLM behind a LangGraph boundary. AI output is treated as a recommendation, validated and then persisted by backend code. This supports explainability and human review.
