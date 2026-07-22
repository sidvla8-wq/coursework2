import pytest
from unittest.mock import patch, MagicMock
from src.models import Aeroplane
from src.api import NominatimAPI, OpenSkyAPI, AeroplanesAPI
from src.storage import JSONSaver, StorageBase


class TestAeroplane:
    def test_valid_creation(self):
        a = Aeroplane(callsign="UAL1621", origin_country="United States", velocity=268.79, baro_altitude=10203.18)
        assert a.callsign == "UAL1621"
        assert a.origin_country == "United States"

    def test_invalid_velocity_raises(self):
        with pytest.raises(ValueError):  # <-- просто ValueError
            Aeroplane(callsign="X", origin_country="Y", velocity=-1, baro_altitude=100)

    def test_invalid_callsign_raises(self):
        with pytest.raises(ValueError):  # <-- просто ValueError
            Aeroplane(callsign="", origin_country="Y", velocity=100, baro_altitude=100)

    def test_from_opensky_state(self):
        state = {
            "callsign": "BAW123",
            "origin_country": "UK",
            "velocity": 250.0,
            "baro_altitude": 11000.0,
            "icao24": "A1B2C3",
            "latitude": 51.5,
            "longitude": -0.1,
            "time_position": 1700000000,
        }
        a = Aeroplane.from_opensky_state(state)
        assert a.callsign == "BAW123"
        assert a.velocity == 250.0

    def test_comparison_by_altitude_then_velocity(self):
        a1 = Aeroplane("A", "US", 200, 10000)
        a2 = Aeroplane("B", "CA", 300, 9000)
        # a1 выше, значит должен считаться «меньше» для сортировки по убыванию
        assert a1 < a2


class TestNominatimAPI:
    @patch("requests.Session.get")
    def test_get_country_bbox_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {"boundingbox": ["40.0", "50.0", "-120.0", "-110.0"]}
        ]
        mock_get.return_value = mock_resp

        api = NominatimAPI()
        bbox = api.get_country_bbox("USA")
        assert bbox == [40.0, 50.0, -120.0, -110.0]

    @patch("requests.Session.get")
    def test_get_country_bbox_not_found(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = []
        mock_get.return_value = mock_resp

        api = NominatimAPI()
        assert api.get_country_bbox("UnknownCountry") is None


class TestOpenSkyAPI:
    @patch("requests.Session.get")
    def test_get_aeroplanes_in_bbox(self, mock_get):
        # Пример «сырого» ответа OpenSky: список списков
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "states": [
                [
                    "icao1",
                    "BAW123",
                    "UK",
                    1700000000,
                    1700000001,
                    -0.1,
                    51.5,
                    11000,
                    False,
                    250,
                    0,
                    0,
                    [],
                    11100,
                    "7000",
                    False,
                    0,
                ]
            ]
        }
        mock_get.return_value = mock_resp

        api = OpenSkyAPI()
        planes = api.get_aeroplanes_in_bbox(40, 50, -120, -110)
        assert len(planes) == 1
        assert planes[0]["callsign"] == "BAW123"


class TestAeroplanesAPI:
    @patch.object(NominatimAPI, "get_country_bbox")
    @patch.object(OpenSkyAPI, "get_aeroplanes_in_bbox")
    def test_full_flow(self, mock_opensky, mock_nominatim):
        mock_nominatim.return_value = [40.0, 50.0, -120.0, -110.0]
        mock_opensky.return_value = [
            {
                "callsign": "BAW123",
                "origin_country": "UK",
                "velocity": 250.0,
                "baro_altitude": 11000.0,
                "icao24": "icao1",
                "latitude": 51.5,
                "longitude": -0.1,
                "time_position": 1700000000,
            }
        ]

        api = AeroplanesAPI()
        result = api.get_aeroplanes("UK")
        assert len(result) == 1
        assert result[0]["callsign"] == "BAW123"

    def test_country_not_found_raises_value_error(self):
        api = AeroplanesAPI()
        with patch.object(NominatimAPI, "get_country_bbox", return_value=None):
            with pytest.raises(ValueError):
                api.get_aeroplanes("NonExistentCountry")


class TestJSONSaver:
    @pytest.fixture
    def saver(self, tmp_path):
        path = tmp_path / "test_aircrafts.json"
        saver = JSONSaver(str(path))
        yield saver
        # опционально: можно удалить файл после теста, но pytest.tmp_path и так очистит

    def test_add_and_get_all(self, saver):
        p = Aeroplane("TEST1", "US", 100.0, 5000.0)
        saver.add_aeroplane(p)
        all_planes = saver.get_all()
        assert len(all_planes) == 1
        assert all_planes[0].callsign == "TEST1"

    def test_delete_aeroplane(self, saver):
        p1 = Aeroplane("TEST1", "US", 100.0, 5000.0)
        p2 = Aeroplane("TEST2", "CA", 120.0, 6000.0)
        saver.add_aeroplane(p1)
        saver.add_aeroplane(p2)

        deleted = saver.delete_aeroplane("TEST1")
        assert deleted is True
        remaining = saver.get_all()
        assert len(remaining) == 1
        assert remaining[0].callsign == "TEST2"

        deleted_again = saver.delete_aeroplane("TEST1")
        assert deleted_again is False

    def test_get_by_country(self, saver):
        saver.add_aeroplane(Aeroplane("US1", "United States", 100.0, 5000.0))
        saver.add_aeroplane(Aeroplane("CA1", "Canada", 110.0, 5500.0))
        us_planes = saver.get_by_country("United States")
        ca_planes = saver.get_by_country("Canada")
        assert len(us_planes) == 1 and us_planes[0].origin_country == "United States"
        assert len(ca_planes) == 1 and ca_planes[0].origin_country == "Canada"

    def test_load_empty_file_no_crash(self, tmp_path):
        path = tmp_path / "empty.json"
        path.write_text("")  # пустой файл
        saver = JSONSaver(str(path))
        assert isinstance(saver.get_all(), list)


# Заглушка для проверки, что абстрактный класс StorageBase требует реализации методов
def test_storage_base_requires_implementation():
    with pytest.raises(TypeError):

        class BadStorage(StorageBase):
            pass

        BadStorage()
