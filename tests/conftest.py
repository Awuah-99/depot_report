import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.snapshot import load_export

@pytest.fixture
def sample_raw_df():
    return load_export()

@pytest.fixture
def processor():
    from src.processor import DataProcessor
    return DataProcessor()

@pytest.fixture
def empty_df():
    return pd.DataFrame()
