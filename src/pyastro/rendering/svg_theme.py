"""Тема для диаграммы векторной графики SVG."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, Iterable, Optional, get_args, get_origin


from ..astro import AspectKind

logger = logging.getLogger(__name__)


@dataclass
class Shift:
    """Задает смещения для подписей планет, чтобы не пересекались."""

    dr: float = 0.0  # радиальное смещение
    dangle: float = 0.0  # угловое смещение (в градусах)

    @staticmethod
    def from_dict(data: dict) -> Shift:
        """Создает Shift из JSON-объекта {"dr": float, "dangle": float}."""
        if not isinstance(data, dict):
            raise ValueError("Shift data must be an object")
        return Shift(dr=data.get("dr", 0.0), dangle=data.get("dangle", 0.0))


@dataclass
class SvgTheme:
    """Тема для диаграммы векторной графики SVG."""

    # Параметры полярной системы координат относительно стандартной системы
    clockwise: bool = False  # направление возрастания угла
    zero_at: int = 180  # Положение 0° Овна, 0 - справа (3 часа), 180 - слева (9 часов)

    width: int = 800
    height: int = 800
    margin: int = 40
    background: str = "#ffffff"
    circle_stroke: str = "#222"
    circle_stroke_width: float = 2.0

    houses_outer_stroke: str = "#000000"
    houses_outer_stroke_width: float = 0.0
    # монохромные цвета для зодиака если не задано zodiac_fill
    zodiac_ring_fill: str = "#fafafa"
    zodiac_alt_fill: str = "#f0f0f0"
    # список цветов для знаков, цвет для знака i = zodiac_fill[i % len(zodiac_fill)]
    zodiac_fill: tuple[str, ...] = (
        (
            "#FFDDC1",
            "#0CF05C",
            "#DDDDDD",
            "#C1E1FF",
        )  # цветной зодиак по стихиям огонь-земля-воздух-вода
        # None # Монохромный зодиак:  --- IGNORE ---
    )
    zodiac_border: str = "#999"

    # Параметры подписей планет
    planet_font_size: int = 20
    # чтобы верхняя линия индекса примерно совпадала с верхней линией символа
    planet_angle_baseline_shift = "+30%"
    planet_retro_baseline_shift = "-30%"
    planet_color: str = "#000"
    planet_symbol_offset: float = 25.0
    # Параметры подписей знаков зодиака
    sign_font_size: int = 16
    sign_color: str = "#444"
    # обводка для некоторых символов планет в некоторых шрифтах
    planet_symbol_outlines: Optional[dict[str, float]] = (
        None  # {"VENUS": 1.5, "MARS": 1.5}
    )

    # Масштаб шрифта для дополнительной информации (например, градусы домов)
    extra_info_scale: float = 0.66

    aspect_colors: Optional[dict[AspectKind, str]] = None
    aspect_width: float = 1.6
    tick_length: float = 6.0
    tick_width: float = 1.6
    tick_color: str = "#333"
    tick_opacity: float = 0.85
    # Дополнительное тонкое кольцо с десятиградусными насечками
    tick_limb_width: float = (
        4.0  # planet_r - (planet_r - tick_limb_width) => ширина кольца для 10° насечек
    )
    # Параметры разведения планет
    min_planet_separation_deg: float = 4.0  # кластерный порог (как было)
    cluster_min_pixel_gap: float = (
        16.0  # минимальный пиксельный зазор вдоль дуги между центрами символов
    )
    max_cluster_fan_deg: float = (
        14.0  # ограничение общей веерной ширины кластера (если возможно)
    )
    planet_stack_spacing_px: float = (
        14.0  # радиальное смещение при необходимости доп. слоёв
    )
    max_planet_stack_layers: int = 2  # максимум слоёв (обычно достаточно 2)
    allow_radial_stack: bool = (
        True  # включать ли радиальное дублирование при слишком плотных кластерах
    )
    # Символы аспектов
    show_aspect_symbols: bool = True
    aspect_symbol_font_size: int = 14
    aspect_symbol_fill: str = "#000"
    aspect_symbol_bg: str | None = None  # фон отключен
    aspect_symbol_bg_radius: float = 11.0
    aspect_symbol_bg_opacity: float = 0.85
    aspect_symbol_outline: str | None = "#000"
    aspect_symbol_outline_width: float = 0.6
    # Выделение соединений (дуга по окружности planet_r)
    highlight_conjunctions: bool = True
    conjunction_highlight_color: str = "#009975"  # изумрудно-зелёный
    conjunction_arc_stroke_width: float = 10.0
    conjunction_arc_inner_inset: float = 0.0  # смещение внутрь (уменьшаем радиус дуги)
    conjunction_arc_end_padding_deg: float = (
        1.2  # срез по углам (чтобы не упираться в символы)
    )
    # Базовые отметки позиций планет на окружности planet_r
    show_planet_base_points: bool = True
    planet_base_point_radius: float = 5.0
    planet_base_point_fill: str = "#cccccc"
    planet_base_point_stroke: str = "#000000"
    planet_base_point_stroke_width: float = 0.6

    # Радиусы колец относительно максимального радиуса, равного половине высоты/ширины диаграммы
    house_outer_ratio: float = 1.0  # Внешний радиус домов
    zodiac_outer_ratio: float = 0.86  # Коэффициент радиуса внешнего кольца зодиака
    zodiac_inner_ratio: float = (
        0.75  # внутренний радиус зодиака относительно внешнего радиуса домов
    )
    planet_inner_ratio: float = (
        0.60  # радиус планет относительно внешнего радиуса домов
    )

    # Параметры подписей домов
    house_num_font_size: int = 14
    house_num_color: str = "#555"
    # Смещения подписей домов, чтобы не пересекать линии куспидов
    house_label_tangent_offset_px: float = 16.0  # смещение вдоль касательной (CCW)
    house_label_angle_offset_deg: float = 0.5  # небольшой угловой сдвиг CCW
    # Сдвиг значения угла дома относительно базовой линии номера.
    house_angle_baseline_shift: str = (
        "+30%"  # чтобы верхняя линия индекса примерно совпадала с верхней линией номера дома
    )

    manual_shifts: Optional[dict[str, Shift]] = None  # ручные смещения подписей планет

    def __post_init__(self):
        if self.aspect_colors is None:
            # Цвета: секстиль красный, квадрат тёмно-синий, трин оранжевый, оппозиция чёрная
            self.aspect_colors = {
                AspectKind.CONJUNCTION: "#000000",  # без изменения
                AspectKind.SEXTILE: "#ff0000",  # красный
                AspectKind.SQUARE: "#00008b",  # тёмно-синий
                AspectKind.TRINE: "#ff8800",  # оранжевый
                AspectKind.OPPOSITION: "#000000",  # чёрный
            }
        if self.manual_shifts is None:
            self.manual_shifts = {}
        if self.planet_symbol_outlines is None:
            self.planet_symbol_outlines = {}
        if self.planet_symbol_outlines is None:
            self.planet_symbol_outlines = {}

    @staticmethod
    def aspect_colors_from_dict(data: dict) -> dict[AspectKind, str]:
        """Создает словарь цветов аспектов из JSON-объекта {"CONJUNCTION": color, ...}."""
        if not isinstance(data, dict):
            raise ValueError("Aspect colors data must be an object")
        result = {}
        for k, v in data.items():
            try:
                ak = AspectKind[k.upper()]
                result[ak] = str(v)
            except KeyError:
                logging.warning("Unknown aspect kind in aspect_colors: %s", k)
        return result

    @staticmethod
    def manual_shifts_from_dict(data: dict) -> dict[str, Shift]:
        """Создает словарь ручных смещений планет из JSON-объекта вида

        ```
        {"PLANET": {"dr": float, "dangle": float}, ...}.
        ```
        """
        if not isinstance(data, dict):
            raise ValueError("Manual shifts data must be an object")
        result = {}
        for k, v in data.items():
            if not isinstance(v, dict):
                logging.warning(
                    "Invalid shift data for planet '%s' - %s - skipping", k, v
                )
                continue
            try:
                result[k.upper()] = Shift.from_dict(v)
            except ValueError as e:
                logging.error(
                    "Invalid shift data for planet '%s' - %s: %s - skipping", k, v, e
                )
        return result

    @staticmethod
    def from_dict(data: dict) -> SvgTheme:
        """Создает тему из JSON-объекта."""
        theme = SvgTheme()
        for field, spec in theme.__dataclass_fields__.items():  # pylint: disable=E1101
            if field in data:
                value = data[field]
                if field == "aspect_colors":
                    if not isinstance(value, dict):
                        raise ValueError("aspect_colors must be a dictionary")
                    # Преобразуем ключи в AspectKind
                    new_dict = {}
                    for k, v in value.items():
                        try:
                            ak = AspectKind[k.upper()]
                            new_dict[ak] = v
                        except KeyError:
                            pass
                    setattr(theme, field, new_dict)
                elif field == "manual_shifts":
                    if not isinstance(value, dict):
                        raise ValueError("manual_shifts must be a dictionary")
                    new_dict = {}
                    for k, v in value.items():
                        try:
                            logging.debug(
                                "Parsing manual shift for planet '%s': %s", k, v
                            )
                            new_dict[k.upper()] = Shift.from_dict(v)
                        except ValueError as e:
                            logging.error(
                                "Invalid shift data for planet '%s' - %s: %s - skipping",
                                k,
                                v,
                                e,
                            )
                    setattr(theme, field, new_dict)
                else:
                    # проверить, что тип совпадает (или совместим) с типом поля
                    try:
                        # value = spec.type(value)  # попытка преобразования
                        logger.debug(
                            "Coerce field '%s' of type %s to type %s",
                            field,
                            type(value),
                            spec.type,
                        )
                        if spec.type == int or spec.type == "int":
                            value = int(value)
                        elif spec.type == float or spec.type == "float":
                            value = float(value)
                        elif spec.type == bool or spec.type == "bool":
                            if isinstance(value, bool):
                                pass
                            elif isinstance(value, str):
                                value = value.lower() in ("1", "true", "yes", "on")
                            else:
                                value = bool(value)
                        elif (
                            spec.type == list
                            or spec.type == "list"
                            or (
                                isinstance(spec.type, str)
                                and spec.type.startswith("list[")
                            )
                        ):
                            if not isinstance(value, (list, tuple, Iterable)):
                                raise ValueError(f"Field '{field}' must be an iterable")
                            value = list(value)
                        elif (
                            spec.type == dict
                            or spec.type == "dict"
                            or (
                                isinstance(spec.type, str)
                                and spec.type.startswith("dict[")
                            )
                        ):
                            if not isinstance(value, dict):
                                raise ValueError(
                                    f"Field '{field}' must be a dictionary"
                                )
                            value = dict(value)
                        elif (
                            spec.type == tuple
                            or spec.type == "tuple"
                            or (
                                isinstance(spec.type, str)
                                and spec.type.startswith("tuple[")
                            )
                        ):
                            if not isinstance(value, (list, tuple, Iterable)):
                                raise ValueError(f"Field '{field}' must be an iterable")
                            value = tuple(value)
                        else:
                            logger.warning(
                                "No coercion rule for field '%s' of type %s, using as is",
                                field,
                                spec.type,
                            )

                    except (TypeError, ValueError) as e:
                        raise ValueError(
                            f"Invalid type for field '{field}': "
                            f"expected {spec.type}, got {type(value)}({value}): {e}"
                        ) from e
                    setattr(theme, field, value)
        return theme


def _coerce_type(t: Any, val: Any, field_name: str):
    logger.debug(
        "_coerce_type: type %s, type of type specifier: %s",
        repr(type(val)),
        repr(type(t)),
    )
    origin = get_origin(t)
    logger.debug(
        "Coerce type: %s, origin: %s, value: %s (%s)", t, origin, val, type(val)
    )
    if origin is None:
        # Простой тип
        if isinstance(t, type):
            if isinstance(val, t):
                return val
            try:
                return t(val)
            except Exception as e:  # noqa: BLE001
                raise ValueError(
                    f"Invalid value for '{field_name}': cannot cast {val!r} to {t}"
                ) from e
        elif isinstance(t, str):
            if (t == "list" or t.startswith("list[")) and isinstance(val, (Iterable)):
                return list(val)
            elif (t == "tuple" or t.startswith("tuple[")) and isinstance(
                val, (Iterable)
            ):
                return tuple(val)
            raise ValueError(f"Field '{field_name}' must be a list or tuple")
        else:
            # Аннотация без origin (например |) — просто вернуть как есть
            raise TypeError(f"Cannot coerce field '{t}' is not a type")
        return val
    # Обработка generic
    if origin in (list, tuple):
        (elem_type,) = get_args(t) or (Any,)
        if not isinstance(val, list):
            raise ValueError(f"Field '{field_name}' must be a list")
        return [
            (
                _coerce_type(elem_type, x, f"{field_name}[{i}]")
                if elem_type is not Any
                else x
            )
            for i, x in enumerate(val)
        ]
    if origin is dict:
        key_t, val_t = get_args(t)
        if not isinstance(val, dict):
            raise ValueError(f"Field '{field_name}' must be a dict")
        out = {}
        for k, v in val.items():
            ck = _coerce_type(key_t, k, f"{field_name}.key") if key_t is not Any else k
            cv = _coerce_type(val_t, v, f"{field_name}[{k}]") if val_t is not Any else v
            out[ck] = cv
        return out
    # Иное generic — без строгой обработки
    return val
