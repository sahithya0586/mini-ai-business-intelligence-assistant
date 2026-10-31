# Development Notes

## Tools used
ChatGPT was used as an AI coding assistant for architecture planning, code drafting, explanation, and test-case design.

## How AI was used
- Break the task into data ingestion, database, API, analytics, UI, and testing.
- Draft a small implementation using Python, SQLite, FastAPI, and Streamlit.
- Review edge cases in the supplied sales dataset.
- Prepare setup instructions and interview explanations.

## Problems encountered and debugging
- One row has a missing unit price, one row has zero quantity, and one row is marked Returned.
- The loader validates dates and numeric fields and excludes rows that should not contribute to completed sales revenue.
- Analytics use fixed SQL templates instead of executing user-provided SQL.
- Automated tests cover the five requested analytics plus unsupported and empty questions.

## Improvements with another day
- Add LLM intent extraction returning a strict JSON schema.
- Add charts and filters.
- Expand month/date parsing and test edge cases.
- Add authentication and deployment configuration.
