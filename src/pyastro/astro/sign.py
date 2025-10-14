
from enum import Enum
from typing import Self


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
