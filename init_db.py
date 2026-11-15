import sqlite3
from pathlib import Path
from aqi_parser.config import DB_NAME
from aqi_parser.db import coords_hash, save_stations
from aqi_parser.parser import fetch_stations

loc_state_file = Path('data/.stations_update.json')
loc_state_file.parent.mkdir(parents=True, exist_ok=True)
loc_state_file.touch(exist_ok=True)

loc_db_file = Path('data') / DB_NAME

conn = sqlite3.connect(loc_db_file)
cursor = conn.cursor()

cursor.execute('PRAGMA foreign_keys = ON')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS AirOfficial (
    id INTEGER PRIMARY KEY,
    station_id INTEGER,
    time TEXT,
    dominentpol TEXT,
    aqi INTEGER,
    pm25 REAL,
    pm10 REAL,
    no2 REAL,
    o3 REAL,
    co REAL,
    so2 REAL,
    temp REAL,
    hum REAL,
    press REAL,
    dew REAL,
    wind REAL,
    wind_gust REAL,
    UNIQUE (time, station_id),
    FOREIGN KEY (station_id) REFERENCES Station (id) ON DELETE CASCADE
    )
    ''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS AirCitizen (
    id INTEGER PRIMARY KEY,
    station_id INTEGER,
    time TEXT,
    dominentpol TEXT,
    aqi INTEGER,
    pm25 REAL,
    pm10 REAL,
    UNIQUE (time, station_id),
    FOREIGN KEY (station_id) REFERENCES Station (id) ON DELETE CASCADE
    )
    '''
)

cursor.execute('''
    CREATE TABLE IF NOT EXISTS Station (
    id INTEGER PRIMARY KEY,
    coord_key TEXT UNIQUE,
    uid INTEGER UNIQUE,
    name TEXT,
    lat REAL,
    lon REAL,
    network TEXT
    )
    ''')


st_data = fetch_stations()

st_rows = [
    (
        coords_hash((st['lat'],st['lon'])),
        st['uid'],
        st['station']['name'],
        st['lat'],
        st['lon'],
        'official' if st['uid'] > 0 else 'citizen'
    )
    for st in st_data
]

save_stations(cursor, loc_state_file, st_data)
conn.commit()
conn.close()