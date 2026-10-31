import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Sales BI Assistant", page_icon="📊", layout="wide")
st.title("📊 Mini AI Business Intelligence Assistant")
st.caption("Ask questions about sales data and receive answers backed by SQLite queries.")

examples = [
    "What is the total revenue?",
    "Which product generated the highest revenue?",
    "Show the monthly revenue trend",
    "Which region generated the highest sales?",
    "Compare revenue between 2026-01 and 2026-02"
]

with st.sidebar:
    st.header("Try an example")
    for item in examples:
        if st.button(item, use_container_width=True):
            st.session_state["question"] = item
    st.markdown("---")
    st.write("**Data source:** supplied sales CSV")
    st.write("**Database:** SQLite")
    st.write("**Backend:** FastAPI")

question = st.text_input("Enter your business question", value=st.session_state.get("question", ""), placeholder="e.g. What is the total revenue?")
if st.button("Analyze", type="primary") and question.strip():
    try:
        response = requests.post("http://127.0.0.1:8000/query", json={"question": question}, timeout=15)
        response.raise_for_status()
        result = response.json()
        st.subheader("Answer")
        st.success(result.get("answer", "No answer returned"))
        data = result.get("data", [])
        if data:
            st.subheader("Supporting figures")
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        if result.get("sql"):
            with st.expander("Database query used"):
                st.code(result["sql"], language="sql")
    except requests.exceptions.ConnectionError:
        st.error("Backend is not running. Start FastAPI in a second terminal using: uvicorn api:app --reload")
    except requests.exceptions.RequestException as exc:
        st.error(f"Request failed: {exc}")
elif not question.strip():
    st.info("Enter a question or choose an example from the sidebar.")
