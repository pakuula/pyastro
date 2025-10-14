import os.path as ospath

import swisseph as swe

# Ephemeris data files are expected to be in the same directory as this __init__.py file
swe.set_ephe_path( # pylint: disable=I1101
    ospath.dirname(__file__)
)  # Set the path to Swiss Ephemeris data files

del swe
del ospath

from .chart import Aspect, AspectKind, DEFAULT_ORB, PLANET_ORBS, ASPECT_ORBS, Chart
from .date_time_position import DatetimeLocation, GeoPosition
from .houses import HouseSystem, HousePosition
from .planet import Planet, EssentialDignity, PlanetPosition, CLASSIC_PLANETS, NEW_PLANETS, NEW_PLANETS_WITH_NODES
from .sign import ZodiacSign

__all__ = [
    "ZodiacSign",
    "HouseSystem",
    "HousePosition",
    "Planet",
    "PlanetPosition",
    "EssentialDignity",
    "AspectKind",
    "Aspect",
    "Chart",
    "GeoPosition",
    "DatetimeLocation",
    "DEFAULT_ORB",
    "PLANET_ORBS",
    "ASPECT_ORBS",
    "CLASSIC_PLANETS",
    "NEW_PLANETS",
    "NEW_PLANETS_WITH_NODES",
]
