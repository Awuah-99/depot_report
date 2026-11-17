import os
from typing import List, Optional
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime, timedelta

load_dotenv()

class Config:
    url: str = os.getenv("URL", "")
    company_id: str = os.getenv("COMPANY_ID","")
    its_from_persol: str = os.getenv("ITS_FROM_PERSOL", "")
    group_by: str = os.getenv("GROUP_BY", "")
    group_by1: str = os.getenv("GROUP_BY1", "")
    query1: str = os.getenv("QUERY1", "")
    query2: str = os.getenv("QUERY2", "")
    query3: str = os.getenv("QUERY3", "")
    query4: str = os.getenv("QUERY4", "")
    pic_height: str = os.getenv("PIC_HEIGHT", "1")
    pic_weight: str = os.getenv("PIC_WEIGHT", "1")
    period_id: str = os.getenv("PERIOD_ID", "1")
    user_id: str = os.getenv("USER_ID", "")
    app_id: str = os.getenv("APP_ID", "")
    timeout: int = 120
    max_retries: int = 3
    batch_size: int = 100
    clear_tables_before_insert: bool = "true"
    log_level = "INFO"
    date_format = "%Y-%m-%d"
    yesterday = datetime.now() - timedelta(days=1)
    today = datetime.now()

CONFIG = Config()

# Table names
TABLE_NAMES = [
        'approved', 'bdc_cancel_order', 'bdc_decline', 'brv_checked',
    'depot_manager', 'good_standing', 'loaded', 'order_released',
    'ordered', 'ppmc_cancel_order', 'depot_manager_decline', 'marked'
        ]

STANDARD_COLUMNS = [
        'order_date', 'order_number', 'products',
    'volume', 'ex_ref_price', 'brv_number', 'bdc', 'depot'
        ]
