import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, Mock
from aqi_parser.parser import is_measurements_stale, is_stations_stale, fetch_measurements
from aqi_parser.config import MSC_TZ

@pytest.fixture
def mock_cursor():
    cursor = Mock()
    cursor.fetchall.return_value = [(12345, 'station_name', 'official')]
    return cursor


@pytest.fixture
def mock_requesting_uid():
    with patch('aqi_parser.parser.fetch_by_uid') as mock_func:
        mock_func.return_value = {
        "status": "error",
        "data": "Invalid key"
        }
        yield mock_func


def test_fetch_measurement(mock_requesting_uid, mock_cursor):
    result = fetch_measurements(mock_cursor, 'official')
    assert len(result) == 0
    mock_requesting_uid.assert_called_once()


def test_is_measurement_stale():
    st_info_stale = {
        "time": 
        {
            "s": f"{datetime.now(MSC_TZ) - timedelta(hours=12)}"
         }
    }
    assert is_measurements_stale(st_info_stale)

    st_info_fresh = {
            "time": 
            {
                "s": f"{datetime.now(MSC_TZ) - timedelta(hours=5)}"
             }
        }
    assert not is_measurements_stale(st_info_fresh)


def test_stations_update_is_empty(tmp_path):
    f = tmp_path / "state.json"
    assert is_stations_stale(state_file=f)

    f.write_text(json.dumps({"updated_at": None}, ensure_ascii=False), encoding='utf-8')
    assert is_stations_stale(state_file=f)


def test_stations_update_is_stale(tmp_path):
    upd_date = datetime.now(MSC_TZ) - timedelta(hours=24)
    f = tmp_path / "state.json"
    f.write_text(json.dumps({"updated_at": upd_date.isoformat()}, ensure_ascii=False), encoding='utf-8')
    assert is_stations_stale(state_file=f)