"""
tests/test_processor.py
Run with: pytest tests/ -v
"""
import pandas as pd
import numpy as np
import pytest
from processor import DataProcessor

@pytest.fixture
def processor():
    return DataProcessor()

@pytest.fixture
def sample_excel_df():
    rows = [
        # --- noise at top ---
        ["DAILY ORDER REPORT", None, None, None, None, None, None, None, None, None,
         None, None, None, None, None, None, None, None, None, None, None],
        ["TRANS DATE: 20/11/2026", None, None, None, None, None, None, None, None, None,
         None, None, None, None, None, None, None, None, None, None, None],

        # --- APPROVED section header ---
        ["Approved", None, None, None, None, None, None, None, None, None,
         None, None, None, None, None, None, None, None, None, None, None],
        # --- APPROVED data row 1 (depot = SENTUO) ---
        ["Amh0228", "AGO(Retail Outlets)", "54,000.00", "AD112326", "13.90",
         "20/11/2026", "CIRRUS OIL SERVICES LIMITED", None, None, None,
         None, None, None, None, None, None, None, None, None, None,
         "SENTUO OIL REFINERY- TEMA"],
        # --- APPROVED data row 2 (depot = KUMASI - should be filtered out) ---
        ["Amh0229", "PMS(Retail Outlets)", "27,000.00", "AD112327", "9.20",
         "20/11/2026", "CIRRUS OIL SERVICES LIMITED", None, None, None,
         None, None, None, None, None, None, None, None, None, None,
         "BOST- KUMASI"],
        # --- APPROVED footer (noise) ---
        ["Total# for Approved is 2", None, None, None, None, None, None, None, None, None,
         None, None, None, None, None, None, None, None, None, None, None],

        # --- LOADED section header ---
        ["Loaded", None, None, None, None, None, None, None, None, None,
         None, None, None, None, None, None, None, None, None, None, None],
        # --- LOADED data row ---
        ["HUSS/067GP", "AGO(Retail Outlets)", "27,000.00", "GR840615", "14.00",
         "20/11/2026", "BLUE OCEAN ENERGY LIMITED", None, None, None,
         None, None, None, None, None, None, None, None, None, None,
         "SENTUO OIL REFINERY- TEMA"],
        ["Total# for Loaded is 1", None, None, None, None, None, None, None, None, None,
         None, None, None, None, None, None, None, None, None, None, None],
    ]
    return pd.DataFrame(rows)

#------------- section boundary tests -------

def test_finds_section_headers(processor, sample_excel_df):
    headers = processor.find_section_boundaries(sample_excel_df)
    statuses = [status for _, status in headers]
    assert "approved" in statuses
    assert "loaded" in statuses

def test_ignores_noise_rows(processor, sample_excel_df):
    headers = processor.find_section_boundaries(sample_excel_df)
    labels = [sample_excel_df.iloc[pos, 0] for pos, _ in headers]
    for label in labels:
        assert "DAILY" not in label.upper()
        assert "TRANS DATE" not in label.upper()

def test_splits_into_sections(processor, sample_excel_df):
    sections = processor.split_dataframe_by_sections(sample_excel_df)
    assert "approved" in sections
    assert "loaded" in sections

#------- cleaning tests ------------

def test_removes_footer_rows(processor, sample_excel_df):
    approved_section = processor.split_dataframe_by_sections(sample_excel_df)["approved"]
    cleaned = processor._clean_rows(
        processor._standardize_section_columns(approved_section)
    )
    order_numbers = cleaned["order_number"].astype(str).tolist()
    assert not any("Total#" in on for on in order_numbers)

def test_removes_empty_order_numbers(processor):
    df = pd.DataFrame({
        "order_number": ["ABC123", "", None, "DEF456"],
        "product": ["AGO", "PMS", "AGO", "PMS"],
    })
    cleaned = processor._clean_rows(df)
    assert len(cleaned) == 2
    assert list(cleaned["order_number"]) == ["ABC123", "DEF456"]

#--------- column standardization ------------

def test_positional_column_mapping(processor):
    df = pd.DataFrame([["ORD001", "PMS(Retail)", "10,000", "BRV1", "9.50",
                        "20/11/2026", "BDC1", "DEPOT1"]])
    std = processor._standardize_section_columns(df)
    assert std.iloc[0]["order_number"] == "ORD001"
    assert std.iloc[0]["product"] == "PMS(Retail)"
    assert std.iloc[0]["volume"] == "10,000"


# ---------- Type Coercion Tests ----------

def test_coerces_volume_with_commas(processor):
    df = pd.DataFrame({"volume": ["54,000.00", "27,000", "invalid"],
                       "ex_ref_price": ["13.90", "9.20", "bad"],
                       "order_date": ["20/11/2026", "21/11/2026", "nope"],
                       "order_number": ["A", "B", "C"],
                       "product": ["PMS", "AGO", "PMS"],
                       "brv_number": ["x", "y", "z"],
                       "bdc": ["a", "b", "c"],
                       "depot": ["d", "e", "f"]})
    coerced = processor._coerce_types(df)
    assert coerced.iloc[0]["volume"] == 54000.0
    assert coerced.iloc[1]["volume"] == 27000.0
    assert pd.isna(coerced.iloc[2]["volume"])
    assert pd.isna(coerced.iloc[2]["order_date"])

def test_strips_trailing_dot_zero_from_order_number(processor):
    df = pd.DataFrame({"order_number": ["123456.0", "ABC789"],
                       "volume": [1, 1], "ex_ref_price": [1, 1],
                       "order_date": ["20/11/2026", "20/11/2026"],
                       "product": ["PMS", "AGO"], "brv_number": ["x", "y"],
                       "bdc": ["a", "b"], "depot": ["d", "e"]})
    coerced = processor._coerce_types(df)
    assert coerced.iloc[0]["order_number"] == "123456"
    assert coerced.iloc[1]["order_number"] == "ABC789"


# ---------- Depot Filter Tests ----------

def test_filters_by_depot(processor):
    df = pd.DataFrame({
        "order_number": ["A", "B", "C"],
        "depot": ["SENTUO OIL REFINERY", "BOST- KUMASI", "sentuo refinery"],
    })
    filtered = processor._filter_depot(df)
    assert len(filtered) == 2
    assert list(filtered["order_number"]) == ["A", "C"]

def test_filter_handles_missing_depot_column(processor):
    df = pd.DataFrame({"order_number": ["A"], "product": ["PMS"]})
    filtered = processor._filter_depot(df)
    assert len(filtered) == 1

#----------- product classification ----

def test_classify_product_pms():
    from pdf_report import classify_product
    assert classify_product("PMS(Retail Outlets)") == "PMS"
    assert classify_product("PMS-Additivated") == "PMS"


#---------- smoke test ----------------

def test_full_pipeline_smoke(processor, sample_excel_df):
    result = processor.process(sample_excel_df)
    assert not result.empty
    assert "status" in result.columns
    assert "order_number" in result.columns
    assert len(result) >= 1
    assert all("SENTUO" in str(d).upper() for d in result["depot"])






