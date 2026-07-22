from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class Aeroplane:
    callsign: str
    origin_country: str
    velocity: float
    baro_altitude: Optional[float]
    icao24: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    time_position: Optional[int] = None

    def __post_init__(self):
        self.callsign = self._validate_callsign(self.callsign)
        self.origin_country = self._validate_origin_country(self.origin_country)
        self.velocity = self._validate_velocity(self.velocity)
        if self.baro_altitude is not None:
            self.baro_altitude = self._validate_altitude(self.baro_altitude)

    @staticmethod
    def _validate_callsign(value: str) -> str:
        """Проверяет, что callsign — непустая строка."""
        if not value or not isinstance(value, str):
            raise ValueError("Callsign должен быть непустой строкой.")
        return value.strip()

    @staticmethod
    def _validate_origin_country(value: str) -> str:
        """Проверяет, что страна — непустая строка."""
        if not value or not isinstance(value, str):
            raise ValueError("Страна регистрации должна быть непустой строкой.")
        return value.strip()

    @staticmethod
    def _validate_velocity(value: float) -> float:
        """Проверяет, что скорость — неотрицательное число."""
        if value is None or not isinstance(value, (int, float)):
            raise ValueError("Скорость должна быть числом.")
        if value < 0:
            raise ValueError("Скорость не может быть отрицательной.")
        return float(value)

    @staticmethod
    def _validate_altitude(value: float) -> float:
        """Проверяет, что высота — неотрицательное число."""
        if value is None or not isinstance(value, (int, float)):
            raise ValueError("Высота должна быть числом.")
        if value < 0:
            raise ValueError("Высота не может быть отрицательной.")
        return float(value)

    @classmethod
    def from_opensky_state(cls, state: dict) -> "Aeroplane":
        """Создаёт объект Aeroplane из словаря состояния OpenSky."""
        return cls(
            callsign=state.get("callsign") or "UNKNOWN",
            origin_country=state.get("origin_country") or "Unknown",
            velocity=state.get("velocity") or 0.0,
            baro_altitude=state.get("baro_altitude"),
            icao24=state.get("icao24"),
            latitude=state.get("latitude"),
            longitude=state.get("longitude"),
            time_position=state.get("time_position"),
        )

    @classmethod
    def cast_to_object_list(cls, raw_list: List[dict]) -> List["Aeroplane"]:
        """Преобразует список словарей (от OpenSky) в список объектов Aeroplane, пропуская некорректные записи."""
        result = []
        for s in raw_list:
            try:
                result.append(cls.from_opensky_state(s))
            except ValueError:
                # Пропускаем некорректные записи, чтобы не ломать весь список
                continue
        return result

    # Методы сравнения по высоте и скорости
    def __lt__(self, other: "Aeroplane") -> bool:
        """Сравнивает два самолёта: сначала по высоте (убывание), затем по скорости (убывание)."""
        h1 = self.baro_altitude if self.baro_altitude is not None else 0
        h2 = other.baro_altitude if other.baro_altitude is not None else 0

        if h1 != h2:
            return h1 > h2  # большая высота считается «меньше» для сортировки по убыванию
        return self.velocity > other.velocity  # при равной высоте — большая скорость «меньше»