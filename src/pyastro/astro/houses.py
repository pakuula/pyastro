
from dataclasses import dataclass
from enum import Enum
from typing import Self
from .planet import PlanetPosition
from .sign import ZodiacSign


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
