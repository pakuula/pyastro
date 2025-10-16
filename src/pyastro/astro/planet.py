"""Модуль для работы с планетами и их позициями в гороскопе."""
from dataclasses import dataclass
from enum import Enum
from typing import Self

from .sign import ZodiacSign


class EssentialDignity(Enum):
    """Основные достоинства планет."""

    DOMICILE = 0  # обитель
    EXALTATION = 1  # экзальтация
    DETRIMENT = 2  # изгнание
    FALL = 3  # падение


@dataclass
class PlanetSpec:
    """Спецификация планеты для перечисления Planet."""

    code: int
    symbol: str
    domicile: tuple[ZodiacSign] | None = (
        None  # обитель, может быть два знака или None для малых планет
    )
    exaltation: ZodiacSign | None = (
        None  # экзальтация, один знак или None для малых планет
    )
    detriment: tuple[ZodiacSign] | None = (
        None  # изгнание, может быть два знака или None для малых планет
    )
    fall: ZodiacSign | None = None  # падение, один знак или None для малых планет
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

    def dignity(self, sign: ZodiacSign) -> EssentialDignity | None:
        """Возвращает достоинство планеты в данном знаке зодиака."""
        if self.domicile and sign in self.domicile:
            return EssentialDignity.DOMICILE
        elif sign == self.exaltation:
            return EssentialDignity.EXALTATION
        elif self.detriment and sign in self.detriment:
            return EssentialDignity.DETRIMENT
        elif sign == self.fall:
            return EssentialDignity.FALL
        else:
            return None


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


class Planet(Enum):
    """Идентификаторы планет, используются в Swiss Ephemeris."""

    SUN = PlanetSpec(
        code=0,
        symbol="☉",
        domicile=(ZodiacSign.LEO,),
        exaltation=ZodiacSign.ARIES,
        detriment=(ZodiacSign.AQUARIUS,),
        fall=ZodiacSign.LIBRA,
    )
    MOON = PlanetSpec(
        code=1,
        symbol="☽",
        domicile=(ZodiacSign.CANCER,),
        exaltation=ZodiacSign.TAURUS,
        detriment=(ZodiacSign.CAPRICORN,),
        fall=ZodiacSign.SCORPIO,
    )
    # по старой традиции Меркурий управляет Девой и экзальтирует в Деве, следовательно в падении находится в Рыбах,
    # но в современной астрологии он экзальтирует в Водолее, и в падении находится в Льве
    MERCURY = PlanetSpec(
        code=2,
        symbol="☿",
        domicile=(ZodiacSign.GEMINI, ZodiacSign.VIRGO),
        exaltation=ZodiacSign.AQUARIUS,
        detriment=(ZodiacSign.SAGITTARIUS, ZodiacSign.PISCES),
        fall=ZodiacSign.LEO,
    )
    VENUS = PlanetSpec(
        code=3,
        symbol="♀",
        domicile=(ZodiacSign.TAURUS, ZodiacSign.LIBRA),
        exaltation=ZodiacSign.PISCES,
        detriment=(ZodiacSign.SCORPIO, ZodiacSign.ARIES),
        fall=ZodiacSign.VIRGO,
    )
    MARS = PlanetSpec(
        code=4,
        symbol="♂",
        domicile=(ZodiacSign.ARIES, ZodiacSign.SCORPIO),
        exaltation=ZodiacSign.CAPRICORN,
        detriment=(ZodiacSign.LIBRA, ZodiacSign.TAURUS),
        fall=ZodiacSign.CANCER,
    )
    JUPITER = PlanetSpec(
        code=5,
        symbol="♃",
        domicile=(ZodiacSign.SAGITTARIUS, ZodiacSign.PISCES),
        exaltation=ZodiacSign.CANCER,
        detriment=(ZodiacSign.GEMINI, ZodiacSign.VIRGO),
        fall=ZodiacSign.CAPRICORN,
    )
    SATURN = PlanetSpec(
        code=6,
        symbol="♄",
        domicile=(ZodiacSign.CAPRICORN, ZodiacSign.AQUARIUS),
        exaltation=ZodiacSign.LIBRA,
        detriment=(ZodiacSign.CANCER, ZodiacSign.LEO),
        fall=ZodiacSign.ARIES,
    )
    URANUS = PlanetSpec(
        code=7,
        symbol="♅",
        domicile=(ZodiacSign.AQUARIUS,),
        exaltation=None,  # ZodiacSign.SCORPIO,
        detriment=(ZodiacSign.LEO,),
        fall=None,  # ZodiacSign.TAURUS,
    )
    NEPTUNE = PlanetSpec(
        code=8,
        symbol="♆",
        domicile=(ZodiacSign.PISCES,),
        exaltation=None,  # ZodiacSign.SAGITTARIUS,
        detriment=(ZodiacSign.VIRGO,),
        fall=None,  # ZodiacSign.GEMINI,
    )
    PLUTO = PlanetSpec(
        code=9,
        symbol="⯓",
        domicile=(ZodiacSign.SCORPIO,),
        exaltation=None,  # ZodiacSign.LEO,
        detriment=(ZodiacSign.TAURUS,),
        fall=None,  # ZodiacSign.AQUARIUS,
    )
    NORTH_NODE = PlanetSpec(10, "☊")  # символ U+260A
    SOUTH_NODE = PlanetSpec(10, "☋")  # символ U+260B
    # для малых планет и астероидов достоинства не определены
    CHIRON = PlanetSpec(15, "⚷")  # символ U+26B7
    PHOLUS = PlanetSpec(16, "⯛")  # символ U+2BDB
    CERES = PlanetSpec(17, "⚳")  # символ U+26B3
    PALLAS = PlanetSpec(18, "⚴")  # символ U+26B4
    JUNO = PlanetSpec(19, "⚵")  # символ U+26B5
    VESTA = PlanetSpec(20, "⚶")  # символ U+26B6
    CUPIDO = PlanetSpec(40, "⯠")  # символ U+2BE0
    HADES = PlanetSpec(41, "⯡")  # символ U+2BE1
    ZEUS = PlanetSpec(42, "⯢")  # символ U+2BE2
    KRONOS = PlanetSpec(43, "⯣")  # символ U+2BE3
    APOLLON = PlanetSpec(44, "⯤")  # символ U+2BE4
    ADMETOS = PlanetSpec(45, "⯥")  # символ U+2BE5
    VULKANUS = PlanetSpec(46, "⯦")  # символ U+2BE6
    POSEIDON = PlanetSpec(47, "⯧")  # символ U+2BE7
    # Псевдопланеты
    ISIS = PlanetSpec(48, "Is")
    NIBIRU = PlanetSpec(49, "Nb")
    HARRINGTON = PlanetSpec(50, "Hr")
    NEPTUNE_LEVERRIER = PlanetSpec(51, "♆L")
    NEPTUNE_ADAMS = PlanetSpec(52, "♆A")
    PLUTO_LOWELL = PlanetSpec(53, "♇L")
    PLUTO_PICKERING = PlanetSpec(54, "♇P")
    VULCAN = PlanetSpec(55, "√")
    WHITE_MOON = PlanetSpec(56, "⯝")  # White Moon Lilith (U+2B5D)
    PROSERPINA = PlanetSpec(57, "⯘")  # Proserpina (U+2BD8)
    WALDEMATH = PlanetSpec(58, "⚸")  # Black Moon Lilith

    @property
    def code(self) -> int:
        """Возвращает идентификатор планеты, используемый в Swiss Ephemeris."""
        return self.value.code

    @property
    def symbol(self) -> str:
        """Возвращает символ планеты в юникоде."""
        return self.value.symbol

    @property
    def domicile(self) -> tuple[ZodiacSign] | None:
        """Возвращает знак(и) зодиака, в которых планета находится в обители."""
        return self.value.domicile

    @property
    def exaltation(self) -> ZodiacSign | None:
        """Возвращает знак зодиака, в котором планета находится в экзальтации."""
        return self.value.exaltation

    @property
    def detriment(self) -> tuple[ZodiacSign] | None:
        """Возвращает знак(и) зодиака, в которых планета находится в падении."""
        return self.value.detriment

    @property
    def fall(self) -> ZodiacSign:
        """Возвращает знак зодиака, в котором планета находится в падении."""
        return self.value.fall

    def dignity(self, sign: ZodiacSign) -> EssentialDignity | None:
        """Возвращает достоинство планеты в данном знаке зодиака."""
        return self.value.dignity(sign)

    def __lt__(self, other):
        if isinstance(other, Planet):
            return self.code < other.code
        return NotImplemented

    def is_south_node(self) -> bool:
        """Возвращает True, если планета - Южный узел."""
        return self == Planet.SOUTH_NODE


CLASSIC_PLANETS = (
    Planet.SUN,
    Planet.MOON,
    Planet.MERCURY,
    Planet.VENUS,
    Planet.MARS,
    Planet.JUPITER,
    Planet.SATURN,
)

NEW_PLANETS = CLASSIC_PLANETS + (Planet.URANUS, Planet.NEPTUNE, Planet.PLUTO)
NEW_PLANETS_WITH_NODES = NEW_PLANETS + (Planet.NORTH_NODE, Planet.SOUTH_NODE)


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
        latitude = swe_data[1] % 90 if swe_data[1] >= 0 else -(abs(swe_data[1]) % 90)
        return PlanetPosition(
            planet=planet,
            longitude=(
                swe_data[0] % 360
                if not planet.is_south_node()
                else (swe_data[0] + 180) % 360
            ),
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

    @property
    def dignity(self) -> EssentialDignity | None:
        """Возвращает достоинство планеты в данном знаке зодиака."""
        return self.planet.dignity(self.zodiac_sign)

    def match_dignity(self, dignity: EssentialDignity) -> bool:
        """Проверяет, соответствует ли достоинство планеты заданному достоинству."""
        if self.dignity is None:
            return False
        return dignity == self.dignity
