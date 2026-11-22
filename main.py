"""
main.py: Orchestrates the complete pipeline.
1. Fetch data from API
2. Process and split data by order status
4. Generate PDF with graph

Usage:
	python main.py 
"""
import sys
from datetime import datetime
from typing import Dict, Optional

import asyncio
import pandas as pd


from src.config import CONFIG
from src.app_logger import setup_logger
from src.fetcher import DataFetcher
from src.processor import DataProcessor
from src.snapshot import save_export, find_file
from src.pdf_report import PDFReportGenerator 

logger = setup_logger(__name__, CONFIG.log_level)

class DataPipeline:
    def __init__(self):
       self.fetcher = DataFetcher()
       self.processor = DataProcessor()
       self.pdf_generator = PDFReportGenerator()
       self.depot = CONFIG.depot
       self.unified_data = pd.DataFrame()

    async def run(self)-> bool:
        try:
            df, error_msg = await self.fetcher.fetch_data()
            if df is None: return False

            if not find_file():
                path = save_export(df)
                logger.info(f"Snapshot saved: {path}")

            self.unified_data = self.processor.process(df)
            if self.unified_data.empty: return False
 
            success = self.pdf_generator.generate(self.unified_data)
            return success
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            return False
    def run_sync(self)->bool:
        return asyncio.run(self.run())

def main():
    logger.info(" Initializing Data Pipeline..")
    pipeline = DataPipeline()

    success = pipeline.run_sync()
    if not success:
        logger.error("Pipeline execution failed")
        sys.exit(1)
    logger.info("Pipeline completed sucessfully")
    sys.exit(0)

if __name__ == "__main__":
    main()

