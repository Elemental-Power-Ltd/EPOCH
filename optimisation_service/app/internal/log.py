import datetime
import logging
import os
import sys

os.makedirs("./logs", exist_ok=True)


formatter_file = logging.Formatter("[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
formatter_stream = logging.Formatter("[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
handler_file = logging.FileHandler(f"./logs/{datetime.datetime.now(datetime.UTC).strftime("%Y_%m_%d_%H_%M_%S")}.log")
handler_stream = logging.StreamHandler(sys.stdout)
handler_file.setFormatter(formatter_file)
handler_stream.setFormatter(formatter_stream)

logger = logging.getLogger("default")
logger.setLevel(logging.DEBUG)
logger.addHandler(handler_file)
logger.addHandler(handler_stream)
