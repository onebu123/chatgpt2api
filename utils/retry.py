from fastapi import HTTPException

from utils.Logger import logger
from utils.configs import retry_times

NON_RETRYABLE_STATUS = {400, 401, 403, 404, 422}


async def async_retry(func, *args, max_retries=retry_times, **kwargs):
    for attempt in range(max_retries + 1):
        try:
            result = await func(*args, **kwargs)
            return result
        except HTTPException as e:
            if e.status_code in NON_RETRYABLE_STATUS:
                raise HTTPException(status_code=e.status_code, detail=e.detail)
            if attempt == max_retries:
                logger.error(f"Throw an exception {e.status_code}, {e.detail}")
                if e.status_code == 500:
                    raise HTTPException(status_code=500, detail="Server error")
                raise HTTPException(status_code=e.status_code, detail=e.detail)
            logger.info(f"Retry {attempt + 1} status code {e.status_code}, {e.detail}. Retrying...")


def retry(func, *args, max_retries=retry_times, **kwargs):
    for attempt in range(max_retries + 1):
        try:
            result = func(*args, **kwargs)
            return result
        except HTTPException as e:
            if e.status_code in NON_RETRYABLE_STATUS:
                raise HTTPException(status_code=e.status_code, detail=e.detail)
            if attempt == max_retries:
                logger.error(f"Throw an exception {e.status_code}, {e.detail}")
                if e.status_code == 500:
                    raise HTTPException(status_code=500, detail="Server error")
                raise HTTPException(status_code=e.status_code, detail=e.detail)
            logger.error(f"Retry {attempt + 1} status code {e.status_code}, {e.detail}. Retrying...")
