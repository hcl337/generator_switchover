import os
import sys
import logging
from logging.handlers import RotatingFileHandler

#if __name__ == "__main__":
logger = logging.getLogger("generator")
logger.setLevel("DEBUG")
formatter = logging.Formatter(
        fmt='%(asctime)s %(module)s,line: %(lineno)d %(levelname)8s | %(message)s',
        datefmt='%Y/%m/%d %H:%M:%S') # %I:%M:%S %p AM|PM format

if not os.path.exists('./logs/'):
    os.makedirs('./logs/')

# File logger 10M max
logger_fh = RotatingFileHandler('./logs/generator.log', mode='a', maxBytes=10*1024*1024, 
                                 backupCount=2, encoding=None, delay=0)
logger_fh.setFormatter(formatter)
logger_fh.setLevel(logging.INFO)
logger.addHandler(logger_fh)

# Console Logger for everything
logger_sh = logging.StreamHandler(stream=sys.stdout)
logger_sh.setFormatter(formatter)
logger_sh.setLevel(logging.DEBUG)
logger.addHandler(logger_sh)

logger.info("Set up all loggers")
print("asdf")

