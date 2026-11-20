"""
processor.py: Data processing component.
""" 
from __future__ import annotations
import re
from typing import Dict, List, Tuple

import pandas as pd
import numpy as np

from config import CONFIG
from app_logger import setup_logger

logger = setup_logger(__name__)

class DataProcessor:
    SECTION_TO_STATUS: Dict[str, str] = {
        'APPROVED': 'approved',
        'BDC CANCEL ORDER': 'bdc_cancel_order',
        'BDC DECLINE': 'bdc_decline',
        'BRV CHECKED': 'brv_checked',
        'DEPOT MANAGER': 'depot_manager',
        'DEPOT MANAGER DECLINE': 'depot_manager_decline',
        'GOOD STANDING': 'good_standing',
        'LOADED': 'loaded',
        'ORDER RELEASED': 'order_released',
        'ORDERED': 'ordered',
        'PPMC CANCEL ORDER': 'ppmc_cancel_order',
        'MARKED': 'marked',
    }

    COLUMN_POSITIONS: Dict[str, int] = {
        'order_date': 0,
        'order_number': 2,
        'product': 5,   
        'volume': 9,
        'ex_ref_price': 10,
        'brv_number': 12,
        'bdc': 15,
        'depot': 20,        
    }    

    NOISE_LABELS = {
        'order number', 'order date', 'daily order report', 'trans date',
        'total#', 'page', 'persol systems'
    }

    def __init__(self, depot: Optional[str] = None, max_nulls: int = 2):
        self.depot = depot if depot is not None else getattr(CONFIG, 'depot', '')
        self.max_nulls = max_nulls
        self.standard_columns = list(self.COLUMN_POSITIONS.keys())

#--------------------------------------------------------------------------API

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            logger.warning("Processor received an empty DataFrame")
            return self._empty()
        df = df.reset_index(drop=True)
        df = df.replace(r"^\s*$", np.nan, regex=True)
        sections = self.split_dataframe_by_sections(df)
        frames = []
        for status, section_df in sections.items():
            std = self._standardize_section_columns(section_df)
            std = self._clean_rows(std)

            if std.empty:
                logger.info("Secrtion '%s': 0 usable rows after cleaning", status)
                continue
            std['status'] = status
            frames.append(std)

        if not frames:
                logger.error("No usable row found in any section. Check Excel layout")
                return self._empty()

        master = pd.concat(frames, ignore_index=True)
        master = self._filter_depot(master)
        master = self._coerce_types(master)
        master = self._apply_null_rule(master)

        logger.info("Successfully processed %d total orders across %d statuses",
                len(master), master['status'].nunique())
        return master

    def find_section_boundaries(self, df: pd.DataFrame) -> list[Tuple[int, str]]:
        first_col = df.iloc[:, 0].astype('string').str.strip().str.upper().fillna('')
        non_empty_counts = df.notna().sum(axis=1).to_numpy()

        patterns = sorted(self.SECTION_TO_STATUS.keys(), key=len, reverse=True)
        headers: List[Tuple[int, str]] = []

        for pos in np.flatnonzero(non_empty_counts <=2):
            label = first_col.iat[pos]
            if not label or len(label) > 60:
                continue

            # Exact match first
            if label in self.SECTION_TO_STATUS:
                headers.append((int(pos), self.SECTION_TO_STATUS[label]))
                continue 
            # Fallback
            for p in patterns:
                if len(p) >= 4 and re.search(rf'\b{re.escape(p)}\b', label):
                    headers.append((int(pos), self.SECTION_TO_STATUS[p]))
                    break
        return headers

    def split_dataframe_by_sections(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        headers = self.find_section_boundaries(df)
        if not headers:
            logger.warning("No section headers found. Treating entire sheet as 'ordered'.")
            return {'ordered': df}
        
        buckets: Dict[str, List[pd.DataFrame]] = {}
        for i, (pos, status) in enumerate(headers):
            start = pos + 1
            end = headers[i + 1][0] - 1 if i + 1 < len(headers) else len(df) - 1

            if start <= end:
                chunk = df.iloc[start:end + 1]
                if not chunk.empty:
                    buckets.setdefault(status, []).append(chunk)
        return {s: pd.concat(v, ignore_index=True) for s, v in buckets.items()}

    #--------------------------------------------------------------- Cleaning

    def _standardize_section_columns(self, df: pd.DataFrame) -> pd.DataFrame:
           out = pd.DataFrame(index=df.index)
           for name, pos in self.COLUMN_POSITIONS.items():
               if pos < df.shape[1]:
                   out[name] = df.iloc[:, pos]
               else:
                    out[name] = np.nan
           return out

    def _clean_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df[-df['order_number'].astype('string').str.startswith('Total#', na=False)]
        first_col_lower = df['order_number'].astype('string').str.lower().str.strip()
        df = df[~first_col_lower.isin(self.NOISE_LABELS)]
        df = df[df['order_number'].notna() & (df['order_number'].astype('string').str.strip() != '')]
        return df

    def _filter_depot(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self.depot:
            return df
        if not df['depot'].notna().any():
            logger.warning("No depot values found; skipping depot filter")
            return df
        mask = df['depot'].astype('string').str.contains(
                self.depot, case=False, na=False, regex=False
                )
        out = df[mask].copy()
        logger.info("Depot filter '%s': %d -> %d rows", self.depot, len(df), len(out))
        return out

    def _apply_null_rule(self, df: pd.DataFrame) -> pd.DataFrame:
        informative = [c for c in self.standard_columns if df[c].notna().any()]
        if not informative:
            return df
        return df[df[informative].isna().sum(axis=1) <= self.max_nulls].copy()
    
    def _coerce_types(self, df: pd.DataFrame) -> pd.DataFrame:
        df['order_number'] = (df['order_number'].astype('string').str.strip()
                              .str.replace(r'\.0$', '', regex=True))
        for col in ('volume', 'ex_ref_price'):
            df[col] = pd.to_numeric(
                    df[col].astype('string').str.replace(',', '', regex=False),
                    errors='coerce'
                    )
        df['order_date'] = pd.to_datetime(df['order_date'], errors='coerce', dayfirst=True, format='%d/%m/%Y')
        for col in ('product', 'brv_number', 'bdc', 'depot'):
            df[col] = df[col].astype('string').str.strip()
        return df

    def _empty(self) -> pd.DataFrame:
        return pd.DataFrame(columns=self.standard_columns + ['status'])
