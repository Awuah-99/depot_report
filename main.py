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

# custom include files
from config import CONFIG
from app_logger import setup_logger
from fetcher import DataFetcher
from processor import DataProcessor

from pdf_report import PDFReportGenerator, default_pdf_path 

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

            self.unified_data = self.processor.process(df)
            if self.unified_data.empty: return False

            output_path = default_pdf_path(CONFIG.depot)

            success = self.pdf_generator.generate(self.unified_data, output_path)
            if success: return success
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
    sys.exit(0)

if __name__ == "__main__":
    main()

