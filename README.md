# Mini AI Business Intelligence Assistant

A small Python application that answers natural-language sales questions using validated intent mapping and deterministic SQLite queries.

## Features
- Imports the supplied CSV into SQLite.
- Answers total revenue, top product, monthly trend, top region, and two-month comparison.
- Shows supporting figures and the SQL query where applicable.
- Excludes returned transactions, missing/invalid prices, invalid dates, and non-positive quantities.
- Uses parameterized SQL for month comparisons. User text is never executed as SQL.
- Includes FastAPI backend, Streamlit UI, and automated tests.

## Setup
1. Install Python 3.10 or newer.
2. Create and activate a virtual environment:
   - Linux/macOS: `python3 -m venv venv && source venv/bin/activate`
   - Windows: `py -m venv venv && venv\\Scripts\\activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Keep `ai_bi_assistant_sales_data.csv` in this folder.
5. Start backend in terminal 1: `uvicorn api:app --reload`
6. Start frontend in terminal 2: `streamlit run app.py`
7. Open the Streamlit URL shown in the terminal (usually http://localhost:8501).
8. API documentation is available at http://127.0.0.1:8000/docs.

## Tests
Run: `pytest -q`

## Architecture
CSV -> Pandas validation/cleaning -> SQLite (`sales` table) -> FastAPI `/query` endpoint -> intent classification -> fixed SQL analytics -> JSON response -> Streamlit UI.

## Revenue and data-quality rules
Revenue = Quantity * Unit_price - Discount_amount.
Only `Completed` transactions with valid dates, non-null product/region, positive quantity, non-negative unit price and discount, and non-negative calculated revenue are loaded. Returned rows and invalid rows are excluded. Zero unit price is retained as supplied; it contributes zero revenue and should be verified with the data owner.

## AI approach and safety
The current implementation uses a transparent natural-language intent interpreter (keyword/phrase mapping) to select one of five predefined analytics operations. It does not generate arbitrary SQL. This makes the output reproducible and prevents destructive SQL. For a production extension, an LLM could map questions to a strict JSON intent schema, with server-side validation and allow-listed query templates before execution.

## Known limitations
- The intent interpreter supports a defined set of question patterns, not unrestricted conversation.
- Month-name comparison assumes the supplied year is 2026; YYYY-MM is preferred.
- This is a local demo; authentication, deployment, and multi-user support are not included.

## AI-assisted development note
AI tool used: ChatGPT.
AI assistance: planning the architecture, drafting and explaining Python/FastAPI/Streamlit code, identifying data-quality rules, and preparing test cases and documentation. The implementation was reviewed against the assessment requirements; all SQL analytics are deterministic and use fixed query templates.
Problems/debugging: data validation and date parsing were handled before database insertion; invalid and returned records are excluded to avoid misleading totals. The tests verify supported questions and unsupported/empty input.
With one more day: add optional LLM-based intent extraction with strict schema validation, charts, broader date parsing, richer tests, and deployment.
