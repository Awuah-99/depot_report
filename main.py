"""
main.py: Orchestrates the complete pipeline.
1. Fetch data from API
2. Process and split data by order status
4. write processed data to database
5. Optionally export tables to PDF with graphs

Usage:
	python main.py
	python main.py  --pdf
	python main.py  --pdf reports/my_reports.pdf
	python main.py  --pdf-only
"""
import argparse
import sys
from datetime import datetime
from typing import Dict, Optional

import asyncio

# custom include files
from config import CONFIG
from app_logger import setup_logger
from fetcher import DataFetcher
logger = setup_logger(__name__, CONFIG.log_level)

class DataPipeline:
    def __init__(self):
       self.fetcher = DataFetcher()
       # self.processor = DataProcessor()
       # self.writer = DataWriter()
       # self.pdf_generator = PDFReportGenerator()

    async def run(self)-> bool:
        """
        Execute the complete data pipiline
        """
        start_time = datetime.now()
        logger.info("="*60)
        logger.info(" Starting Data Pipeline")
        try:
            df, error_msg = await self.fetcher.fetch_data()
            if error_msg:
                logger.error(error_msg)
                return False
            if df is None or df.empty:
                logger.warning(error_msg)
                return False
            print("Processing next")
            return True
        except Exception as e:
            logger.error(e)
            return False
    def run_sync(self)->bool:
        return asyncio.run(self.run())


pipe = DataPipeline()
pipe.run_sync()
