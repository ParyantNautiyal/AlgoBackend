import logging
import pytest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@pytest.fixture(autouse=True)
def setup_logging():
    logger = logging.getLogger()
    return logger 