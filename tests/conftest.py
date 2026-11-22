import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

FIXTURES_DIR = Path(__file__).parent / "fixtures"

def save_real_export(df: pd.DataFrame, name: str = "sample_export.pkl"):
    FIXTURES_DIR.mkdir(exist_ok=True)
    df.to_pickle(FIXTURES_DIR / name)

def load_real_export(name: str = "sample_export.pkl") -> pd.DataFrame:
    return pd.read_pickle(FIXTURES_DIR / name)



