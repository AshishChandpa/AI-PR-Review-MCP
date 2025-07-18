import logging
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from config.settings import settings
except ImportError:
    # Fallback settings if config is not available
    class FallbackSettings:
        LOG_LEVEL = "INFO"
        LOG_FILE = "pr_review.log"


    settings = FallbackSettings()


def get_logger(name: str) -> logging.Logger:
    """Get configured logger"""
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    return logger
