import os.path
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Self
from zoneinfo import ZoneInfo

import swisseph as swe

swe.set_ephe_path(
    os.path.dirname(__file__)
)  # Set the path to Swiss Ephemeris data files


@dataclass
class GeoPosition:
    """Географическое положение на поверхности Земли."""

    latitude: float  # градусы, позитивное значение означает северное полушарие
    longitude: float  # градусы, позитивное значение означает восточное полушарие
    elevation: float = 0.0  # высота над уровнем моря в метрах


class Planet(Enum):
    """Идентификаторы планет, используются в Swiss Ephemeris."""

    SUN = 0
    MOON = 1
    MERCURY = 2
    VENUS = 3
    MARS = 4
    JUPITER = 5
    SATURN = 6
    URANUS = 7
    NEPTUNE = 8
    PLUTO = 9
    # CHIRON = 15
    NORTH_NODE = 10
    # SOUTH_NODE = 11

    @property
    def symbol(self) -> str:
        """Возвращает символ планеты в юникоде."""
        return _planet_symbols[self]


_planet_symbols = {
    Planet.SUN: "☉",
    Planet.MOON: "☽",
    Planet.MERCURY: "☿",
    Planet.VENUS: "♀",
    Planet.MARS: "♂",
    Planet.JUPITER: "♃",
    Planet.SATURN: "♄",
    Planet.URANUS: "♅",
    Planet.NEPTUNE: "♆",
    Planet.PLUTO: "♇",
    # Planet.CHIRON: "⚷",
    Planet.NORTH_NODE: "☊",
    # Planet.SOUTH_NODE: "☋",
}


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


_zodiac_symbols = [
    "♈︎︎",  # Aries
    "♉︎︎",  # Taurus
    "♊︎︎",  # Gemini
    "♋︎︎",  # Cancer
    "♌︎︎",  # Leo
    "♍︎︎",  # Virgo
    "♎︎︎",  # Libra
    "♏︎︎",  # Scorpio
    "♐︎︎",  # Sagittarius
    "♑︎︎",  # Capricorn
    "♒︎︎",  # Aquarius
    "♓︎︎",  # Pisces
]


class ZodiacSign(Enum):
    """Знаки зодиака."""

    ARIES = 0  # Овен
    TAURUS = 1  # Телец
    GEMINI = 2  # Близнецы
    CANCER = 3  # Рак
    LEO = 4  # Лев
    VIRGO = 5  # Дева
    LIBRA = 6  # Весы
    SCORPIO = 7  # Скорпион
    SAGITTARIUS = 8  # Стрелец
    CAPRICORN = 9  # Козерог
    AQUARIUS = 10  # Водолей
    PISCES = 11  # Рыбы

    @classmethod
    def from_longitude(cls, longitude: float) -> tuple[Self, float]:
        """Создает ZodiacSign из долготы в градусах и угол в знаке."""
        longitude = longitude % 360
        index = int(longitude // 30)
        return cls(index), longitude % 30

    @property
    def symbol(self) -> str:
        """Возвращает символ знака зодиака в юникоде."""
        return _zodiac_symbols[self.value]


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
    def zodiac_sign(self) -> ZodiacSign:
        """Знак зодиака, в котором находится куспид дома."""
        return ZodiacSign(self.cusp_longitude // 30)

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
class Angle:
    """Долгота или широта, с поддержкой арифметики и форматирования.

    Значение всегда хранится в градусах.

    :param value: значение угла в градусах
    :param from_0_to_360: если True, значение всегда от 0 до 360, иначе от -180 до +180
    """

    value: float  # градусы
    from_0_to_360: bool = (
        True  # если True, значение всегда от 0 до 360, иначе от -180 до +180
    )

    def __post_init__(self):
        if self.from_0_to_360:
            self.value = self.value % 360
        else:
            self.value = ((self.value + 180) % 360) - 180

    def __add__(self, other: Any) -> Self:
        if isinstance(other, Angle):
            return Angle(self.value + other.value, self.from_0_to_360)
        elif isinstance(other, (int, float)):
            return Angle(self.value + other, self.from_0_to_360)
        return NotImplemented

    def __sub__(self, other: Any) -> Self:
        if isinstance(other, Angle):
            return Angle(self.value - other.value, self.from_0_to_360)
        elif isinstance(other, (int, float)):
            return Angle(self.value - other, self.from_0_to_360)
        return NotImplemented

    def __mul__(self, other: Any) -> Self:
        if isinstance(other, (int, float)):
            return Angle(self.value * other, self.from_0_to_360)
        return NotImplemented

    def __truediv__(self, other: Any) -> Self:
        if isinstance(other, (int, float)):
            return Angle(self.value / other, self.from_0_to_360)
        return NotImplemented

    def __repr__(self) -> str:
        return f"Angle({self.value}, from_0_to_360={self.from_0_to_360})"

    def __str__(self) -> str:
        if self.from_0_to_360:
            sign = ""
            deg = int(self.value)
            min = int((self.value - deg) * 60)
            sec = ((self.value - deg) * 60 - min) * 60
        else:
            sign = "+" if self.value >= 0 else "-"
            abs_value = abs(self.value)
            deg = int(abs_value)
            min = int((abs_value - deg) * 60)
            sec = ((abs_value - deg) * 60 - min) * 60
        return f'''{sign}{deg}°{min}'{sec:.2f}"'''

    @classmethod
    def from_str(cls, angle_str: str, from_0_to_360: bool = False) -> Self:
        """Парсит строку в формате ±DD°MM'SS.SS" в Angle."""
        angle_str = angle_str.strip()
        if not angle_str:
            raise ValueError("Empty angle string")

        sign = 1
        if angle_str[0] == "-":
            if from_0_to_360:
                raise ValueError("Negative angle not allowed in 0-360 mode")
            sign = -1
            angle_str = angle_str[1:].strip()
        elif angle_str[0] == "+":
            angle_str = angle_str[1:].strip()

        try:
            deg_part, rest = angle_str.split("°", 1)
            deg = int(deg_part.strip())
            min_part, sec_part = rest.split("'", 1)
            min = int(min_part.strip())
            sec = float(sec_part.strip().rstrip('"'))
        except Exception as e:
            raise ValueError(f"Invalid angle format: {angle_str}") from e

        if not (0 <= deg <= 360 and 0 <= min < 60 and 0 <= sec < 60):
            raise ValueError(f"Angle components out of range in: {angle_str}")

        total_degrees = sign * (deg + min / 60 + sec / 3600)
        from_0_to_360 = from_0_to_360 or total_degrees >= 0
        return cls(total_degrees, from_0_to_360)

    @classmethod
    def from_longitude(cls, longitude: float) -> Self:
        """Создает Angle из долготы в градусах."""
        return cls(longitude, True)

    @classmethod
    def from_latitude(cls, latitude: float) -> Self:
        """Создает Angle из широты в градусах."""
        return cls(latitude, False)

    @classmethod
    def Lat(cls, latitude: float) -> Self:
        """Создает Angle из широты в градусах."""
        return cls(latitude, False)

    @classmethod
    def Lon(cls, longitude: float) -> Self:
        """Создает Angle из долготы в градусах."""
        return cls(longitude, True)


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
        swe_data, _ = swe.calc_ut(jd, planet.value)

        return PlanetPosition.from_swe_data(planet, swe_data)

    def get_all_planet_positions(self) -> list[PlanetPosition]:
        """Возвращает позиции всех планет."""
        return [self.get_planet_position(planet) for planet in Planet]

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
