"""
fetcher.py: Data fetching component for Data API
"""
from datetime import datetime, timedelta
from io import BytesIO
from typing import Tuple, Optional
import traceback
import ssl

import asyncio
import aiohttp
import pandas as pd

from config import CONFIG
from app_logger import setup_logger

logger = setup_logger(__name__)

class FetchResult:
    pass
class DataFetcher:
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=CONFIG.timeout)
        self.max_retries = CONFIG.max_retries

    def build_params(self)-> dict:
        return{
            'lngCompanyId': CONFIG.company_id,
            'szITSfromPersol': CONFIG.its_from_persol,
            'strGroupBy': CONFIG.group_by,
            'strGroupBy1': CONFIG.group_by1,
            'strQuery1': CONFIG.query1,
            'strQuery2': CONFIG.yesterday.strftime(CONFIG.date_format),
            'strQuery3': CONFIG.today.strftime(CONFIG.date_format),
            'strQuery4': CONFIG.query4,
            'strPicHeight': CONFIG.pic_height,
            'strPicWeight': CONFIG.pic_weight,
            'intPeriodID': int(CONFIG.period_id),
            'iUserId': int(CONFIG.user_id),
            'iAppId': int(CONFIG.app_id)
                }
    def build_headers(self)-> dict:
        return {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
                }
    async def fetch_data(self)-> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """
        Fetch data from API
        Returns tuple of (DataFetcher, error_message)
        """
        # Create SSL ontext
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        connector = aiohttp.TCPConnector(ssl=ssl_context)

        # Use a single session for all retries to avoid "Session is closed error"
        async with aiohttp.ClientSession(
                connector=connector,
                timeout=self.timeout
                ) as session:
            for attempt in range(self.max_retries):
                try:
                    start_time = datetime.now()
                    logger.info(f"Fetching data from API (attempt {attempt+1}/{self.max_retries})")
                    async with session.get(
                            url=CONFIG.url,
                            params=self.build_params(),
                            headers=self.build_headers()
                            ) as response:
                        if response.status != 200:
                            logger.warning(f"HTTP{response.status} on attempt {
                                           attempt+1}")
                            if attempt == self.max_retries - 1:
                                return None, f"HTTP {response.status}:{response.reason}"
                            continue
                        content = await response.read()
                        if not content:
                            if attempt == self.max_retries -1:
                                return None, "Empty response from API"
                            continue
                        # Parse Excel data
                        try:
                            df = await asyncio.to_thread(pd.read_excel, BytesIO(content))
                            if df.empty:
                                if attempt == self.max_retries - 1:
                                    return None, "Empty DataFrame received"
                                continue

                            response_time = (datetime.now() - start_time).total_seconds()
                            logger.info(f"Successfully fetched {len(df)} rows in {response_time:.2f}s")
                            #----- remove later(local Test) replace with file verification logic--
                            save_real_export(df)
                            return df, None

                        except Exception as e:
                            logger.error(f"Failed to parse Excel data: {str(e)}")
                            if attempt == self.max_retries - 1:
                                return None, f"Failed to parse Excel data: {str(e)}"

                except asyncio.TimeoutError:
                    error_msg = f"API request timed out (attempt {attempt + 1})"
                    logger.warning(error_msg)
                    if attempt == self.max_retries - 1:
                            return None, error_msg

                    await asyncio.sleep(2 ** attempt)

                except Exception as e:
                    error_msg = f"Request failed: {str(e)}"
                    logger.error(f"{error_msg} (attempt {attempt + 1})")
                    logger.debug(traceback.format_exc())
                    if attempt == self.max_retries - 1:
                        return None, error_msg
                    await asyncio.sleep(2 ** attempt)

        return None, "Maximum retries exceeded"

