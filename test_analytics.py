import pytest
from analytics import interpret_question, answer_question, load_data, DB_PATH, CSV_PATH

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    load_data(CSV_PATH, DB_PATH)

def test_total_revenue():
    result = answer_question("What is the total revenue?")
    assert "Total revenue is" in result["answer"]
    assert result["data"][0]["transactions"] > 0

def test_top_product():
    result = answer_question("Which product generated the highest revenue?")
    assert result["data"][0]["revenue"] > 0
    assert result["data"][0]["Product"]

def test_monthly_trend():
    result = answer_question("Show the monthly revenue trend")
    assert len(result["data"]) >= 1

def test_top_region():
    result = answer_question("Which region generated the highest sales?")
    assert result["data"][0]["Region"]

def test_month_comparison():
    result = answer_question("Compare revenue between 2026-01 and 2026-02")
    assert len(result["data"]) == 2

def test_unsupported_question():
    result = answer_question("Tell me a joke")
    assert "could not map" in result["answer"]

def test_empty_question():
    assert interpret_question("") == "invalid"
