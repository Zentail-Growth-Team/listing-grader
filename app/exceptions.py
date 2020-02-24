import logging

logger = logging.getLogger(__name__)


class ProcessingException(Exception):
    logger.error('Processing Exception')
