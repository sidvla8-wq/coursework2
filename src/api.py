import requests
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseAPI(ABC):
    @abstractmethod
    def get_data(self, *args, **kwargs) -> Any:
        """Единый интерфейс для получения данных из API."""
        pass


class NominatimAPI(BaseAPI):
    BASE_URL = "https://nominatim.openstreetmap.org/search"

    def __init__(self):
        self.session = requests.Session()
        # OpenStreetMap требует корректный User-Agent
        self.session.headers.update({"User-Agent": "Coursework-Aircraft-Tracker/1.0"})

    def get_country_bbox(self, country_name: str) -> Optional[List[float]]:
        """Вспомогательный метод для получения boundingbox."""
        params = {
            "q": country_name,
            "format": "json",
            "limit": 1,
        }
        resp = self.session.get(self.BASE_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if not data:
            return None

        place = data[0]
        bbox_str = place.get("boundingbox")
        if not bbox_str:
            return None

        south, north, west, east = map(float, bbox_str)
        return [south, north, west, east]

    # РЕАЛИЗАЦИЯ АБСТРАКТНОГО МЕТОДА
    def get_data(self, country_name: str, **kwargs) -> Optional[List[float]]:
        return self.get_country_bbox(country_name)


class OpenSkyAPI(BaseAPI):
    BASE_URL = "https://opensky-network.org/api/states/all"

    def __init__(self):
        self.session = requests.Session()

    def get_aeroplanes_in_bbox(
        self, south: float, north: float, west: float, east: float
    ) -> List[Dict[str, Any]]:
        """Вспомогательный метод для получения самолётов в прямоугольнике."""
        params = {
            "lamin": south,
            "lamax": north,
            "lomin": west,
            "lomax": east,
        }
        resp = self.session.get(self.BASE_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        states = data.get("states", [])
        if not states:
            return []

        mapped = []
        for s in states:
            mapped.append(
                {
                    "icao24": s[0],
                    "callsign": s[1],
                    "origin_country": s[2],
                    "time_position": s[3],
                    "last_contact": s[4],
                    "longitude": s[5],
                    "latitude": s[6],
                    "baro_altitude": s[7],
                    "on_ground": s[8],
                    "velocity": s[9],
                    "true_track": s[10],
                    "vertical_rate": s[11],
                    "sensors": s[12],
                    "geo_altitude": s[13],
                    "squawk": s[14],
                    "spi": s[15],
                    "position_source": s[16],
                }
            )
        return mapped

    # РЕАЛИЗАЦИЯ АБСТРАКТНОГО МЕТОДА
    def get_data(
        self, south: float, north: float, west: float, east: float, **kwargs
    ) -> List[Dict[str, Any]]:
        return self.get_aeroplanes_in_bbox(south, north, west, east)


class AeroplanesAPI:
    """Фасад для работы с двумя API: Nominatim + OpenSky."""

    def __init__(self):
        self.nominatim = NominatimAPI()
        self.opensky = OpenSkyAPI()

    def get_aeroplanes(self, country_name: str) -> List[Dict[str, Any]]:
        # Используем абстрактный интерфейс get_data
        bbox = self.nominatim.get_data(country_name)

        if bbox is None:
            raise ValueError(f"Страна '{country_name}' не найдена в Nominatim.")

        south, north, west, east = bbox
        # Используем абстрактный интерфейс get_data
        return self.opensky.get_data(south, north, west, east)
