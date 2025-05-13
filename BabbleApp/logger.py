import re
import logging
import os
import sys
import platform
import psutil
from logging.handlers import RotatingFileHandler

def strip_ansi_codes(text):
    """Remove ANSI color codes from a string."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def log_system_info(logger):
    """
    Logs basic system and hardware information to the provided logger.
    """
    try:
        # Operating system details
        os_name = platform.system()
        os_version = platform.version()
        os_release = platform.release()
        machine = platform.machine()
        processor = platform.processor()
        
        # CPU and Memory
        cpu_count = psutil.cpu_count(logical=True)
        total_memory = psutil.virtual_memory().total // (1024 ** 2)  # Convert bytes to MB
        
        logger.info("========== System Information ==========")
        logger.info(f"Operating System: {os_name} {os_release} (Version: {os_version})")
        logger.info(f"Architecture: {machine}")
        logger.info(f"Processor: {processor}")
        logger.info(f"Logical CPUs: {cpu_count}")
        logger.info(f"Total Memory: {total_memory} MB")
        logger.info(f"Python Version: {platform.python_version()}")
        logger.info("========================================")
    except Exception as e:
        logger.error(f"Failed to log system information: {e}")

class _RotatingFileHandler(RotatingFileHandler):
    def doRollover(self):
        super().doRollover()
        # Include system info after rollover
        log_system_info(logging.getLogger("debug_logger"))

def setup_logging():
    # Log to program directory
    log_dir = "./Logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "ProjectBabble.log")

    # Set up logging
    logger = logging.getLogger("debug_logger")
    logger.setLevel(logging.DEBUG)

    file_handler = _RotatingFileHandler(log_file, mode='w', maxBytes=2000000, backupCount=1, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    # Redirect stdout and stderr
    class StreamToLogger:
        def __init__(self, stream, log_level):
            self.stream = stream
            self.log_level = log_level

        def write(self, message):
            if self.stream:
                message = strip_ansi_codes(message)
                if message.strip():
                    logger.log(self.log_level, message.strip())
                try:
                    self.stream.write(message)
                    self.stream.flush()
                except AttributeError:
                    pass

        def flush(self):
            if self.stream:
                try:
                    self.stream.flush()
                except AttributeError:
                    pass

    sys.stdout = StreamToLogger(sys.stdout, logging.INFO)
    sys.stderr = StreamToLogger(sys.stderr, logging.ERROR)

    log_system_info(logger)