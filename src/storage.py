import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from src.models import Aeroplane


class StorageBase(ABC):
    @abstractmethod
    def add_aeroplane(self, plane: Aeroplane) -> None:
        pass

    @abstractmethod
    def delete_aeroplane(self, callsign: str) -> bool:
        pass

    @abstractmethod
    def get_all(self) -> List[Aeroplane]:
        pass

    @abstractmethod
    def get_by_country(self, country: str) -> List[Aeroplane]:
        pass


class JSONSaver(StorageBase):
    def __init__(self, filepath: str = "aircrafts.json"):
        self.filepath = filepath
        self._data: List[Dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    self._data = data
                else:
                    self._data = []
        except FileNotFoundError:
            self._data = []
        except json.JSONDecodeError:
            self._data = []

    def _save(self) -> None:
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def add_aeroplane(self, plane: Aeroplane) -> None:
        record = plane.to_dict()
        # Удаляем дубликаты по callsign
        self._data = [p for p in self._data if p.get("callsign") != plane.callsign]
        self._data.append(record)
        self._save()

    def delete_aeroplane(self, callsign: str) -> bool:
        initial_len = len(self._data)
        self._data = [p for p in self._data if p.get("callsign") != callsign]
        changed = len(self._data) != initial_len
        if changed:
            self._save()
        return changed

    def get_all(self) -> List[Aeroplane]:
        return [Aeroplane(**p) for p in self._data]

    def get_by_country(self, country: str) -> List[Aeroplane]:
        country_lower = country.lower()
        filtered = [
            p
            for p in self._data
            if (p.get("origin_country") or "").lower() == country_lower
        ]
        return [Aeroplane(**p) for p in filtered]
