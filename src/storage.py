import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from src.models import Aeroplane


class StorageBase(ABC):
    """Абстрактный базовый класс для работы с хранилищем данных."""
    @abstractmethod
    def add_aeroplane(self, plane: Aeroplane) -> None:
        """Добавляет самолёт в хранилище."""
        pass

    @abstractmethod
    def delete_aeroplane(self, callsign: str) -> bool:
        pass

    @abstractmethod
    def get_all(self) -> List[Aeroplane]:
        """Возвращает все сохранённые самолёты."""
        pass

    @abstractmethod
    def get_by_country(self, country: str) -> List[Aeroplane]:
        """Возвращает самолёты, зарегистрированные в указанной стране."""
        pass


class JSONSaver(StorageBase):
    """Реализация хранилища на основе JSON-файла."""
    def __init__(self, filepath: str = "aircrafts.json"):
        """Инициализирует хранилище и создаёт пустой файл, если его нет"""
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
        """Добавляет самолёт в JSON-файл."""
        planes = self.get_all()
        planes.append(plane)
        # Используем __dict__ вместо to_dict — это работает для dataclass по умолчанию
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump([p.__dict__ for p in planes], f, indent=2, ensure_ascii=False)

    def delete_aeroplane(self, callsign: str) -> bool:
        """Удаляет самолёт из JSON-файла по callsign"""
        initial_len = len(self._data)
        self._data = [p for p in self._data if p.get("callsign") != callsign]
        changed = len(self._data) != initial_len
        if changed:
            self._save()
        return changed

    def get_all(self) -> List[Aeroplane]:
        """Читает все самолёты из JSON-файла и возвращает список объектов Aeroplane."""
        return [Aeroplane(**p) for p in self._data]

    def get_by_country(self, country: str) -> List[Aeroplane]:
        """
                Возвращает список самолётов, зарегистрированных в указанной стране.
                Сравнение идёт без учёта регистра
                """
        country_lower = country.lower()
        filtered = [
            p
            for p in self._data
            if (p.get("origin_country") or "").lower() == country_lower
        ]
        return [Aeroplane(**p) for p in filtered]
