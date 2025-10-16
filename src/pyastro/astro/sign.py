"""Модуль для работы со знаками зодиака."""
from dataclasses import dataclass
from enum import Enum
from typing import Self


class Element(Enum):
    """Стихии."""

    FIRE = "Огонь"
    EARTH = "Земля"
    AIR = "Воздух"
    WATER = "Вода"

    def __str__(self) -> str:
        return self.value


class Modality(Enum):
    """Модальности."""

    CARDINAL = "Кардинальный"
    FIXED = "Фиксированный"
    MUTABLE = "Мутабельный"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class ZodiacSignInfo:
    """Информация о знаке зодиака."""

    element: Element
    modality: Modality


class ZodiacSign(Enum):
    """Знаки зодиака."""

    # модификатор FE0E (VARIATION SELECTOR-15) добавлен для обеспечения отображения символов монохромно на всех платформах
    ARIES = (0, "\u2648\ufe0e", ZodiacSignInfo(Element.FIRE, Modality.CARDINAL))  # Овен
    TAURUS = (1, "\u2649\ufe0e", ZodiacSignInfo(Element.EARTH, Modality.FIXED))  # Телец
    GEMINI = (
        2,
        "\u264a\ufe0e",
        ZodiacSignInfo(Element.AIR, Modality.MUTABLE),
    )  # Близнецы
    CANCER = (
        3,
        "\u264b\ufe0e",
        ZodiacSignInfo(Element.WATER, Modality.CARDINAL),
    )  # Рак
    LEO = (4, "\u264c\ufe0e", ZodiacSignInfo(Element.FIRE, Modality.FIXED))  # Лев
    VIRGO = (5, "\u264d\ufe0e", ZodiacSignInfo(Element.EARTH, Modality.MUTABLE))  # Дева
    LIBRA = (6, "\u264e\ufe0e", ZodiacSignInfo(Element.AIR, Modality.CARDINAL))  # Весы
    SCORPIO = (
        7,
        "\u264f\ufe0e",
        ZodiacSignInfo(Element.WATER, Modality.FIXED),
    )  # Скорпион
    SAGITTARIUS = (
        8,
        "\u2650\ufe0e",
        ZodiacSignInfo(Element.FIRE, Modality.MUTABLE),
    )  # Стрелец
    CAPRICORN = (
        9,
        "\u2651\ufe0e",
        ZodiacSignInfo(Element.EARTH, Modality.CARDINAL),
    )  # Козерог
    AQUARIUS = (
        10,
        "\u2652\ufe0e",
        ZodiacSignInfo(Element.AIR, Modality.FIXED),
    )  # Водолей
    PISCES = (
        11,
        "\u2653\ufe0e",
        ZodiacSignInfo(Element.WATER, Modality.MUTABLE),
    )  # Рыбы

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

    @property
    def element(self) -> Element:
        """Возвращает стихию знака зодиака."""
        return self.value[2].element

    @property
    def modality(self) -> Modality:
        """Возвращает модальность знака зодиака."""
        return self.value[2].modality

    @property
    def ruler(self) -> tuple["Planet"]:
        """Возвращает управителя знака зодиака."""
        from .planet import (
            Planet,
            EssentialDignity,
        )  # импорт здесь, чтобы избежать циклических зависимостей

        return tuple(
            planet
            for planet in Planet
            if planet.dignity(self) == EssentialDignity.DOMICILE
        )

    @property
    def detriment(self) -> tuple["Planet"]:
        """Возвращает планету в изгнании для знака зодиака."""
        from .planet import (
            Planet,
            EssentialDignity,
        )  # импорт здесь, чтобы избежать циклических зависимостей

        return tuple(
            planet
            for planet in Planet
            if planet.dignity(self) == EssentialDignity.DETRIMENT
        )

    @property
    def exaltation(self) -> "Planet":
        """Возвращает планету в экзальтации для знака зодиака."""
        from .planet import (
            Planet,
            EssentialDignity,
        )  # импорт здесь, чтобы избежать циклических зависимостей

        planets = [
            planet
            for planet in Planet
            if planet.dignity(self) == EssentialDignity.EXALTATION
        ]
        if len(planets) == 0:
            return None
        if len(planets) == 1:
            return planets[0]
        raise ValueError(
            f"Знак {self.name} имеет несколько планет в экзальтации: {planets}."
        )

    @property
    def fall(self) -> "Planet":
        """Возвращает планету в падении для знака зодиака."""
        from .planet import (
            Planet,
            EssentialDignity,
        )  # импорт здесь, чтобы избежать циклических зависимостей

        planets = [
            planet for planet in Planet if planet.dignity(self) == EssentialDignity.FALL
        ]
        if len(planets) == 0:
            return None
        if len(planets) == 1:
            return planets[0]
        raise ValueError(f"Знак {self.name} имеет несколько планет в падении.")
