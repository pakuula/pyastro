"""Модуль для работы с Дата, время и географическое положение."""

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Dict, Optional, Type
from zoneinfo import ZoneInfo

import swisseph as swe

from pyastro.util.angle import parse_lat, parse_lon
from pyastro.util.parse_time import datetime_from_dict

from .houses import HousePosition, HouseSystem
from .planet import NEW_PLANETS_WITH_NODES, Planet, PlanetPosition


def value_from_dict[T](
    data: dict,
    key: str,
    expected_types: Dict[Type, Callable],
    default: Optional[T] = None,
) -> T:
    """Извлекает значение из словаря и преобразует его в один из ожидаемый тип.

    :param data: Словарь для извлечения значения.
    :param key: Ключ для извлечения значения.
    :param expected_types: Словарь типов и функций преобразования.
    :param default: Значение по умолчанию, если ключ отсутствует.
    :raises ValueError: Если ключ отсутствует и значение по умолчанию не задано.
    :raises TypeError: Если тип значения не соответствует ожидаемым типам.
    :return: Преобразованное значение.

    Пример использования:
    ```python
    longitude = value_from_dict(
            data, "longitude", {int: float, float: float, str: parse_lon}
        )
    elevation = value_from_dict(
            data, "elevation", {int: float, float: float}, default=0.0
        )
    ```
    """
    if key not in data:
        if default is not None:
            return default
        raise ValueError(f"JSON должен содержать поле '{key}'")
    value = data[key]
    for expected_type, converter in expected_types.items():
        if isinstance(value, expected_type):
            return converter(value)
    expected_type_names = ", ".join([t.__name__ for t in expected_types.keys()])
    raise TypeError(
        f"Invalid type for '{key}': expected one of ({expected_type_names}), got {type(value)}"
    )


@dataclass
class GeoPosition:
    """Географическое положение на поверхности Земли."""

    latitude: float  # градусы, позитивное значение означает северное полушарие
    longitude: float  # градусы, позитивное значение означает восточное полушарие
    elevation: float = 0.0  # высота над уровнем моря в метрах
    place: str = ""  # название места

    @staticmethod
    def from_dict(data: dict) -> "GeoPosition":
        """Создает GeoPosition из JSON-объекта."""

        latitude: float = value_from_dict(
            data, "latitude", {int: float, float: float, str: parse_lat}
        )
        longitude: float = value_from_dict(
            data,
            "longitude",
            {int: float, float: float, str: parse_lon},
        )
        # if "latitude" not in data or "longitude" not in data:
        #     raise ValueError("GeoPosition requires 'latitude' and 'longitude' fields")
        # if isinstance(data["latitude"], (int, float)):
        #     latitude = float(data["latitude"])
        # elif isinstance(data["latitude"], str):
        #     latitude = parse_lat(data["latitude"])
        # else:
        #     raise ValueError(
        #         f"Invalid type for 'latitude': expected str or float, got {type(data['latitude'])}"
        #     )
        # if isinstance(data["longitude"], (int, float)):
        #     longitude = float(data["longitude"])
        # elif isinstance(data["longitude"], str):
        #     longitude = parse_lon(data["longitude"])
        # else:
        #     raise ValueError(
        #         f"Invalid type for 'longitude': expected str or float, got {type(data['longitude'])}"
        #     )
        data["latitude"] = latitude
        data["longitude"] = longitude
        # if "elevation" in data:
        #     if not isinstance(data["elevation"], (int, float)):
        #         raise ValueError(
        #             f"Invalid type for 'elevation': expected float, got {type(data['elevation'])}"
        #         )
        #     elevation = float(data["elevation"])
        # else:
        #     elevation = 0.0
        elevation: float = value_from_dict(
            data, "elevation", {int: float, float: float}, default=0.0
        )
        if "elevation" in data:
            data["elevation"] = elevation
        place: str = value_from_dict(data, "place", {str: str}, default="")
        if "place" in data:
            data["place"] = place
        # if "place" in data:
        #     if not isinstance(data["place"], str):
        #         raise ValueError(
        #             f"Invalid type for 'place': expected str, got {type(data['place'])}"
        #         )
        #     place = data["place"]
        # else:
        #     place = ""
        return GeoPosition(
            latitude=latitude,
            longitude=longitude,
            elevation=elevation,
            place=place,
        )


@dataclass
class DatetimeLocation:
    """Дата, время и географическое положение.

    Дополнительно можно указать, что метка времени приблизительна, и непригодна для вычисления домов.
    """

    datetime: datetime
    location: GeoPosition
    date_only: bool = (
        False  # если True, время приблизительное, используется только дата
    )

    def to_julian_day(self) -> float:
        """Преобразует дату и время в юлианскую дату."""
        utc_datetime = self.datetime.astimezone(ZoneInfo("UTC"))  # Convert to UTC
        return swe.julday(  # pylint: disable=c-extension-no-member
            utc_datetime.year,
            utc_datetime.month,
            utc_datetime.day,
            utc_datetime.hour + utc_datetime.minute / 60 + utc_datetime.second / 3600,
        )

    def get_planet_position(self, planet: Planet) -> PlanetPosition:
        """Возвращает позицию планеты в виде (долгота, широта, расстояние от Земли)."""
        jd = self.to_julian_day()
        swe_data, _ = swe.calc_ut(jd, planet.code)

        return PlanetPosition.from_swe_data(planet, swe_data)

    def get_all_planet_positions(
        self, planets: Optional[tuple[Planet, ...]] = None
    ) -> list[PlanetPosition]:
        """Возвращает позиции всех планет."""
        if planets is None:
            planets = NEW_PLANETS_WITH_NODES
        return [self.get_planet_position(planet) for planet in planets]

    def get_house_cusps(
        self, house_system: HouseSystem = HouseSystem.PLACIDUS
    ) -> list[HousePosition]:
        """Возвращает позиции куспидов домов."""
        if self.date_only:
            raise ValueError("Невозможно вычислить дома, если date_only=True")
        jd = self.to_julian_day()
        lat = self.location.latitude
        lon = self.location.longitude
        cusps, _ = swe.houses(  # pylint: disable=c-extension-no-member
            jd, lat, lon, house_system.value
        )

        house_cusps = []
        for i in range(12):
            next_cusp = cusps[(i + 1) % 12]
            house_cusps.append(HousePosition.from_swe_data(i + 1, cusps[i], next_cusp))

        return house_cusps

    @staticmethod
    def from_dict(data: dict) -> "DatetimeLocation":
        """Создает DatetimeLocation из JSON-объекта."""

        if not "datetime" in data:
            raise ValueError("JSON должен содержать поле 'datetime'")
        dt = datetime_from_dict(data["datetime"])
        if not "location" in data:
            raise ValueError("JSON должен содержать поле 'location'")
        loc = GeoPosition.from_dict(data["location"])
        if "date_only" in data:
            if not isinstance(data["date_only"], bool):
                raise ValueError(
                    f"Invalid type for 'date_only': expected bool, got {type(data['date_only'])}"
                )
            date_only = data["date_only"]
        else:
            date_only = False

        return DatetimeLocation(datetime=dt, location=loc, date_only=date_only)
