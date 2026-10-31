import os
import re
import sqlite3
from pathlib import Path
from datetime import datetime

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "sales.db"
CSV_PATH = BASE_DIR / "ai_bi_assistant_sales_data.csv"

REQUIRED_COLUMNS = [
    "Transaction_Id", "Order_date", "Product", "Category", "Region",
    "Sales_channel", "Quantity", "Unit_price", "Discount_amount", "Status"
]

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def load_data(csv_path=CSV_PATH, db_path=DB_PATH):
    """Load CSV into SQLite after basic validation and cleaning."""
    df = pd.read_csv(csv_path)
    missing_columns = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_columns:
        raise ValueError(f"CSV is missing columns: {missing_columns}")

    df = df[REQUIRED_COLUMNS].copy()
    df["Order_date"] = pd.to_datetime(df["Order_date"], format="%d-%m-%Y", errors="coerce")
    for col in ["Quantity", "Unit_price", "Discount_amount"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Exclude rows that cannot safely contribute to sales calculations.
    valid = (
        df["Order_date"].notna()
        & df["Transaction_Id"].notna()
        & df["Product"].notna()
        & df["Region"].notna()
        & df["Quantity"].notna()
        & (df["Quantity"] > 0)
        & df["Unit_price"].notna()
        & (df["Unit_price"] >= 0)
        & df["Discount_amount"].notna()
        & (df["Discount_amount"] >= 0)
        & (df["Status"].str.lower() == "completed")
    )
    clean = df.loc[valid].copy()
    clean["Order_date"] = clean["Order_date"].dt.strftime("%Y-%m-%d")
    clean["Revenue"] = clean["Quantity"] * clean["Unit_price"] - clean["Discount_amount"]
    clean = clean[clean["Revenue"] >= 0]
    clean.to_sql("sales", sqlite3.connect(db_path), if_exists="replace", index=False)
    return {"input_rows": len(df), "loaded_rows": len(clean), "excluded_rows": len(df) - len(clean)}

def ensure_database():
    if not DB_PATH.exists():
        load_data()

def query_total_revenue():
    with get_connection() as conn:
        row = conn.execute("SELECT ROUND(COALESCE(SUM(Revenue),0),2) AS total_revenue, COUNT(*) AS transactions FROM sales").fetchone()
    return {"answer": f"Total revenue is ₹{row['total_revenue']:,.2f} across {row['transactions']} completed transactions.", "data": [dict(row)]}

def query_top_product():
    sql = """SELECT Product, ROUND(SUM(Revenue),2) AS revenue
             FROM sales GROUP BY Product ORDER BY revenue DESC LIMIT 1"""
    with get_connection() as conn:
        row = conn.execute(sql).fetchone()
    return {"answer": f"{row['Product']} generated the highest revenue: ₹{row['revenue']:,.2f}.", "data": [dict(row)], "sql": sql}

def query_monthly_trend():
    sql = """SELECT strftime('%Y-%m', Order_date) AS month,
                    ROUND(SUM(Revenue),2) AS revenue
             FROM sales GROUP BY month ORDER BY month"""
    with get_connection() as conn:
        rows = conn.execute(sql).fetchall()
    data = [dict(r) for r in rows]
    answer = "Monthly revenue: " + "; ".join(f"{r['month']}: ₹{r['revenue']:,.2f}" for r in data)
    return {"answer": answer, "data": data, "sql": sql}

def query_top_region():
    sql = """SELECT Region, ROUND(SUM(Revenue),2) AS revenue
             FROM sales GROUP BY Region ORDER BY revenue DESC LIMIT 1"""
    with get_connection() as conn:
        row = conn.execute(sql).fetchone()
    return {"answer": f"{row['Region']} generated the highest sales revenue: ₹{row['revenue']:,.2f}.", "data": [dict(row)], "sql": sql}

def query_month_comparison(question):
    months = re.findall(r"(20\d{2}-\d{1,2})", question)
    if len(months) < 2:
        # Also accept month names such as January and February.
        names = {m.lower(): f"2026-{i:02d}" for i, m in enumerate(
            ["January","February","March","April","May","June","July","August","September","October","November","December"], 1)}
        found = [names[m.lower()] for m in re.findall(
            r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\b",
            question, flags=re.I)]
        months = found
    if len(months) < 2:
        return {"answer": "Please mention two months, for example: Compare 2026-01 and 2026-02.", "data": []}
    m1, m2 = months[0], months[1]
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT strftime('%Y-%m', Order_date) AS month, ROUND(SUM(Revenue),2) AS revenue
               FROM sales WHERE strftime('%Y-%m', Order_date) IN (?,?)
               GROUP BY month ORDER BY month""", (m1, m2)
        ).fetchall()
    values = {r["month"]: r["revenue"] for r in rows}
    a, b = float(values.get(m1, 0)), float(values.get(m2, 0))
    change = b - a
    pct = (change / a * 100) if a else None
    direction = "increased" if change > 0 else "decreased" if change < 0 else "did not change"
    pct_text = f" ({pct:.2f}%)" if pct is not None else ""
    return {"answer": f"Revenue {direction} by ₹{abs(change):,.2f}{pct_text} from {m1} (₹{a:,.2f}) to {m2} (₹{b:,.2f}).",
            "data": [{"month": m1, "revenue": a}, {"month": m2, "revenue": b}],
            "sql": "Parameterized monthly revenue comparison query"}

def interpret_question(question):
    """Safe intent classification; never executes SQL generated from user text."""
    q = question.lower().strip()
    if not q:
        return "invalid"
    if any(word in q for word in ["compare", "between", "change", "difference"]) and (
        re.search(r"20\d{2}-\d{1,2}", q) or re.search(r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\b", q)
    ):
        return "compare_months"
    if "total" in q and any(w in q for w in ["revenue", "sales"]):
        return "total_revenue"
    if any(w in q for w in ["highest", "top", "best"]) and "product" in q:
        return "top_product"
    if any(w in q for w in ["monthly", "month-wise", "month wise", "trend"]) and any(w in q for w in ["revenue", "sales"]):
        return "monthly_trend"
    if any(w in q for w in ["highest", "top", "best"]) and any(w in q for w in ["region", "sales"]):
        return "top_region"
    return "unsupported"

def answer_question(question):
    intent = interpret_question(question)
    if intent == "invalid":
        return {"answer": "Please enter a question.", "data": []}
    if intent == "total_revenue":
        return query_total_revenue()
    if intent == "top_product":
        return query_top_product()
    if intent == "monthly_trend":
        return query_monthly_trend()
    if intent == "top_region":
        return query_top_region()
    if intent == "compare_months":
        return query_month_comparison(question)
    return {"answer": "I could not map that question to a supported sales analysis. Try asking about total revenue, top product, monthly trend, top region, or comparing two months.", "data": []}
