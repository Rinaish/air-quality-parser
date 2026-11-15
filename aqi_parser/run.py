import sqlite3
import logging
from logger import setup_logger
from aqi_parser.parser import fetch_measurements, fetch_stations, is_stations_stale
from aqi_parser.db import save_measurement_official, save_measurement_citizen, save_stations
from aqi_parser.config import DB_PATH, STATE_FILE

logger = logging.getLogger('aqi_parser.run')

def run():
    setup_logger()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if is_stations_stale():
        sts = fetch_stations()
        save_stations(cursor, STATE_FILE, sts)

    off_measurements = fetch_measurements(cursor, 'official')
    cit_measurements = fetch_measurements(cursor, 'citizen')
    off_records = save_measurement_official(cursor, off_measurements)
    cit_records = save_measurement_citizen(cursor, cit_measurements)

    logger.info('Records obtained from %s official stations and %s citizen stations', off_records, cit_records)
    conn.commit()
    conn.close()


if __name__ == '__main__':
    run()