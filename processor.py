"""
processor.py: Data processing component.
""" 
from typing import Dict, List, Tuple
import os
from datetime import datetime
import traceback

import pandas as pd

from config import CONFIG
from app_logger import setup_logger

logger = setup_logger(__name__)

class DataProcessor:
    def __init__(self):
        self.standard_columns = [
            'order_date', 'order_number', 'products', 
            'volume', 'ex_ref_price', 'brv_number', 'bdc', 'depot'
                ]
        self.table_mapping = {
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
            'MARKED': 'marked'
                }
        self.required_columns = ['order_date', 'order_number']

    def process(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        process raw csv and split into tables
        """
        try:
            table_data = self.split_dataframe_by_sections(df)
            validated_data = {}
            for table_name, section_df in table_data.items():
                standardized_df = self._standardize_section_columns(section_df)
                if standardized_df.empty:
                    logger.warning(f"Section {table_name} became empty after standardization")
                    continue
                if not standardized_df.empty and 'depot' in standardized_df.columns:
                    mask = standardized_df['depot'].astype(str).str.contains('BOST.*KUMASI', case=False, na=False, regex=True)
                    filtered_df = standardized_df[mask].copy()
                    filtered_df = filtered_df.dropna(how='all')
                    # drop rows with more than two empty cells
                    filtered_df = filtered_df[filtered_df.isnull().sum(axis=1) <= 2]
                else:
                    filtered_df = standardized_df
                if filtered_df.empty:
                    logger.warning(f"Section {table_name} become empty after filtering")
                    continue

                if self._validate_section(table_name, filtered_df):
                    validated_data[table_name] = filtered_df
                else:
                   logger.warning(f"Skipping invalid section: {table_name}")
                for name, data in validated_data.items():
                    data.to_csv("report.csv")
            return validated_data
        except Exception as e:
             logger.error(f"Error processing data: str{e}")
             logger.error(traceback.format_exc())

    def find_section_boundaries(self, df: pd.DataFrame) -> Dict[str, Tuple[int, int]]:
        boundaries = {}
        section_starts = {}
        last_col = df.columns[-1]
        for idx, row in df.iterrows():
            section_value = str(row[last_col]).strip().upper()
            first_col_value = str(row[df.columns[0]]).strip().upper()
            # count non-empty values in the row
            non_empty_count = sum(1 for val in row if str(val).strip() not in ['', 'nan', 'NAN'])
            section_candidate = None
            if section_value and section_value != 'NAN' and non_empty_count <= 2:
                section_candidate = section_value
            elif non_empty_count <= 2 and first_col_value and first_col_value != 'NAN':
                section_candidate = first_col_value
            if section_candidate:
                sorted_patterns = sorted(self.table_mapping.items(), key=lambda x: len(x[0]), reverse=True)
                matched = False
                for pattern, table_name in sorted_patterns:
                    if pattern.upper() == section_candidate:
                        # don't override with later occurrence
                        if table_name not in section_starts:
                            section_starts[table_name] = idx
                        matched = True
                        break
                if not matched:
                    for pattern, table_name in sorted_patterns:
                        if pattern.upper() in section_candidate or section_candidate in pattern.upper():
                            if table_name not in section_starts:
                                section_starts[table_name] = idx
                            break


        if not section_starts:
                logger.warning("No sections found, treating entire dataset as 'ordered'")
                section_starts['ordered'] = df.index[0]

        sorted_sections = sorted(section_starts.items(), key=lambda x: x[1])
        for i, (section_name, start_idx) in enumerate(sorted_sections):
            data_start = start_idx + 1
            if i < len(sorted_sections) - 1:
                next_section_header = sorted_sections[i + 1][1]
                data_end = next_section_header - 1
            else:
                  data_end = df.index[-1]
            if data_start <= data_end:
                 boundaries[section_name] = (data_start, data_end)
              
        return boundaries

    def split_dataframe_by_sections(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        boundaries = self.find_section_boundaries(df)

        section_dataframes = {}
        for section_name, (start_idx, end_idx) in boundaries.items():
            try:
                section_df = df.loc[start_idx:end_idx].copy()
                if not section_df.empty:
                    section_dataframes[section_name] = section_df
            except Exception as e:
                logger.error(e)
                continue
        return section_dataframes

    def _standardize_section_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """ Standardize column names and structure for a section """
        try:
            column_mapping = {
                'Unnamed: 0': 'order_date',
                'Unnamed: 2': 'order_number',
                'Unnamed: 5': 'products',
                'Unnamed: 9': 'volume',
                'Unnamed: 10': 'ex_ref_price',
                'Unnamed: 12': 'brv_number',
                'Unnamed: 15': 'bdc',
                'Unnamed: 20': 'depot'
            }
            if 'order_date' in df.columns:
                available_columns = [col for col in self.standard_columns if col in df.columns]
                df = df[available_columns].copy()
            else:
                available_columns = [col for col in column_mapping.keys() if col in df.columns]
                df = df[available_columns].rename(columns=column_mapping)
            for col in self.standard_columns:
                if col not in df.columns:
                    df[col] = ""
            df = df[self.standard_columns]
            return df
        except Exception as e:
            logger.error(e)
            return pd.DataFrame()

    def _validate_section(self,table_name: str, df: pd.DataFrame) -> bool:
        if df.empty:
            logger.warning(f"Empty DataFrame for table {table_name}")
            return False
        if table_name not in self.table_mapping.values():
            logger.warning(f"Unrecognized table {table_name}")
            return False
        available_columns = [col for col in self.required_columns if col in df.columns]
        if not available_columns:
            logger.warning(f"No required columns found in {table_name}")
            return False
        return True



