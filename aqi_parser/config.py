import os
from dotenv import load_dotenv
from datetime import timezone, timedelta
from pathlib import Path
load_dotenv()

BBOX = '55.57,37.35,55.92,37.85'
MSC_TZ = timezone(timedelta(hours=3))
TOKEN = os.environ['TOKEN_AQICN']
DB_NAME = os.environ['DB_NAME']
DB_PATH = Path('/app/data') / DB_NAME
STATE_FILE = Path('/app/data/.stations_update.json')