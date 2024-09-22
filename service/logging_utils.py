import logging


format_pattern = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FORMAT = (format_pattern)

logging.basicConfig(format=LOG_FORMAT)

LOGGER = logging.getLogger(__name__)

LOGGER.setLevel(logging.DEBUG)