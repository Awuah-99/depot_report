"""
writer.py: Database writer component
"""
import traceback
from typing import Dict, List, Optional

import pandas as pd
import sqlite3

from config import CONFIG, TABLE_NAMES, STANDARD_COLUMNS
from app_logger import setup_logger

logger = setup_logger(__name__)

class DatabaseWriter:

    def __init__(self):
        self.db_config = {}
        self.batch_size = CONFIG.batch_size
        self.clear_before_insert = CONFIG.clear_tables_before_insert

    def create_tables(self) -> bool:
        """ create all tables if they don't exist. """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS {table_name}(
        id SERIAL PRIMARY KEY,
        order_date TEXT,
        order_number TEXT,
        products TEXT,
        Volume TEXT,
        ex_ref_price TEXT,
        brv_number TEXT,
        bdc TEXT,
        depot TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        try:
            
            logger.info("SOOON")
            return True
        except Exception as e:
            logger.debug(traceback.format_exc())
            return False

    def clear_table(self, table_name: str) -> bool:
        """ clear all data from a table. """
        if table_name not in TABLE_NAMES:
            logger.warning(f"Unknown table name: {table_name}")
            return False
        try:
            logger.info("SOON")
            return True
        except Exception as e:
            return False

    def write_section(self, table_name: str, df: pd.DataFrame) -> int:
        """
        Write a DataFrame to the specified table.
        """
        if table_name not in TABLE_NAMES:
            logger.warning(f"Unknown table name: {table_name}")
            return 0
        if df.empty:
            logger.warning(f"Empty DataFrame for table {table_name}")
            return 0
        if self.clear_before_insert:
            self.clear_table(table_name)

        columns = [col for col in STANDARD_COLUMNS if col in df.columns]
        if not columns:
            logger.error(f"No valid columns found for table {table_name}")
            return 0
        records = []
        for _, row in df.iterrows():
            record = tuple(str(row.get(col, '')) if pd.notna(row.get(col)) else '' for col in columns)
            records.append(record)
        try:
            logger.info("SOON")
            return 1
        except Exception as e:
            logger.debug(traceback.format_exc())
            return 0

    def write_all_sections(self, table_data: Dict[str, pd.DataFrame]) -> Dict[str, int]:
        """
        write all processed sections to their respective tables.
        """
        results = {}
        logger.info(f" Writing {len(table_data)} sections to database")
        for table_name, df in table_data.items():
            rows_inserted = self.write_section(table_name, df)
            results[table_name] = rows_inserted
        return results

    def read_all_tables(self) -> Dict[str, pd.DataFrame]:
        """ Read all table data from the database. """
        table_data = {}
        try:
            logger.info("SOON")
            return {}
        except Exception as e:
            logger.debug(traceback.format_exc())
            return {}

