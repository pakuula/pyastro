
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from itertools import combinations
from typing import Self
from pyastro.astro.date_time_position import DatetimeLocation, GeoPosition
from pyastro.astro.houses import HousePosition, HouseSystem
from pyastro.astro.planet import Planet, PlanetPosition


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
