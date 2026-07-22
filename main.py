# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/

import sys
import os
from src.api import AeroplanesAPI
from src.models import Aeroplane
from src.storage import JSONSaver
from typing import List


def filter_aeroplanes_by_countries(planes: List[Aeroplane], countries: List[str]) -> List[Aeroplane]:
    """Фильтрует список самолётов по списку стран регистрации"""
    countries_lower = [c.lower() for c in countries]
    return [p for p in planes if (p.origin_country or "").lower() in countries_lower]


def get_aeroplanes_by_altitude(planes: List[Aeroplane], range_str: str) -> List[Aeroplane]:
    """
    Формат: "min-max", например "1000-15000".
    Если одно число — считаем это min.
    """
    parts = [p.strip() for p in range_str.split("-") if p.strip()]
    if len(parts) == 0:
        return planes
    if len(parts) == 1:
        min_alt = float(parts[0])
        max_alt = float("inf")
    else:
        min_alt = float(parts[0])
        max_alt = float(parts[1])

    result = []
    for p in planes:
        alt = p.baro_altitude
        if alt is None:
            continue
        if min_alt <= alt <= max_alt:
            result.append(p)
    return result


def sort_aeroplanes_by_altitude_velocity(planes: List[Aeroplane]) -> List[Aeroplane]:
    """Сортирует самолёты: сначала по высоте (убывание), затем по скорости (убывание)"""
    return sorted(planes, key=lambda p: (p.baro_altitude or 0, p.velocity), reverse=True)


def get_top_n(planes: List[Aeroplane], n: int) -> List[Aeroplane]:
    """Возвращает первые N самолётов из списка."""
    return planes[:n]


def print_aeroplanes(planes: List[Aeroplane]) -> None:
    """Выводит таблицу с данными о самолётах в привычном формате"""
    if not planes:
        print("Самолёты не найдены.")
        return
    print(f"{'Callsign':<15} {'Country':<20} {'Velocity (m/s)':<16} {'Altitude (m)':<14}")
    print("-" * 70)
    for p in planes:
        callsign = p.callsign[:14]
        country = (p.origin_country or "Unknown")[:19]
        vel = f"{p.velocity:.1f}"
        alt = f"{p.baro_altitude:.1f}" if p.baro_altitude is not None else "N/A"
        print(f"{callsign:<15} {country:<20} {vel:<16} {alt:<14}")


def user_interaction():
    """
        Основная функция взаимодействия с пользователем.
        Запрашивает страну, получает данные, сохраняет их и предлагает фильтры.
        """
    api = AeroplanesAPI()
    saver = JSONSaver("aircrafts.json")

    country = input("Введите название страны для запроса информации о самолётах: ").strip()
    if not country:
        print("Название страны не может быть пустым.")
        return

    try:
        raw_planes = api.get_aeroplanes(country)
    except Exception as e:
        print(f"Ошибка при получении данных: {e}")
        return

    planes = Aeroplane.cast_to_object_list(raw_planes)
    print(f"\nНайдено самолётов в воздушном пространстве {country}: {len(planes)}")

    # Сохраняем в JSON
    for p in planes:
        saver.add_aeroplane(p)
    print("Данные сохранены в aircrafts.json\n")

    # Топ N по высоте/скорости
    while True:
        n_str = input("Введите количество самолётов для вывода в топ N (или 0 для пропуска): ").strip()
        try:
            n = int(n_str)
            if n < 0:
                print("Число должно быть неотрицательным.")
                continue
            break
        except ValueError:
            print("Пожалуйста, введите целое число.")

    if n > 0:
        sorted_planes = sort_aeroplanes_by_altitude_velocity(planes)
        top_planes = get_top_n(sorted_planes, n)
        print(f"\nТоп-{n} самолётов по высоте и скорости:")
        print_aeroplanes(top_planes)

    # Фильтрация по стране регистрации
    filter_input = input("\nВведите названия стран для фильтрации по стране регистрации (через пробел, или оставьте пустым): ").strip()
    if filter_input:
        countries_filter = filter_input.split()
        filtered_planes = filter_aeroplanes_by_countries(planes, countries_filter)
        print(f"\nСамолёты, зарегистрированные в указанных странах ({', '.join(countries_filter)}):")
        print_aeroplanes(filtered_planes)

    # Фильтр по высоте
    alt_range = input("\nВведите диапазон высот полёта (формат min-max, например 1000-10000, или оставьте пустым): ").strip()
    if alt_range:
        ranged_planes = get_aeroplanes_by_altitude(planes, alt_range)
        print(f"\nСамолёты в диапазоне высот {alt_range}:")
        print_aeroplanes(ranged_planes)


if __name__ == "__main__":
    user_interaction()
