import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

logger = logging.getLogger()

# Disable httpx INFO logs
httpx_logger = logging.getLogger('httpx')
httpx_logger.setLevel(logging.WARNING)
