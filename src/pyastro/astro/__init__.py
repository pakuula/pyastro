from itertools import combinations
import os.path
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Self
from zoneinfo import ZoneInfo

import swisseph as swe

from pyastro.util.angle import parse_lat, parse_lon

swe.set_ephe_path(
    os.path.dirname(__file__)
)  # Set the path to Swiss Ephemeris data files


@dataclass
class GeoPosition:
    """Географическое положение на поверхности Земли."""

    latitude: float  # градусы, позитивное значение означает северное полушарие
    longitude: float  # градусы, позитивное значение означает восточное полушарие
    elevation: float = 0.0  # высота над уровнем моря в метрах

    @staticmethod
    def from_json(data: dict) -> Self:
        """Создает GeoPosition из JSON-объекта."""
        if "latitude" not in data or "longitude" not in data:
            raise ValueError("GeoPosition requires 'latitude' and 'longitude' fields")
        if isinstance(data["latitude"], (int, float)):
            latitude = float(data["latitude"])
        elif isinstance(data["latitude"], str):
            latitude = parse_lat(data["latitude"])
        else:
            raise ValueError(
                f"Invalid type for 'latitude': expected str or float, got {type(data['latitude'])}"
            )
        if isinstance(data["longitude"], (int, float)):
            longitude = float(data["longitude"])
        elif isinstance(data["longitude"], str):
            longitude = parse_lon(data["longitude"])
        else:
            raise ValueError(
                f"Invalid type for 'longitude': expected str or float, got {type(data['longitude'])}"
            )
        data["latitude"] = latitude
        data["longitude"] = longitude
        if "elevation" in data:
            if not isinstance(data["elevation"], (int, float)):
                raise ValueError(
                    f"Invalid type for 'elevation': expected float, got {type(data['elevation'])}"
                )
            elevation = float(data["elevation"])
        else:
            elevation = 0.0
        return GeoPosition(
            latitude=latitude,
            longitude=longitude,
            elevation=elevation,
        )

class Planet(Enum):
    """Идентификаторы планет, используются в Swiss Ephemeris."""

    SUN = (0, "☉")
    MOON = (1, "☽")
    MERCURY = (2, "☿")
    VENUS = (3, "♀")
    MARS = (4, "♂")
    JUPITER = (5, "♃")
    SATURN = (6, "♄")
    URANUS = (7, "♅")
    NEPTUNE = (8, "♆")
    PLUTO = (9, "♇") # символ ⯓ не поддерживается большинством шрифтов
    # CHIRON = (15, "⚷")
    NORTH_NODE = (10, "☊")
    # SOUTH_NODE = (11, "☋")

    @property
    def code(self) -> int:
        """Возвращает идентификатор планеты, используемый в Swiss Ephemeris."""
        return self.value[0]

    @property
    def symbol(self) -> str:
        """Возвращает символ планеты в юникоде."""
        return self.value[1]

    def __lt__(self, other):
        if isinstance(other, Planet):
            return self.code < other.code
        return NotImplemented

class HouseSystem(Enum):
    """Идентификаторы систем домов, используются в Swiss Ephemeris."""

    PLACIDUS = b"P"
    KOCH = b"K"
    PORPHYRIUS = b"O"
    REGIOMONTANUS = b"R"
    CAMPANUS = b"C"
    EQUAL = b"A"
    EQUAL_2 = b"E"
    VEHLOW_EQUAL = b"V"
    WHOLE_SIGN = b"W"
    MERIDIAN = b"X"
    AZIMUTHAL = b"H"
    POLICH_PAGE = b"T"
    ALCABITUS = b"B"
    MORINUS = b"M"


class ZodiacSign(Enum):
    """Знаки зодиака."""
    # модификатор FE0E (VARIATION SELECTOR-15) добавлен для обеспечения отображения символов монохромно на всех платформах
    ARIES = (0, "\u2648\ufe0e")  # Овен
    TAURUS = (1, "\u2649\ufe0e")  # Телец
    GEMINI = (2, "\u264a\ufe0e")  # Близнецы
    CANCER = (3, "\u264b\ufe0e")  # Рак
    LEO = (4, "\u264c\ufe0e")  # Лев
    VIRGO = (5, "\u264d\ufe0e")  # Дева
    LIBRA = (6, "\u264e\ufe0e")  # Весы
    SCORPIO = (7, "\u264f\ufe0e")  # Скорпион
    SAGITTARIUS = (8, "\u2650\ufe0e")  # Стрелец
    CAPRICORN = (9, "\u2651\ufe0e")  # Козерог
    AQUARIUS = (10, "\u2652\ufe0e")  # Водолей
    PISCES = (11, "\u2653\ufe0e")  # Рыбы

    # ARIES = (0, "♈︎")  # Овен
    # TAURUS = (1, "♉︎")  # Телец
    # GEMINI = (2, "♊︎︎")  # Близнецы
    # CANCER = (3, "♋︎︎")  # Рак
    # LEO = (4, "♌︎︎")  # Лев
    # VIRGO = (5, "♍︎︎")  # Дева
    # LIBRA = (6, "♎︎︎")  # Весы
    # SCORPIO = (7, "♏︎︎")  # Скорпион
    # SAGITTARIUS = (8, "♐︎︎")  # Стрелец
    # CAPRICORN = (9, "♑︎︎")  # Козерог
    # AQUARIUS = (10, "♒︎︎")  # Водолей
    # PISCES = (11, "♓︎︎")  # Рыбы

    @classmethod
    def from_longitude(cls, longitude: float) -> tuple[Self, float]:
        """Создает ZodiacSign из долготы в градусах и угол в знаке."""
        longitude = longitude % 360
        index = int(longitude // 30)
        angle_in_sign = longitude % 30
        return list(cls)[index], angle_in_sign

    @property
    def index(self) -> int:
        """Возвращает индекс знака зодиака (0-11)."""
        return self.value[0]

    @property
    def symbol(self) -> str:
        """Возвращает символ знака зодиака в юникоде."""
        return self.value[1]


@dataclass
class PlanetPosition:
    """Позиция планеты в астрологической карте."""

    planet: Planet
    longitude: float  # градусы
    latitude: float  # градусы
    longitude_speed: float  # градусы в день
    latitude_speed: float  # градусы в день
    distance: float  # расстояние от Земли в астрономических единицах
    distance_speed: (
        float  # скорость изменения расстояния в астрономических единицах в день
    )

    def __post_init__(self):
        self.longitude = self.longitude % 360
        self.latitude = (
            self.latitude % 90 if self.latitude >= 0 else -(abs(self.latitude) % 90)
        )
        if self.planet not in Planet.__members__.values():
            raise ValueError(f"Invalid planet: {self.planet}")
        if self.distance < 0:
            raise ValueError(f"Distance cannot be negative: {self.distance}")

    @staticmethod
    def from_swe_data(planet: Planet, swe_data: list[float]) -> Self:
        """Создает PlanetPosition из данных, возвращаемых Swiss Ephemeris."""
        return PlanetPosition(
            planet=planet,
            longitude=swe_data[0] % 360,
            latitude=swe_data[1] % 90 if swe_data[1] >= 0 else -(abs(swe_data[1]) % 90),
            distance=swe_data[2],
            longitude_speed=swe_data[3],
            latitude_speed=swe_data[4],
            distance_speed=swe_data[5],
        )

    @property
    def zodiac_sign(self) -> ZodiacSign:
        """Возвращает знак зодиака, в котором находится планета."""
        sign, _ = ZodiacSign.from_longitude(self.longitude)
        return sign

    def angle_in_sign(self) -> float:
        """Возвращает угол в знаке зодиака (0-30 градусов)."""
        _, angle = ZodiacSign.from_longitude(self.longitude)
        return angle

    def is_retrograde(self) -> bool:
        """Возвращает True, если планета ретроградна."""
        return self.longitude_speed < 0


@dataclass
class HousePosition:
    """Позиция домов в астрологической карте."""

    house_number: int  # номер дома (1-12)
    cusp_longitude: float  # долгота куспида дома в градусах
    length: float  # длина дома в градусах

    def __post_init__(self):
        if not (1 <= self.house_number <= 12):
            raise ValueError(
                f"house_number must be between 1 and 12, got {self.house_number}"
            )
        self.cusp_longitude = self.cusp_longitude % 360
        if not (0 < self.length <= 360):
            raise ValueError(f"length must be between 0 and 360, got {self.length}")

    @property
    def roman_number(self) -> str:
        """Возвращает номер дома в римской нотации."""
        roman_numerals = [
            "I",
            "II",
            "III",
            "IV",
            "V",
            "VI",
            "VII",
            "VIII",
            "IX",
            "X",
            "XI",
            "XII",
        ]
        return roman_numerals[self.house_number - 1]

    @property
    def zodiac_sign(self) -> ZodiacSign:
        """Знак зодиака, в котором находится куспид дома."""
        return ZodiacSign.from_longitude(self.cusp_longitude)[0]

    @property
    def angle_in_sign(self) -> float:
        """Угол между началом дома и куспидом дома."""
        return self.cusp_longitude % 30

    @classmethod
    def from_swe_data(
        cls, house_number: int, cusp_longitude: float, next_cusp_longitude: float
    ) -> Self:
        """Создает HouseCusp из данных, возвращаемых Swiss Ephemeris."""
        length = (next_cusp_longitude - cusp_longitude) % 360
        return cls(
            house_number=house_number, cusp_longitude=cusp_longitude, length=length
        )

    def has_longitude(self, longitude: float) -> bool:
        """Проверяет, находится ли заданная долгота в пределах этого дома."""
        angle = (longitude - self.cusp_longitude) % 360
        return angle < self.length

    def has_planet(self, planet_position: PlanetPosition) -> bool:
        """Проверяет, находится ли планета в пределах этого дома."""
        return self.has_longitude(planet_position.longitude)


@dataclass
class DatetimeLocation:
    """Дата, время и географическое положение."""

    datetime: datetime
    location: GeoPosition

    def to_julian_day(self) -> float:
        """Преобразует дату и время в юлианскую дату."""
        utc_datetime = self.datetime.astimezone(ZoneInfo("UTC"))  # Convert to UTC
        return swe.julday(
            utc_datetime.year,
            utc_datetime.month,
            utc_datetime.day,
            utc_datetime.hour + utc_datetime.minute / 60 + utc_datetime.second / 3600,
        )

    def get_planet_position(self, planet: Planet) -> tuple:
        """Возвращает позицию планеты в виде (долгота, широта, расстояние от Земли)."""
        jd = self.to_julian_day()
        swe_data, _ = swe.calc_ut(jd, planet.code)

        return PlanetPosition.from_swe_data(planet, swe_data)

    def get_all_planet_positions(
        self, planets: list[Planet] = None
    ) -> list[PlanetPosition]:
        """Возвращает позиции всех планет."""
        if planets is None:
            planets = list(Planet)
        return [self.get_planet_position(planet) for planet in planets]

    def get_house_cusps(
        self, house_system: HouseSystem = HouseSystem.PLACIDUS
    ) -> list[HousePosition]:
        """Возвращает позиции куспидов домов."""
        jd = self.to_julian_day()
        lat = self.location.latitude
        lon = self.location.longitude
        cusps, _ = swe.houses(jd, lat, lon, house_system.value)

        house_cusps = []
        for i in range(12):
            next_cusp = cusps[(i + 1) % 12]
            house_cusps.append(HousePosition.from_swe_data(i + 1, cusps[i], next_cusp))

        return house_cusps


class AspectKind(Enum):
    """Типы аспектов."""

    CONJUNCTION = (0, "☌")  # Соединение (0°)
    SEXTILE = (60, "⚹")  # Секстиль (60°)
    SQUARE = (90, "□")  # Квадрат (90°)
    TRINE = (120, "△")  # Трин (120°)
    OPPOSITION = (180, "☍")  # Оппозиция (180°)

    @property
    def angle(self) -> float:
        """Возвращает угол аспекта в градусах."""
        return self.value[0]

    @property
    def symbol(self) -> str:
        """Возвращает символ аспекта."""
        return self.value[1]


DEFAULT_ORB = 6.0  # стандартная орбисность для аспектов в градусах
ASPECT_ORBS = {
    AspectKind.CONJUNCTION: 8.0,
    AspectKind.SEXTILE: 6.0,
    AspectKind.SQUARE: 6.0,
    AspectKind.TRINE: 6.0,
    AspectKind.OPPOSITION: 8.0,
}


@dataclass
class Aspect:
    """Аспект между планетами."""

    planet1: Planet
    planet2: Planet
    angle: float  # угол между планетами в градусах
    kind: AspectKind  # тип аспекта
    max_orb: float  # допустимый орбис аспекта в градусах, заданный при создании карты

    def __post_init__(self):
        self.angle = self.angle % 360
        if self.angle > 180:
            self.angle = 360 - self.angle  # аспект всегда от 0 до 180 градусов
        if self.max_orb < 0:
            raise ValueError(f"Orb must be non-negative, got {self.max_orb}")
        if self.orb > self.max_orb:
            raise ValueError(
                f"Angle {self.angle} is out of orb {self.max_orb} for aspect type {self.kind}"
            )

    @property
    def orb(self) -> float:
        """Возвращает текущий орбис аспекта."""
        return abs(self.angle - self.kind.angle)

    @classmethod
    def aspect_or_none(
        cls,
        planet1: PlanetPosition,
        planet2: PlanetPosition,
        aspect_type: AspectKind,
        max_orb: float = DEFAULT_ORB,
    ) -> Self | None:
        """Возвращает аспект между двумя планетами или None, если аспекта нет."""
        angle = abs(planet1.longitude - planet2.longitude) % 360
        if angle > 180:
            angle = 360 - angle
        if abs(angle - aspect_type.angle) > max_orb:
            return None
        return cls(
            planet1=planet1.planet,
            planet2=planet2.planet,
            angle=angle,
            kind=aspect_type,
            max_orb=max_orb,
        )

class AspectList(list[Aspect]):
    """Список аспектов с дополнительными методами."""

    def by_type(self, aspect_type: AspectKind) -> Self:
        """Возвращает список аспектов заданного типа."""
        return AspectList([aspect for aspect in self if aspect.kind == aspect_type])

    def by_planet(self, planet: Planet) -> Self:
        """Возвращает список аспектов, в которых участвует заданная планета."""
        return AspectList([
            aspect
            for aspect in self
            if aspect.planet1 == planet or aspect.planet2 == planet
        ])
    
    def sorted_by_planets(self) -> Self:
        """Возвращает список аспектов, отсортированный по именам планет."""
        return AspectList(sorted(self, key=lambda aspect: (aspect.planet1, aspect.planet2)))
    def sorted_by_kind_and_planets(self) -> Self:
        """Возвращает список аспектов, отсортированный по типу аспекта и именам планет."""
        return AspectList(sorted(self, key=lambda aspect: (aspect.kind.value[0], aspect.planet1, aspect.planet2)))

def get_aspects(
    planet_positions: list[PlanetPosition],
    aspect_types: list[AspectKind] = None,
    max_orbs: dict[AspectKind, float] = None,
) -> AspectList:
    """Возвращает список аспектов между планетами."""
    if aspect_types is None:
        aspect_types = list(AspectKind)
    if max_orbs is None:
        max_orbs = ASPECT_ORBS

    aspects = AspectList()

    for p1, p2 in combinations(planet_positions, 2):
        for aspect_type in aspect_types:
            max_orb = max_orbs.get(aspect_type, DEFAULT_ORB)
            aspect = Aspect.aspect_or_none(
                p1, p2, aspect_type, max_orb=max_orb
            )
            if aspect is not None:
                aspects.append(aspect)
    return aspects

def get_planet_houses(
    planet_positions: list[PlanetPosition], house_positions: list[HousePosition]
) -> dict[Planet, HousePosition]:
    """Возвращает словарь с планетами и домами, в которых они находятся."""
    planet_houses = {}
    for planet in planet_positions:
        for house in house_positions:
            if house.has_planet(planet):
                planet_houses[planet.planet] = house
                break
    return planet_houses

def get_house_planets(
    planet_positions: list[PlanetPosition], house_positions: list[HousePosition]
) -> dict[int, list[Planet]]:
    """Возвращает словарь с номерами домов и списками планет, находящихся в этих домах."""
    house_planets = {house.house_number: [] for house in house_positions}
    for planet in planet_positions:
        for house in house_positions:
            if house.has_planet(planet):
                house_planets[house.house_number].append(planet.planet)
                break
    return house_planets

class Chart:
    """Астрологическая карта, включающая позиции планет, куспиды домов и аспекты."""
    def __init__(self, name: str, dt_loc: DatetimeLocation, house_system: HouseSystem = HouseSystem.PLACIDUS):
        self.name = name
        self.dt_loc = dt_loc
        self.house_system = house_system
        
        self.planet_positions = self.dt_loc.get_all_planet_positions()
        self.houses = self.dt_loc.get_house_cusps(self.house_system)
        self.aspects = get_aspects(self.planet_positions).sorted_by_kind_and_planets()
        
        self.planet_houses = get_planet_houses(self.planet_positions, self.houses)
        self.house_planets = get_house_planets(self.planet_positions, self.houses)
