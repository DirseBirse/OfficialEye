from officialeye.logger.logger import Logger


_logger = Logger()


def get_logger() -> Logger:
    return _logger
