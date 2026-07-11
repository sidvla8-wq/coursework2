from dataclasses import dataclass
from typing import Optional


@dataclass
class Aeroplane:
    callsign: str
    origin_country: str
    velocity: float  # скорость, м/с
    baro_altitude: Optional[float]  # высота, м
    icao24: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    time_position: Optional[int] = None  # Unix timestamp

    def __post_init__(self):
        # Валидация
        if not self.callsign or not isinstance(self.callsign, str):
            raise ValueError("Callsign должен быть непустой строкой.")
        if not self.origin_country or not isinstance(self.origin_country, str):
            raise ValueError("Страна регистрации должна быть непустой строкой.")
        if self.velocity is None or self.velocity < 0:
            raise ValueError("Скорость должна быть неотрицательным числом.")
        if self.baro_altitude is not None and self.baro_altitude < 0:
            raise ValueError("Высота не может быть отрицательной.")

    @classmethod
    def from_opensky_state(cls, state: dict) -> "Aeroplane":
        return cls(
            callsign=state["callsign"] or "UNKNOWN",
            origin_country=state["origin_country"] or "Unknown",
            velocity=state["velocity"] or 0.0,
            baro_altitude=state["baro_altitude"],
            icao24=state["icao24"],
            latitude=state["latitude"],
            longitude=state["longitude"],
            time_position=state["time_position"],
        )

    @classmethod
    def cast_to_object_list(cls, states: list) -> list["Aeroplane"]:
        result = []
        for s in states:
            try:
                result.append(cls.from_opensky_state(s))
            except ValueError:
                # Пропускаем некорректные записи, чтобы не ломать весь список
                continue
        return result

    # Методы сравнения по скорости и высоте
    def __lt__(self, other: "Aeroplane") -> bool:
        # Сначала по высоте (если есть), потом по скорости
        h1 = self.baro_altitude if self.baro_altitude is not None else 0
        h2 = other.baro_altitude if other.baro_altitude is not None else 0
        if h1 != h2:
            return h1 < h2
        return self.velocity < other.velocity

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Aeroplane):
            return NotImplemented
        return (
            self.icao24 == other.icao24
            and self.callsign == other.callsign
            and self.origin_country == other.origin_country
        )

    def to_dict(self) -> dict:
        return {
            "callsign": self.callsign,
            "origin_country": self.origin_country,
            "velocity": self.velocity,
            "baro_altitude": self.baro_altitude,
            "icao24": self.icao24,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "time_position": self.time_position,
        }
