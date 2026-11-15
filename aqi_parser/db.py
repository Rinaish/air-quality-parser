import hashlib
import sqlite3
import logging
import json
from datetime import datetime
from aqi_parser.config import MSC_TZ

logger = logging.getLogger(__name__)

def coords_hash(coords: tuple[float, float]):
    """
    Args:
        coords: list or tuple - lat, lon
    """
    key = f'{coords[0]:.3f}|{coords[1]:.3f}'
    hash = hashlib.md5(key.encode('utf-8')).hexdigest()
    return hash


def parse_value(value):
    if value in ("-", ""):
        return None
    return value


def round_time(m):
        dt = datetime.fromisoformat(m['time']['s'])
        return dt.strftime('%Y-%m-%d %H:00:00')


def save_stations(cursor, update_file, stations: list[dict]):
    st_rows = [
        (
            coords_hash((st['lat'],st['lon'])),
            st['uid'],
            st['station']['name'],
            st['lat'],
            st['lon'],
            'official' if st['uid'] > 0 else 'citizen'
        )
        for st in stations
    ]

    cursor.executemany('INSERT OR IGNORE INTO Station (coord_key, uid, name, lat, lon, network) VALUES (?, ?, ?, ?, ?, ?)', st_rows)
    logger.info('Stations saved: %s', cursor.rowcount)

    dt_now = datetime.now(MSC_TZ)
    update_file.write_text(json.dumps({"updated_at": dt_now.isoformat()}, ensure_ascii=False), encoding='utf-8')


def save_measurement_official(cursor, measurements: list[dict]):
    cursor.execute("SELECT coord_key, id FROM Station WHERE network = 'official'")
    sts_map = dict(cursor.fetchall())

    def get(m, k):
        return m['iaqi'].get(k, {}).get('v')

    rows = [
        (
            sts_map[coords_hash(m['city']['geo'])],
            m['time']['s'],
            parse_value(m['dominentpol']),
            parse_value(m['aqi']),
            get(m, 'pm25'), get(m, 'pm10'), get(m, 'no2'), get(m, 'o3'), get(m, 'co'), get(m, 'so2'),
            get(m, 't'), get(m, 'h'), get(m, 'p'), get(m, 'dew'), get(m, 'w'), get(m, 'wg')
        )
        for m in measurements
    ]

    cursor.executemany('INSERT OR IGNORE INTO AirOfficial' 
                        '(station_id, time, dominentpol, aqi, pm25, pm10, no2, o3, co, so2, temp, hum, press, dew, wind, wind_gust)'
                        'VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', rows)
    
    return cursor.rowcount


def save_measurement_citizen(cursor, measurements: list[dict]):
    cursor.execute("SELECT coord_key, id FROM Station WHERE network = 'citizen'")
    sts_map = dict(cursor.fetchall())

    rows = [
        (   
            sts_map[coords_hash(m['city']['geo'])],
            round_time(m),
            parse_value(m['dominentpol']),
            parse_value(m['aqi']),
            m.get('iaqi', {}).get('pm25', {}).get('v'),
            m.get('iaqi', {}).get('pm10', {}).get('v')
        )
        for m in measurements
    ]

    cursor.executemany('INSERT OR IGNORE INTO AirCitizen' 
                        '(station_id, time, dominentpol, aqi, pm25, pm10)'
                        'VALUES(?, ?, ?, ?, ?, ?)', rows)

    return cursor.rowcount


def get_stations(cursor, network):
    if network == 'official':
        cursor.execute("SELECT uid, name FROM Station WHERE network = 'official'")
        sts = cursor.fetchall()
        return sts
    
    elif network == 'citizen':
        cursor.execute("SELECT uid, name FROM Station WHERE network = 'citizen'")
        sts = cursor.fetchall()
        return sts
