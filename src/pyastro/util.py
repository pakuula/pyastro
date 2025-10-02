import re
import sys
from typing import Optional

from pyastro.astro import Angle

_HEMI = {'n': +1, 's': -1, 'e': +1, 'w': -1}

class CoordError(ValueError):
    pass

def _parse_angle_core(text: str) -> tuple[float, Optional[int]]:
    """
    Парсит строку угла в одну из форм: DD, DD MM, DD MM SS.
    Возвращает (abs_degrees, explicit_sign) где explicit_sign ∈ {+1,-1,None}.
    explicit_sign — знак, заданный буквой N/S/E/W или знаком числа.
    """
    s = text.strip()

    # 1) вытащим букву полушария, если есть
    hemi = None
    m = re.search(r'([NnSsEeWw])', s)
    if m:
        hemi = _HEMI[m.group(1).lower()]
        s = re.sub(r'[NnSsEeWw]', ' ', s)

    # 2) нормализуем разделители: всё, что не цифра/знак/точка — в пробел
    #    (поймает ° ' ″, двоеточия и т.п.)
    s = re.sub(r'[^0-9+\-\.]+', ' ', s).strip()

    if not s:
        raise CoordError("Не найдено числовых компонентов угла.")

    # 3) числа (возможен ведущий знак у первого)
    parts = s.split()
    if len(parts) > 3:
        raise CoordError(f"Слишком много компонентов: {parts}")

    # 4) извлечём возможный явный числовой знак у градусов
    num_sign = 1
    try:
        deg = float(parts[0])
    except ValueError as e:
        raise CoordError(f"Некорректные градусы: {parts[0]!r}") from e

    if deg < 0:
        num_sign = -1
        deg = abs(deg)

    minutes = 0.0
    seconds = 0.0

    if len(parts) >= 2:
        try:
            minutes = float(parts[1])
        except ValueError as e:
            raise CoordError(f"Некорректные минуты: {parts[1]!r}") from e
        if not (0.0 <= minutes < 60.0):
            raise CoordError(f"Минуты вне диапазона [0,60): {minutes}")

    if len(parts) == 3:
        try:
            seconds = float(parts[2])
        except ValueError as e:
            raise CoordError(f"Некорректные секунды: {parts[2]!r}") from e
        if not (0.0 <= seconds < 60.0):
            raise CoordError(f"Секунды вне диапазона [0,60): {seconds}")

    value = deg + minutes/60.0 + seconds/3600.0

    # 5) объединяем знаки: при конфликте — ошибка
    if hemi is not None and num_sign != 1:
        if hemi != num_sign:
            raise CoordError("Конфликт знаков: и буква полушария, и числовой знак противоречат друг другу.")
        # если совпадают — ок, используем любой

    sign = hemi if hemi is not None else num_sign
    return value, sign

def parse_coord(text: str, kind: Optional[str] = None) -> float:
    """
    Универсальный парсер координаты (широты/долготы) в градусах (float).
    Поддерживаемые формы: 56.25, -56.25, 56°15′, 56:15:30 N, 56n15, 37e30, 56n15.5 и т.п.

    :param kind: 'lat' проверяет |φ|<=90, 'lon' — |λ|<=180, None — без проверки.
    """
    value_abs, sign = _parse_angle_core(text)
    value = value_abs * (sign or 1)

    if kind == 'lat' and not (-90.0 <= value <= 90.0):
        raise CoordError(f"Широта вне диапазона [-90,90]: {value}")
    if kind == 'lon' and not (-180.0 <= value <= 180.0):
        raise CoordError(f"Долгота вне диапазона [-180,180]: {value}")

    return value

# Удобные обёртки
def parse_lat(text: str) -> float:
    """Парсит широту из строки."""
    return parse_coord(text, kind='lat')

def parse_lon(text: str) -> float:
    """Парсит долготу из строки."""
    return parse_coord(text, kind='lon')

class Longitude(Angle):
    """Долгота с нормализацией в диапазон [-180,180)"""
    def __init__(self, value: float):
        super().__init__(value, from_0_to_360=False)
    
    def __post_init__(self):
        self.value = ((self.value + 180) % 360) - 180
        super().__post_init__()
    
    def __str__(self):
        hemi = 'E' if self.value >= 0 else 'W'
        return f"{abs(self.value):.6f}° {hemi}"

    def __format__(self, format_spec):
        angle_str = format(Angle(abs(self.value), from_0_to_360=False), format_spec)
        hemi = 'E' if self.value >= 0 else 'W'
        return f"{angle_str}{hemi}"

class Latitude(Angle):
    """Широта с нормализацией в диапазон [-90,90]"""
    def __init__(self, value: float):
        super().__init__(value, from_0_to_360=False)
    
    def __post_init__(self):
        d = self.value
        if d > 90 or d < -90:
            d = ((d + 90) % 360) - 90
            if d > 90:
                d = 180 - d
            elif d < -90:
                d = -180 - d
        self.value = d
        super().__post_init__()
    
    def __str__(self):
        hemi = 'N' if self.value >= 0 else 'S'
        return f"{abs(self.value):.6f}° {hemi}"

    def __format__(self, format_spec):
        print(f"DEBUG: format_spec: {format_spec}, value: {self.value}", flush=True, file=sys.stdout)
        angle_str = format(Angle(abs(self.value)), format_spec)
        hemi = 'N' if self.value >= 0 else 'S'
        return f"{angle_str}{hemi}"
