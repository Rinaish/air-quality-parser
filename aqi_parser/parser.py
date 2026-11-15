import time
import requests
import json
import logging
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from aqi_parser.db import get_stations
from aqi_parser.config import TOKEN, MSC_TZ, STATE_FILE, BBOX

logger = logging.getLogger(__name__)


def is_stations_stale(state_file=STATE_FILE, max_age_hours=24):
    """
    Indicate if last stations update was expired more than max_age_hours.
    """

    if state_file.exists():
        try:
            updated_at = json.loads(state_file.read_text()).get("updated_at")
        except (json.JSONDecodeError, OSError):
            return True

        if not updated_at:
            return True
        
        dt = datetime.fromisoformat(updated_at)
        dt_now = datetime.now(MSC_TZ)

        return (dt_now - dt).total_seconds() / 3600 >= max_age_hours

    else: return True


def is_measurements_stale(st_info, max_age_hours=12):
    meas_ts = st_info.get('time', {}).get('s')

    if meas_ts:
        meas_dt = datetime.fromisoformat(meas_ts).replace(tzinfo=MSC_TZ)
        diff_dt = datetime.now(MSC_TZ)- meas_dt

        return diff_dt.total_seconds() / 3600 >= max_age_hours


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(requests.RequestException),
    reraise=True
)
def fetch_by_bbox(bbox) -> dict:
    response = requests.get(f'https://api.waqi.info/map/bounds/?latlng={bbox}&networks=all&token={TOKEN}', timeout=20)
    response.raise_for_status()
    return response.json()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(requests.RequestException),
    reraise=True
)
def fetch_by_uid(uid) -> dict:
    response = requests.get(f'https://api.waqi.info/feed/@{uid}/?token={TOKEN}', timeout=20)
    response.raise_for_status()
    return response.json()


def fetch_stations():
    """
    Return initial list of active station within the border box.
    """

    try:
        payload = fetch_by_bbox(BBOX)
    
    except Exception as e:
        logger.error('Request error: %s', str(e))
        raise

    if payload.get('status') != 'ok':
        raise RuntimeError(f"waqi error: {payload.get('message')}")
    
    stations = payload.get('data')
    logger.info(f'Success, %d stations obtained', len(stations))

    return stations


def fetch_measurements(cursor, network) -> list[dict]:
    """
    Return detailed list of recent measurements made by each station.
    """

    st_data = get_stations(cursor, network)
    sts_info = []
    sts_stale = []

    for st in st_data:
        uid, name = st[0], st[1]
        try:
            payload = fetch_by_uid(uid)

        except Exception as e:
            logger.error('Request error for station %s: %s', name, str(e))    
            continue

        if payload.get('status') != 'ok':
            # logger.warning('No info for station: %s', name)
            continue

        st_info = payload.get('data', {})
        st_info.pop('forecast', None)

        if is_measurements_stale(st_info):
            sts_stale.append(st_info)

        sts_info.append(st_info)
        time.sleep(0.2)

    if sts_stale:
        logger.warning('No recent data for %s %s stations', len(sts_stale), network)

    return sts_info
