"""
سیستم لاگینگ

نویسنده: MT5 Trading Team
"""

import logging
import sys
from typing import Optional


# فرمت لاگ
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    ایجاد لاگر

    Args:
        name: نام لاگر
        level: سطح لاگ (اختیاری)

    Returns:
        لاگر پیکربندی شده
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        logger.addHandler(handler)

    if level:
        logger.setLevel(level)
    elif not logger.level:
        logger.setLevel(logging.INFO)

    return logger


def set_log_level(level: int) -> None:
    """
    تنظیم سطح لاگ برای همه

    Args:
        level: سطح لاگ
    """
    logging.getLogger().setLevel(level)


# لاگرهای اصلی
analysis_logger = get_logger("analysis")
decision_logger = get_logger("decision_engine")
api_logger = get_logger("api")
