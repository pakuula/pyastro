#!/usr/bin/env python3
import argparse
from dataclasses import dataclass
import datetime
from enum import Enum

from pyastro.astro import Chart, DatetimeLocation, Planet, GeoPosition

# Скрипт для вычисления парада планет. Он перебирает даты и выводит те, когда как минимум <n> планет (n - параметр)
# находятся в пределах сектора размером 20-30 градусов.
# Можно указать дату начала и дату конца, а также широту и долготу места наблюдения.
# Пример запуска:
# python -m pyastro.scripts.planet_parade --start 2023-01-01 --end 2025-12-31 --min-planets 5 --lat 55.75 --lon 37.62

planet_list = [
    Planet.SUN,
    Planet.MOON,
    Planet.MERCURY,
    Planet.VENUS,
    Planet.MARS,
    Planet.JUPITER,
    Planet.SATURN,
    Planet.URANUS,
    Planet.NEPTUNE,
    Planet.PLUTO,
]


def main():
    parser = argparse.ArgumentParser(description="Нахождение парадов планет.")
    parser.add_argument(
        "-s", "--start", type=str, required=True, help="Дата начала (YYYY-MM-DD)."
    )
    parser.add_argument(
        "-e", "--end", type=str, required=True, help="Дата конца (YYYY-MM-DD)."
    )
    parser.add_argument(
        "-p",
        "--min-planets",
        type=int,
        required=True,
        help="Минимальное количество планет.",
    )
    parser.add_argument(
        "-a",
        "--angle",
        type=float,
        default=30.0,
        help="Угол сектора (по умолчанию 30 градусов).",
    )
    parser.add_argument(
        "--lat",
        type=float,
        default=55.755814,
        help="Широта места наблюдения (по умолчанию 55.755814, Москва).",
    )
    parser.add_argument(
        "--lon",
        type=float,
        default=37.617707,
        help="Долгота места наблюдения (по умолчанию 37.617707, Москва).",
    )
    args = parser.parse_args()

    start_date = datetime.datetime.strptime(args.start, "%Y-%m-%d").date()
    end_date = datetime.datetime.strptime(args.end, "%Y-%m-%d").date()
    min_planets = args.min_planets
    angle = args.angle
    latitude = args.lat
    longitude = args.lon

    parades = list(find_planet_parades(
        start_date=start_date,
        end_date=end_date,
        min_planets=min_planets,
        angle=angle,
        latitude=latitude,
        longitude=longitude,
    ))
    parade_ranges = group_by_parade(parades)
    if parade_ranges:
        print(f"Найдено {len(parade_ranges)} парадов планет:")
        for parade_range in parade_ranges:
            planets_str = " ".join([p.symbol for p in parade_range.planets])
            if parade_range.start_date == parade_range.end_date:
                print(
                    f"{planets_str} : {parade_range.start_date} ({len(parade_range.planets)} планет)"
                )
            else:
                print(
                    f"{planets_str} : {parade_range.start_date} - {parade_range.end_date} ({len(parade_range.planets)} планет)"
                )


class Sector(Enum):
    FORWARD = 1
    BACKWARD = -1
    NONE = 0


@dataclass
class PlanetSector:
    planet: Planet
    center: float
    size: float = 30.0
    # Планеты в секторе +30 градусов
    fwd_planets: list[Planet] = None
    # Планеты в секторе -30 градусов
    back_planets: list[Planet] = None

    def __post_init__(self):
        self.fwd_planets = []
        self.back_planets = []

    def add_planet(self, other: Planet, angle: float):
        if 0 <= angle <= self.size:
            self.fwd_planets.append(other)
        elif -self.size <= angle < 0:
            self.back_planets.append(other)

    def has_parade(self, min_planets: int) -> Sector:
        if self.total_fwd >= min_planets:
            return Sector.FORWARD
        elif self.total_back >= min_planets:
            return Sector.BACKWARD
        else:
            return Sector.NONE

    def parade_planets(self) -> list[tuple[Planet]]:
        result = []
        if self.total_fwd >= self.total_back:
            result.append(tuple(sorted([self.planet] + self.fwd_planets)))
        else:
            result.append(tuple(sorted([self.planet] + self.back_planets)))
        return result

    @property
    def total_fwd(self) -> int:
        return 1 + len(self.fwd_planets)

    @property
    def total_back(self) -> int:
        return 1 + len(self.back_planets)


@dataclass
class ParadeEvent:
    planets: tuple[Planet]
    date: datetime.date

@dataclass
class ParadeRange:
    planets: tuple[Planet]
    start_date: datetime.date
    end_date: datetime.date = None
    
    def __post_init__(self):
        if self.end_date is None:
            self.end_date = self.start_date

    def is_next_day(self, date: datetime.date) -> bool:
        return self.end_date + datetime.timedelta(days=1) == date


def find_planet_parades(
    start_date: datetime.date,
    end_date: datetime.date,
    min_planets: int,
    angle: float,
    latitude: float,
    longitude: float,
):
    current_date = start_date
    delta = datetime.timedelta(days=1)

    while current_date <= end_date:
        dt_loc = DatetimeLocation(
            datetime=datetime.datetime.combine(current_date, datetime.time(12, 0)),
            location=GeoPosition(latitude=latitude, longitude=longitude),
            date_only=True,
        )
        chart = Chart(name="Planet Parade", dt_loc=dt_loc)
        parades: set[tuple[Planet]] = set()
        for planet in planet_list:
            planet_longitude = chart.planet_position(planet).longitude
            sector = PlanetSector(
                planet=planet, center=planet_longitude, size=angle
            )
            for other_planet in planet_list:
                if other_planet == planet:
                    continue
                sector.add_planet(
                    other=other_planet,
                    angle=chart.planet_position(other_planet).longitude
                    - planet_longitude,
                )
            if sector.has_parade(min_planets) != Sector.NONE:
                parades.update(sector.parade_planets())
        if parades:
            for parade in parades:
                yield ParadeEvent(date=current_date, planets=parade)
        current_date += delta

def group_by_parade(parades: list[ParadeEvent]) -> list[ParadeRange]:
    current_parades = {}
    parade_ranges: list[ParadeRange] = []
    for event in parades:
        if event.planets in current_parades:
            parade_range = current_parades[event.planets]
            if parade_range.is_next_day(event.date):
                parade_range.end_date = event.date
            else:
                parade_ranges.append(parade_range)
                current_parades[event.planets] = ParadeRange(
                    planets=event.planets, start_date=event.date
                )
        else:
            current_parades[event.planets] = ParadeRange(
                planets=event.planets, start_date=event.date
            )
    parade_ranges.extend(current_parades.values())
    return parade_ranges

if __name__ == "__main__":
    print("Нахождение парадов планет.")
    main()
