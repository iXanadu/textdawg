import logging

def setup_logger(name):
    print(f"setup_logger called for: {name}")
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # File handler - logs to a file
    file_handler = logging.FileHandler(name + '.log')
    file_handler.setLevel(logging.DEBUG)

    # Console handler - logs to the console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    # Formatter for the log messages
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Adding handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
