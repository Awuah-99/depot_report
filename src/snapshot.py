"""
snapshot.py: Utilities for saving/loading data
"""
from pathlib import Path

import pandas as pd

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"
SAMPLE_DIR = Path(__file__).resolve().parent.parent / "data" / "samples"

DEFAULT_FILENAME = "test_sample.pkl"

def save_export(df: pd.DataFrame, name: str = DEFAULT_FILENAME,
                directory: Path = FIXTURES_DIR) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    df.to_pickle(path)
    return path

def load_real_export(name: str = DEFAULT_FILENAME,
                     directory: Path = FIXTURES_DIR) -> pd.DataFrame:
    path = directory / name
    if not path.exists():
        raise FileNotFoundError(f"Snapshot not found: {path}")
    return pd.read_pickle(path)

def find_file(name: str = DEFAULT_FILENAME,
              directory: Path = FIXTURES_DIR) -> bool:
    return (directory / name).exists()

def save_csv_snapshot(df: pd.DataFrame, name: str = "raw_export.csv",
                      directory: Path = SAMPLE_DIR) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    df.to_csv(path, index=False, header=False)
    return path

def load_csv_snapshot(name: str = "raw_export.csv",
                      directory: Path = SAMPLE_DIR) -> pd.DataFrame:
    path = directory / name
    return pd.read_csv(path, header=None, dtype=object, skip_blank_line=False)
