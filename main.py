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
from processor import DataProcessor
from writer import DatabaseWriter

from pdf_report import PDFReportGenerator, default_pdf_path

logger = setup_logger(__name__, CONFIG.log_level)

class DataPipeline:
    def __init__(self):
       self.fetcher = DataFetcher()
       self.processor = DataProcessor()
       self.writer = DatabaseWriter()
       self.pdf_generator = PDFReportGenerator()

    async def run(self)-> bool:
        """
        Execute the complete data pipiline
        """
        logger.info("="*60)
        try:
            df, error_msg = await self.fetcher.fetch_data()
            if error_msg:
                logger.error(error_msg)
                return False
            if df is None or df.empty:
                logger.warning(error_msg)
                return False
            self.table_data = self.processor.process(df)
            if not self.table_data:
                logger.warning("No data after processing")
                return False
            results = self.writer.write_all_sections(self.table_data)
            for table_name, rows in results.items():
               if rows > 0:
                   logger.info(f"   - {table_name}: {rows} rows inserted")
            logger.info(f"\n Pipeline completed successfully")
            return True
        except Exception as e:
            logger.error(e)
            return False
    def run_sync(self)->bool:
        return asyncio.run(self.run())

    def generate_pdf(self, output_path: Optional[str] = None) -> bool:
        path = output_path or default_pdf_path()
        data = self.table_data or self.writer.read_all_tables()
        
        if not data:
            logger.error("No table data available for PDF report")
            return False
        return self.pdf_generator.generate(data, path)

def parse_args():
    parser = argparse.ArgumentParser(description='NPA Data Pipeline')
    parser.add_argument(
            '--pdf',
            nargs='?',
            const='',
            metavar='PATH',
            help='Generate PDF report after pipeline run (optional output path)',
            )
    parser.add_argument(
            '--pdf-only',
            nargs='?',
            const='',
            metavar='PATH',
            help='Generate PDF report from database tables without running pipeline',
            )
    return parser.parse_args()

def resolve_pdf_path(path_arg: Optional[str]) -> str:
    """ Resolve PDF output path from CLI argument. """
    if path_arg:
        return path_arg
    return default_pdf_path()

def main():
    args = parse_args()
    logger.info(" Initializing Data Pipeline..")
    pipeline = DataPipeline()

    if args.pdf_only is not None:
        pdf_path = resolve_pdf_path(args.pdf_only or None)
        if not pipeline.generate_pdf(pdf_path):
            sys.exit(1)
        sys.exit(0)
    success = pipeline.run_sync()

    if not success:
        logger.error("Pipeline execution failed")
        sys.exit(1)

    if args.pdf is not None:
        pdf_path = resolve_pdf_path(args.pdf or None)
        if not pipeline.generate_pdf(pdf_path):
            sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()

