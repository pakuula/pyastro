from itertools import combinations
import os.path
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Self
from zoneinfo import ZoneInfo

import swisseph as swe

from pyastro.util.angle import parse_lat, parse_lon
from pyastro.util.parse_time import datetime_from_dict

swe.set_ephe_path(
    os.path.dirname(__file__)
)  # Set the path to Swiss Ephemeris data files


@dataclass
class GeoPosition:
    """Географическое положение на поверхности Земли."""

    latitude: float  # градусы, позитивное значение означает северное полушарие
    longitude: float  # градусы, позитивное значение означает восточное полушарие
    elevation: float = 0.0  # высота над уровнем моря в метрах
    place: str = ""  # название места

    @staticmethod
    def from_dict(data: dict) -> Self:
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
        if "place" in data:
            if not isinstance(data["place"], str):
                raise ValueError(
                    f"Invalid type for 'place': expected str, got {type(data['place'])}"
                )
            place = data["place"]
        else:
            place = ""
        return GeoPosition(
            latitude=latitude,
            longitude=longitude,
            elevation=elevation,
            place=place,
        )
        
# swisseph/swephexp.h
# /*
#  * planet numbers for the ipl parameter in swe_calc()
#  */
# #define SE_ECL_NUT      -1
# 
# #define SE_SUN          0
# #define SE_MOON         1
# #define SE_MERCURY      2
# #define SE_VENUS        3
# #define SE_MARS         4
# #define SE_JUPITER      5
# #define SE_SATURN       6
# #define SE_URANUS       7
# #define SE_NEPTUNE      8
# #define SE_PLUTO        9
# #define SE_MEAN_NODE    10
# #define SE_TRUE_NODE    11
# #define SE_MEAN_APOG    12
# #define SE_OSCU_APOG    13
# #define SE_EARTH        14
# #define SE_CHIRON       15
# #define SE_PHOLUS       16
# #define SE_CERES        17
# #define SE_PALLAS       18
# #define SE_JUNO         19
# #define SE_VESTA        20
# #define SE_INTP_APOG    21
# #define SE_INTP_PERG    22
#
# #define SE_NPLANETS     23
#
# #define SE_PLMOON_OFFSET   9000
# #define SE_AST_OFFSET   10000
# #define SE_VARUNA   (SE_AST_OFFSET + 20000)
#
# #define SE_FICT_OFFSET  	40
# #define SE_FICT_OFFSET_1  	39
# #define SE_FICT_MAX  	       999
# #define SE_NFICT_ELEM           15
#
# #define SE_COMET_OFFSET 1000
#
# #define SE_NALL_NAT_POINTS      (SE_NPLANETS + SE_NFICT_ELEM)
#
# /* Hamburger or Uranian "planets" */
# #define SE_CUPIDO       	40
# #define SE_HADES        	41
# #define SE_ZEUS         	42
# #define SE_KRONOS       	43
# #define SE_APOLLON      	44
# #define SE_ADMETOS      	45
# #define SE_VULKANUS     	46
# #define SE_POSEIDON     	47
# /* other fictitious bodies */
# #define SE_ISIS         	48
# #define SE_NIBIRU       	49
# #define SE_HARRINGTON           50
# #define SE_NEPTUNE_LEVERRIER    51
# #define SE_NEPTUNE_ADAMS        52
# #define SE_PLUTO_LOWELL         53
# #define SE_PLUTO_PICKERING      54
# #define SE_VULCAN      		55
# #define SE_WHITE_MOON  		56
# #define SE_PROSERPINA  		57
# #define SE_WALDEMATH  		58



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

class EssentialDignity(Enum):
    Domicile = 0
    Exaltation = 1
    Detriment = 2
    Fall = 3


@dataclass
class PlanetSpec:
    """Спецификация планеты для перечисления Planet."""
    code: int
    symbol: str
    domicile: list[ZodiacSign]
    exaltation: ZodiacSign
    detriment: list[ZodiacSign]
    fall: ZodiacSign
#     Солнце (Sun)	Лев (Leo)	Овен (Aries)	Водолей (Aquarius)	Весы (Libra)
# Луна (Moon)	Рак (Cancer)	Телец (Taurus)	Козерог (Capricorn)	Скорпион (Scorpio)
# Меркурий (Mercury)	Близнецы (Gemini), Дева (Virgo)	Дева (Virgo)	Стрелец (Sagittarius), Рыбы (Pisces)	Рыбы (Pisces)
# Венера (Venus)	Телец (Taurus), Весы (Libra)	Рыбы (Pisces)	Скорпион (Scorpio), Овен (Aries)	Дева (Virgo)
# Марс (Mars)	Овен (Aries), Скорпион (Scorpio)	Козерог (Capricorn)	Весы (Libra), Телец (Taurus)	Рак (Cancer)
# Юпитер (Jupiter)	Стрелец (Sagittarius), Рыбы (Pisces)	Рак (Cancer)	Близнецы (Gemini), Дева (Virgo)	Козерог (Capricorn)
# Сатурн (Saturn)	Козерог (Capricorn), Водолей (Aquarius)	Весы (Libra)	Рак (Cancer), Лев (Leo)	Овен (Aries)
# Уран (Uranus)	Водолей (Aquarius)	Скорпион (Scorpio) (неклассич.)	Лев (Leo)	Телец (Taurus)
# Нептун (Neptune)	Рыбы (Pisces)	Лев (Leo) (неклассич.)	Дева (Virgo)	Козерог (Capricorn)
# Плутон (Pluto)	Скорпион (Scorpio)	Овен (Aries) (неклассич.)	Телец (Taurus)	Весы (Libra)    
    
class Planet(Enum):
    """Идентификаторы планет, используются в Swiss Ephemeris."""

    SUN = PlanetSpec(0, "☉", [ZodiacSign.LEO], ZodiacSign.ARIES, [ZodiacSign.AQUARIUS], ZodiacSign.LIBRA)
    MOON = PlanetSpec(1, "☽", [ZodiacSign.CANCER], ZodiacSign.TAURUS, [ZodiacSign.CAPRICORN], ZodiacSign.SCORPIO)
    MERCURY = PlanetSpec(2, "☿", [ZodiacSign.GEMINI, ZodiacSign.VIRGO], ZodiacSign.VIRGO, [ZodiacSign.SAGITTARIUS, ZodiacSign.PISCES], ZodiacSign.PISCES)
    VENUS = PlanetSpec(3, "♀", [ZodiacSign.TAURUS, ZodiacSign.LIBRA], ZodiacSign.PISCES, [ZodiacSign.SCORPIO, ZodiacSign.ARIES], ZodiacSign.VIRGO)
    MARS = PlanetSpec(4, "♂", [ZodiacSign.ARIES, ZodiacSign.SCORPIO], ZodiacSign.CAPRICORN, [ZodiacSign.LIBRA, ZodiacSign.TAURUS], ZodiacSign.CANCER)
    JUPITER = PlanetSpec(5, "♃", [ZodiacSign.SAGITTARIUS, ZodiacSign.PISCES], ZodiacSign.CANCER, [ZodiacSign.GEMINI, ZodiacSign.VIRGO], ZodiacSign.CAPRICORN)
    SATURN = PlanetSpec(6, "♄", [ZodiacSign.CAPRICORN, ZodiacSign.AQUARIUS], ZodiacSign.LIBRA, [ZodiacSign.CANCER, ZodiacSign.LEO], ZodiacSign.ARIES)
    URANUS = PlanetSpec(7, "♅", [ZodiacSign.AQUARIUS], ZodiacSign.SCORPIO, [ZodiacSign.LEO], ZodiacSign.TAURUS)
    NEPTUNE = PlanetSpec(8, "♆", [ZodiacSign.PISCES], ZodiacSign.LEO, [ZodiacSign.VIRGO], ZodiacSign.CAPRICORN)
    PLUTO = PlanetSpec(9, "⯓", [ZodiacSign.SCORPIO], ZodiacSign.ARIES, [ZodiacSign.TAURUS], ZodiacSign.LIBRA)
    NORTH_NODE = PlanetSpec(10, "☊", [], None, [], None)
    SOUTH_NODE = PlanetSpec(10, "☋", [], None, [], None)
    # CHIRON = (15, "⚷")
    # PHOLUS = (16, "⯛")  # символ U+2BDB
    # CERES = (17, "⚳")  # символ U+26B3
    # PALLAS = (18, "⚴") # символ U+26B4
    # JUNO = (19, "⚵") # символ U+26B5
    # VESTA = (20, "⚶") # символ U+26B6
    # CUPIDO = (40, "⯠")  # символ U+2BE0
    # HADES = (41, "⯡") # символ U+2BE1
    # ZEUS = (42, "⯢") # символ U+2BE2
    # KRONOS = (43, "⯣") # символ U+2BE3
    # APOLLON = (44, "⯤") # символ U+2BE4
    # ADMETOS = (45, "⯥") # символ U+2BE5
    # VULKANUS = (46, "⯦") # символ U+2BE6
    # POSEIDON = (47, "⯧") # символ U+2BE7
    # ISIS = (48, "Is")
    # NIBIRU = (49, "Nb")
    # HARRINGTON = (50, "Hr")
    # NEPTUNE_LEVERRIER = (51, "♆L")
    # NEPTUNE_ADAMS = (52, "♆A")
    # PLUTO_LOWELL = (53, "♇L")
    # PLUTO_PICKERING = (54, "♇P")
    # VULCAN = (55, "√")
    # WHITE_MOON = (56, "⯝") # White Moon Lilith (U+2B5D)
    # PROSERPINA = (57, "⯘") # Proserpina (U+2BD8)
    # WALDEMATH = (58, "⚸") # Black Moon Lilith

    @property
    def code(self) -> int:
        """Возвращает идентификатор планеты, используемый в Swiss Ephemeris."""
        return self.value.code

    @property
    def symbol(self) -> str:
        """Возвращает символ планеты в юникоде."""
        return self.value.symbol
    
    @property
    def domicile(self) -> list[ZodiacSign]:
        """Возвращает знак(и) зодиака, в которых планета находится в обители."""
        return self.value.domicile
    
    @property
    def exaltation(self) -> ZodiacSign:
        """Возвращает знак зодиака, в котором планета находится в экзальтации."""
        return self.value.exaltation
    
    @property
    def detriment(self) -> list[ZodiacSign]:
        """Возвращает знак(и) зодиака, в которых планета находится в падении."""
        return self.value.detriment
    
    @property
    def fall(self) -> ZodiacSign:
        """Возвращает знак зодиака, в котором планета находится в падении."""
        return self.value.fall

    def __lt__(self, other):
        if isinstance(other, Planet):
            return self.code < other.code
        return NotImplemented
    
    def is_south_node(self) -> bool:
        """Возвращает True, если планета - Южный узел."""
        return self == Planet.SOUTH_NODE

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
        latitude=swe_data[1] % 90 if swe_data[1] >= 0 else -(abs(swe_data[1]) % 90)
        return PlanetPosition(
            planet=planet,
            longitude=swe_data[0] % 360 if not planet.is_south_node() else (swe_data[0] + 180) % 360,
            latitude=latitude if not planet.is_south_node() else -latitude,
            distance=swe_data[2],
            longitude_speed=swe_data[3],
            latitude_speed=swe_data[4] if not planet.is_south_node() else -swe_data[4],
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
    
    
    @property
    def is_domicile(self) -> bool:
        """Возвращает True, если планета в обители."""
        return self.zodiac_sign in self.planet.domicile
    
    @property
    def is_exaltation(self) -> bool:
        """Возвращает True, если планета в экзальтации."""
        return self.zodiac_sign == self.planet.exaltation
    
    @property
    def is_detriment(self) -> bool:
        """Возвращает True, если планета в падении."""
        return self.zodiac_sign in self.planet.detriment
    
    @property
    def is_fall(self) -> bool:
        """Возвращает True, если планета в падении."""
        return self.zodiac_sign == self.planet.fall

    def match(self, dignity: EssentialDignity) -> bool:
        match dignity:
            case EssentialDignity.Domicile:
                return self.is_domicile
            case EssentialDignity.Exaltation:
                return self.is_exaltation
            case EssentialDignity.Detriment:
                return self.is_detriment
            case EssentialDignity.Fall:
                return self.is_fall

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
    """Дата, время и географическое положение.

    Дополнительно можно указать, что метка времени приблизительна, и непригодна для вычисления домов."""

    datetime: datetime
    location: GeoPosition
    date_only: bool = False  # если True, время приблизительное, используется только дата

    def to_julian_day(self) -> float:
        """Преобразует дату и время в юлианскую дату."""
        utc_datetime = self.datetime.astimezone(ZoneInfo("UTC"))  # Convert to UTC
        return swe.julday( # pylint: disable=c-extension-no-member
            utc_datetime.year,
            utc_datetime.month,
            utc_datetime.day,
            utc_datetime.hour + utc_datetime.minute / 60 + utc_datetime.second / 3600,
        ) 

    def get_planet_position(self, planet: Planet) -> tuple:
        """Возвращает позицию планеты в виде (долгота, широта, расстояние от Земли)."""
        jd = self.to_julian_day()
        swe_data, _ = swe.calc_ut(jd, planet.code) # pylint: disable=c-extension-no-member

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
        if self.date_only:
            raise ValueError("Невозможно вычислить дома, если date_only=True")
        jd = self.to_julian_day()
        lat = self.location.latitude
        lon = self.location.longitude
        cusps, _ = swe.houses(jd, lat, lon, house_system.value)

        house_cusps = []
        for i in range(12):
            next_cusp = cusps[(i + 1) % 12]
            house_cusps.append(HousePosition.from_swe_data(i + 1, cusps[i], next_cusp))

        return house_cusps

    @staticmethod
    def from_dict(data: dict) -> Self:
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


class AspectKind(Enum):
    """Типы аспектов."""

    CONJUNCTION = (0, "☌", "CON")  # Соединение (0°)
    SEXTILE = (60, "⚹", "SEX")  # Секстиль (60°)
    SQUARE = (90, "□", "SQR")  # Квадрат (90°)
    TRINE = (120, "△", "TRN")  # Трин (120°)
    OPPOSITION = (180, "☍", "OPP")  # Оппозиция (180°)

    @property
    def angle(self) -> float:
        """Возвращает угол аспекта в градусах."""
        return self.value[0]

    @property
    def symbol(self) -> str:
        """Возвращает символ аспекта."""
        return self.value[1]
    
    @property
    def short_name(self) -> str:
        """Возвращает короткое имя аспекта."""
        return self.value[2]


DEFAULT_ORB = 6.0  # стандартная орбисность для аспектов в градусах
ASPECT_ORBS = {
    AspectKind.CONJUNCTION: 8.0,
    AspectKind.SEXTILE: 6.0,
    AspectKind.SQUARE: 6.0,
    AspectKind.TRINE: 6.0,
    AspectKind.OPPOSITION: 8.0,
}
PLANET_ORBS = {
    Planet.SOUTH_NODE: 5,
    Planet.NORTH_NODE: 5,
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
        if planet1.planet == planet2.planet:
            return None
        if planet1.planet.is_south_node() or planet2.planet.is_south_node():
            return None
        if planet1.planet in PLANET_ORBS:
            max_orb = min(max_orb, PLANET_ORBS[planet1.planet])
        if planet2.planet in PLANET_ORBS:
            max_orb = min(max_orb, PLANET_ORBS[planet2.planet])
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

        self.planet_positions: list[PlanetPosition] = self.dt_loc.get_all_planet_positions()
        self.aspects: AspectList = get_aspects(self.planet_positions).sorted_by_kind_and_planets()

        if dt_loc.date_only:
            self.houses = []
            self.ascendant = None
            self.descendant = None
            self.midheaven = None
            self.imum_coeli = None
            self.planet_houses = {}
            self.house_planets = {}
            self.no_houses = True
        else:
            self.houses: list[HousePosition] = self.dt_loc.get_house_cusps(self.house_system)
            self.ascendant: float = self.houses[0].cusp_longitude
            self.descendant: float = (self.ascendant + 180) % 360
            self.midheaven: float = self.houses[9].cusp_longitude
            self.imum_coeli: float = self.houses[3].cusp_longitude
            self.planet_houses: dict[Planet, HousePosition] = get_planet_houses(self.planet_positions, self.houses)
            self.house_planets: dict[int, list[Planet]] = get_house_planets(self.planet_positions, self.houses)
            self.no_houses = False

    @property
    def datetime(self) -> datetime:
        """Возвращает дату и время карты."""
        return self.dt_loc.datetime
    
    @property
    def location(self) -> GeoPosition:
        """Возвращает географическое положение карты."""
        return self.dt_loc.location
    
    def planet_position(self, planet: Planet) -> PlanetPosition | None:
        """Возвращает позицию планеты в карте или None, если планета не найдена."""
        for pos in self.planet_positions:
            if pos.planet == planet:
                return pos
        return None