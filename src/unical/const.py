
from pathlib import Path
import os

STORE_DB = True
DB_FILE = "data.db"

DECIMALS = 2
SAMPLETIME = 30  # seconds

CONFIG_DIR = 'config'

UNICAL_PATH = Path(__file__).parent.parent  # directory del package
CONFIG_ABS_PATH = os.path.join(UNICAL_PATH, CONFIG_DIR)