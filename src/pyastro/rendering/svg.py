"""SVG rendering for natal chart (Chart object)."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from math import cos, sin, radians, pi
from typing import Any, Iterable, Optional, get_args, get_origin

from ..util.angle import Angle, Latitude, Longitude

from ..astro import Chart, AspectKind, Planet, ZodiacSign

logger = logging.getLogger(__name__)

_SUB_MAP = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
_ROMAN = {
    1: "I",
    2: "II",
    3: "III",
    4: "IV",
    5: "V",
    6: "VI",
    7: "VII",
    8: "VIII",
    9: "IX",
    10: "X",
    11: "XI",
    12: "XII",
}


def int_to_subscript(n: int) -> str:
    return str(n % 30).translate(_SUB_MAP)


def to_roman(n: int) -> str:
    return _ROMAN.get(n, str(n))


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
    zodiac_fill: list[str] = (
        None  # цветной зодиак: ["#FFDDC1", "#C1E1FF", "#C1FFD7", "#FFFAC1", "#E1C1FF", "#FFC1C1"]
    )
    zodiac_border: str = "#999"

    # Параметры подписей планет
    planet_font_size: int = 20
    planet_angle_baseline_shift = "+30%"  # чтобы верхняя линия индекса примерно совпадала с верхней линией символа
    planet_retro_baseline_shift = "-30%"
    planet_color: str = "#000"
    planet_symbol_offset: float = 25.0
    # Параметры подписей знаков зодиака
    sign_font_size: int = 16
    sign_color: str = "#444"
    # обводка для некоторых символов планет в некоторых шрифтах
    planet_symbol_outlines: dict[str, float] = None  # {"VENUS": 1.5, "MARS": 1.5}

    # Масштаб шрифта для дополнительной информации (например, градусы домов)
    extra_info_scale: float = 0.66

    aspect_colors: dict[AspectKind, str] = None
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
    house_outer_ratio: float = 1.0 # Внешний радиус домов
    zodiac_outer_ratio: float = 0.86 # Коэффициент радиуса внешнего кольца зодиака
    zodiac_inner_ratio: float = 0.75  # внутренний радиус зодиака относительно внешнего радиуса домов
    planet_inner_ratio: float = 0.60  # радиус планет относительно внешнего радиуса домов

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

    manual_shifts: dict[str, Shift] = None  # ручные смещения подписей планет

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
        """Создает словарь ручных смещений планет из JSON-объекта {"PLANET": {"dr": float, "dangle": float}, ...}."""
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
                        logger.debug("Coerce field '%s' of type %s to type %s", field, type(value), spec.type)
                        if spec.type == int or spec.type == 'int':
                            value = int(value)
                        elif spec.type == float or spec.type == 'float':
                            value = float(value)
                        elif spec.type == bool or spec.type == 'bool':
                            if isinstance(value, bool):
                                pass
                            elif isinstance(value, str):
                                value = value.lower() in ("1", "true", "yes", "on")
                            else:
                                value = bool(value)
                        elif spec.type == list or spec.type == 'list' or (isinstance(spec.type, str) and spec.type.startswith("list[")):
                            if not isinstance(value, (list, tuple, Iterable)):
                                raise ValueError(f"Field '{field}' must be an iterable")
                            value = list(value)
                        elif spec.type == dict or spec.type == 'dict' or (isinstance(spec.type, str) and spec.type.startswith("dict[")):
                            if not isinstance(value, dict):
                                raise ValueError(f"Field '{field}' must be a dictionary")
                            value = dict(value)
                        elif spec.type == tuple or spec.type == 'tuple' or (isinstance(spec.type, str) and spec.type.startswith("tuple[")):
                            if not isinstance(value, (list, tuple, Iterable)):
                                raise ValueError(f"Field '{field}' must be an iterable")
                            value = tuple(value)
                        else:
                            logger.warning("No coercion rule for field '%s' of type %s, using as is", field, spec.type)
                            
                    except (TypeError, ValueError) as e:
                        raise ValueError(
                            f"Invalid type for field '{field}': expected {spec.type}, got {type(value)}({value}): {e}"
                        ) from e
                    setattr(theme, field, value)
        return theme


def _coerce_type(t: Any, val: Any, field_name: str):
    logger.debug(f"_coerce_type: type {repr(t)}, type of type specifier: {type(t)}")
    origin = get_origin(t)
    logger.debug("Coerce type: %s, origin: %s, value: %s (%s)", t, origin, val, type(val))
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
            elif (t == "tuple" or t.startswith("tuple[")) and isinstance(val, (Iterable)):
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


# Geometry helpers


@dataclass
class PolarConverter:
    """Преобразует полярные координаты в декартовы, учитывая центр и угловой сдвиг."""

    cx: float
    cy: float
    zero_at: int = 180
    clockwise: bool = False
    angle_offset_deg: float = 0.0

    def __call__(self, angle_deg: float, r: float) -> tuple[float, float]:
        angle = self.zero_at + angle_deg + self.angle_offset_deg
        if self.clockwise:
            angle = (360 - angle) % 360
        a = radians(angle)
        return self.cx + r * cos(a), self.cy - r * sin(a)


# Clustering & distribution


def _cluster_planet_positions(chart: Chart, threshold_deg: float) -> list[list]:
    positions = sorted(chart.planet_positions, key=lambda p: p.longitude)
    if not positions:
        return []
    clusters: list[list] = []
    current: list = []
    prev_lon: float | None = None
    for pp in positions:
        if prev_lon is None:
            current = [pp]
        else:
            delta = (pp.longitude - prev_lon) % 360
            if delta > 180:
                delta = 360 - delta
            if delta < threshold_deg:
                current.append(pp)
            else:
                clusters.append(current)
                current = [pp]
        prev_lon = pp.longitude
    if current:
        # wrap-around merge
        first = clusters[0][0] if clusters else None
        if (
            first
            and ((positions[0].longitude - positions[-1].longitude) % 360)
            < threshold_deg
        ):
            clusters[0] = clusters[0] + current
        else:
            clusters.append(current)
    return clusters


def _distribute_cluster(
    cluster, base_angle: float, base_r: float, max_allowed_r: float, theme: SvgTheme
) -> list[tuple[Planet, float, float]]:
    """Возвращает список (planet, angle_deg, radius). Симметричное веерное распределение.
    Если веер превышает max_cluster_fan_deg — уменьшаем до лимита и при нехватке пиксельного зазора включаем радиальный второй слой.
    """
    n = len(cluster)
    if n == 1:
        pp = cluster[0]
        return [(pp.planet, base_angle, min(base_r, max_allowed_r))]
    # Estimate required total fan in degrees from pixel gap requirement.
    # angle_gap_deg = (cluster_min_pixel_gap / arc_length_per_degree) => arc_length_per_degree = (pi/180)*base_r
    if base_r <= 0:
        base_r = 1
    per_deg_arc = (pi / 180.0) * base_r
    min_gap_deg = theme.cluster_min_pixel_gap / per_deg_arc
    total_span_needed = min_gap_deg * (n - 1)
    total_span = min(total_span_needed, theme.max_cluster_fan_deg)
    if n == 2:
        offsets = [-total_span / 2, total_span / 2]
    else:
        # distribute -span/2 .. +span/2
        step = total_span / (n - 1) if n > 1 else 0
        offsets = [-total_span / 2 + i * step for i in range(n)]
    # Check if we satisfied required gap; if not and allowed, add radial layer for overlap indices.
    need_radial = (
        total_span < total_span_needed - 1e-6
        and theme.allow_radial_stack
        and theme.max_planet_stack_layers > 1
    )
    result = []
    for idx, pp in enumerate(cluster):
        ang = (base_angle + offsets[idx]) % 360
        rad = base_r
        if need_radial:
            # Alternate inner/outer slight offsets to disentangle subscripts
            layer = idx % 2  # 0,1
            direction = -1 if layer == 0 else 1
            rad = min(
                max(base_r + direction * theme.planet_stack_spacing_px * 0.6, 0),
                max_allowed_r,
            )
        result.append((pp.planet, ang, min(rad, max_allowed_r)))
    return result


def _layout_planets(
    chart: Chart,
    base_symbol_r: float,
    zodiac_r_inner: float,
    theme: SvgTheme,
    # rotation: float = 0.0,
) -> dict[Planet, tuple[float, float]]:
    clusters = _cluster_planet_positions(chart, theme.min_planet_separation_deg)
    layout: dict[Planet, tuple[float, float]] = {}
    max_allowed = zodiac_r_inner - theme.planet_font_size * 0.65
    for cluster in clusters:
        # базовый угол — средний (с учётом wrap modulo 360? упрощённо берем первого)
        # base_angle = (cluster[0].longitude + rotation) % 360
        base_angle = (cluster[0].longitude) % 360
        distributed = _distribute_cluster(
            cluster, base_angle, base_symbol_r, max_allowed, theme
        )
        for planet, ang, r in distributed:
            layout[planet] = (ang, r)
    return layout


def _conjunction_components(chart: Chart) -> list[list[Planet]]:
    """Находит связные компоненты планет, соединённых аспектами CONJUNCTION."""
    edges: list[tuple[Planet, Planet]] = []
    for a in chart.aspects:
        if a.kind == AspectKind.CONJUNCTION:
            edges.append((a.planet1, a.planet2))
    if not edges:
        return []
    adj: dict[Planet, set[Planet]] = {}
    for p1, p2 in edges:
        adj.setdefault(p1, set()).add(p2)
        adj.setdefault(p2, set()).add(p1)
    visited: set[Planet] = set()
    comps: list[list[Planet]] = []
    for node in adj:
        if node in visited:
            continue
        stack = [node]
        comp: list[Planet] = []
        visited.add(node)
        while stack:
            cur = stack.pop()
            comp.append(cur)
            for nxt in adj.get(cur, ()):  # type: ignore
                if nxt not in visited:
                    visited.add(nxt)
                    stack.append(nxt)
        if len(comp) > 1:
            comps.append(comp)
    return comps


def chart_to_svg(
    chart: Chart, theme: SvgTheme | None = None, angle: float = 0.0
) -> str:
    """Возвращает SVG строку натальной карты.

    angle: на сколько градусов ПОВЕРНУТЬ КОЛЬЦО ЗНАКОВ ЗОДИАКА ПРОТИВ часовой стрелки (только фоновые сектора, символы знаков и граничные 30° тики). Планеты, дома и аспекты остаются в гео-долготах без сдвига.
    """
    if theme is None:
        theme = SvgTheme()
    # ring_angle_offset = angle % 360.0  # полный поворот диаграммы CCW
    # rot = ring_angle_offset

    w, h = theme.width, theme.height
    cx, cy = w / 2, h / 2
    polar = PolarConverter(
        cx=cx,
        cy=cy,
        angle_offset_deg=angle,
        clockwise=theme.clockwise,
        zero_at=theme.zero_at,
    )
    # направление дуг при рисовании от меньшего угла к большему (0 - против часовой, 1 - по часовой)
    sweep_flag = 1 if theme.clockwise else 0

    # Радиусы колец
    max_r = min(w, h) / 2 - theme.margin
    houses_r_outer = max_r * theme.house_outer_ratio
    zodiac_r_outer = max_r * theme.zodiac_outer_ratio
    zodiac_r_inner = max_r * theme.zodiac_inner_ratio
    planet_r = max_r * theme.planet_inner_ratio

    planet_positions = chart.planet_positions
    planet_xy_base: dict[Planet, tuple[float, float]] = {
        pp.planet: polar(pp.longitude % 360, planet_r) for pp in planet_positions
    }

    out: list[str] = []
    ap = out.append
    ap(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
    )
    ap(
        f"""<style>
    text.zodiac {{
      font-family: "Noto Sans Symbol", serif;
      font-weight: bold;
      font-size: {theme.sign_font_size}px;
      fill: "{theme.sign_color}";
    }}
    text.planet {{
      font-family: "Noto Sans Symbol", serif;
      font-weight: bold;
      font-size: {theme.planet_font_size}px;
      fill: "{theme.planet_color}";
    }}
    .venus  {{ stroke:{theme.planet_color}; stroke-width: {theme.planet_symbol_outlines.get("VENUS", 1.5)}; }}
    .mars  {{ stroke:{theme.planet_color}; stroke-width: {theme.planet_symbol_outlines.get("MARS", 1.5)}; }}
    .sun {{ font-size: {theme.planet_font_size*1.24}px; }}
  </style>"""
    )
    ap(f'<rect x="0" y="0" width="{w}" height="{h}" fill="{theme.background}" />')

    # Zodiac ring sectors
    for i in range(12):
        # start_angle = i * 30 + ring_angle_offset
        start_angle = i * 30
        end_angle = start_angle + 30
        x1o, y1o = polar(start_angle, zodiac_r_outer)
        x2o, y2o = polar(end_angle, zodiac_r_outer)
        x2i, y2i = polar(end_angle, zodiac_r_inner)
        x1i, y1i = polar(start_angle, zodiac_r_inner)
        if theme.zodiac_fill and len(theme.zodiac_fill) > 0:
            fill = theme.zodiac_fill[i % len(theme.zodiac_fill)]
        else:
            fill = theme.zodiac_alt_fill if i % 2 else theme.zodiac_ring_fill
        path = (
            f"M {x1o:.2f} {y1o:.2f} "
            f"A {zodiac_r_outer:.2f} {zodiac_r_outer:.2f} 0 0 {sweep_flag} {x2o:.2f} {y2o:.2f} "
            f"L {x2i:.2f} {y2i:.2f} "
            f"A {zodiac_r_inner:.2f} {zodiac_r_inner:.2f} 0 0 {1 - sweep_flag} {x1i:.2f} {y1i:.2f} Z"
        )
        ap(
            f'<path d="{path}" fill="{fill}" stroke="{theme.zodiac_border}" stroke-width="0.5" />'
        )

    # Zodiac signs glyphs
    for i, sign in enumerate(ZodiacSign):
        # mid_angle = i * 30 + 15 + ring_angle_offset
        mid_angle = i * 30 + 15  # середина сектора
        tx, ty = polar(mid_angle, (zodiac_r_outer + zodiac_r_inner) / 2)
        ap(
            f'<text class="zodiac" x="{tx:.2f}" y="{ty:.2f}" text-anchor="middle" dominant-baseline="middle">{sign.symbol}</text>'
        )

    # Houses outer circle and segmented cusps
    ap(
        f'<circle cx="{cx}" cy="{cy}" r="{houses_r_outer:.2f}" fill="none" stroke="{theme.houses_outer_stroke}" stroke-width="{theme.houses_outer_stroke_width}" />'
    )
    for house in chart.houses:
        # ang = (house.cusp_longitude + rot) % 360
        ang = (house.cusp_longitude) % 360
        xpi, ypi = polar(ang, planet_r)
        xzi, yzi = polar(ang, zodiac_r_inner)
        ap(
            f'<line x1="{xpi:.2f}" y1="{ypi:.2f}" x2="{xzi:.2f}" y2="{yzi:.2f}" stroke="{theme.circle_stroke}" stroke-width="0.7" />'
        )
        xzo, yzo = polar(ang, zodiac_r_outer)
        xho, yho = polar(ang, houses_r_outer)
        ap(
            f'<line x1="{xzo:.2f}" y1="{yzo:.2f}" x2="{xho:.2f}" y2="{yho:.2f}" stroke="{theme.circle_stroke}" stroke-width="0.7" />'
        )
        # реальный угол в знаке без учёта поворота (оставляем физическое значение 0..29)
        deg_sub = round(house.cusp_longitude % 30)
        label = (
            f"{to_roman(house.house_number)}"
            # показатель угла куспида дома в знаке
            f"<tspan font-size='{theme.house_num_font_size * theme.extra_info_scale:.0f}' "
            f"baseline-shift='{theme.house_angle_baseline_shift}' "
            ">"
            f"{deg_sub}"
            "</tspan>"
        )
        base_r_label = (houses_r_outer + zodiac_r_outer) / 2
        # лёгкий угловой сдвиг (CCW)
        label_angle = ang + theme.house_label_angle_offset_deg
        ntx, nty = polar(label_angle, base_r_label)
        # касательное смещение вдоль направления увеличения угла (единичный тангенциальный вектор)
        a_rad = radians(ang)
        tx = -sin(a_rad) * theme.house_label_tangent_offset_px
        ty = -cos(a_rad) * theme.house_label_tangent_offset_px
        ntx += tx
        nty += ty
        ap(
            f"<text x='{ntx:.2f}' y='{nty:.2f}' "
            f"font-size='{theme.house_num_font_size}' fill='{theme.house_num_color}' font-weight='bold' "
            f"text-anchor='middle' dominant-baseline='middle'>"
            f"{label}"
            "</text>"
        )

    # Structural circles
    for r in (zodiac_r_outer, zodiac_r_inner, planet_r):
        ap(
            f'<circle cx="{cx}" cy="{cy}" r="{r:.2f}" fill="none" stroke="{theme.circle_stroke}" stroke-width="{theme.circle_stroke_width}" stroke-opacity="0.9" />'
        )

    # Sign boundary ticks on planet_r (inward)
    tick_r_inner = max(planet_r - theme.tick_length, 0)
    for k in range(12):
        # ang = (k * 30 + rot) % 360
        ang = (k * 30) % 360
        x1, y1 = polar(ang, planet_r)
        x2, y2 = polar(ang, tick_r_inner)
        ap(
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{theme.tick_color}" stroke-width="{theme.tick_width}" stroke-linecap="round" stroke-opacity="{theme.tick_opacity}" />'
        )

    # Внутреннее тонкое кольцо и 10° насечки в образованном кольце (planet_r - tick_limb_width .. planet_r)
    limb_r = max(planet_r - theme.tick_limb_width, 0)
    ap(
        f'<circle cx="{cx}" cy="{cy}" r="{limb_r:.2f}" fill="none" stroke="{theme.circle_stroke}" stroke-width="0.4" stroke-opacity="0.6" />'
    )
    for base_ang in range(0, 360, 10):
        # ang = (base_ang + rot) % 360
        ang = (base_ang) % 360
        x1, y1 = polar(ang, planet_r)
        x2, y2 = polar(ang, limb_r)
        ap(
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{theme.tick_color}" stroke-width="0.5" stroke-opacity="0.65" />'
        )

    # Аспекты
    if chart.aspects:
        for aspect in chart.aspects:
            p1 = planet_xy_base.get(aspect.planet1)
            p2 = planet_xy_base.get(aspect.planet2)
            if not p1 or not p2:
                continue
            color = theme.aspect_colors.get(aspect.kind, "#888")
            x1, y1 = p1
            x2, y2 = p2
            ap(
                f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{color}" stroke-width="{theme.aspect_width}" stroke-opacity="0.8" />'
            )
            if theme.show_aspect_symbols and aspect.kind != AspectKind.CONJUNCTION:
                mx = (x1 + x2) / 2
                my = (y1 + y2) / 2
                ap(
                    f'<text x="{mx:.2f}" y="{my:.2f}" '
                    f'font-size="{theme.aspect_symbol_font_size}"  fill="{color}" '
                    f'text-anchor="middle" dominant-baseline="middle">{aspect.kind.symbol}</text>'
                )

    # Расстояние от центра до символов планет
    base_symbol_r = min(
        planet_r + theme.planet_symbol_offset,
        zodiac_r_inner - theme.planet_font_size * 0.65,
    )
    layout = _layout_planets(chart, base_symbol_r, zodiac_r_inner, theme)

    # Дуги соединений по окружности planet_r
    if theme.highlight_conjunctions:
        comps = _conjunction_components(chart)
        if comps:

            def cluster_span(angles: list[float]) -> tuple[float, float]:
                if len(angles) == 1:
                    a = angles[0] % 360
                    return a, a
                a = sorted(x % 360 for x in angles)
                ext = a + [x + 360 for x in a]
                n = len(a)
                best = (0.0, 0.0, 1e9)  # start, end, span
                for i in range(n):
                    end = ext[i + n - 1]
                    start = ext[i]
                    span = end - start
                    if span < best[2]:
                        best = (start, end, span)
                return best[0] % 360, best[1] % 360

            arc_r = max(planet_r - theme.conjunction_arc_inner_inset, 0)
            for comp in comps:
                base_angles = [
                    # ((pp.longitude + rot) % 360)
                    ((pp.longitude) % 360)
                    for pp in planet_positions
                    if pp.planet in comp
                ]
                if len(base_angles) < 2:
                    continue
                start_a, end_a = cluster_span(base_angles)
                # учесть wrap: определяем направление минимальной дуги
                raw_span = (end_a - start_a) % 360
                if raw_span > 180:  # инвертируем чтобы брать короткую сторону
                    start_a, end_a = end_a, start_a
                    raw_span = (end_a - start_a) % 360
                # padding по концам
                pad = theme.conjunction_arc_end_padding_deg
                if raw_span > 2 * pad:
                    start_a = (start_a + pad) % 360
                    end_a = (end_a - pad) % 360
                    raw_span = (end_a - start_a) % 360
                orientation = sweep_flag if start_a < end_a else 1 - sweep_flag
                # точки
                sx, sy = polar(start_a, arc_r)
                ex, ey = polar(end_a, arc_r)
                large_arc = 1 if raw_span > 180 else 0
                path = f"M {sx:.2f} {sy:.2f} A {arc_r:.2f} {arc_r:.2f} 0 {large_arc} {orientation} {ex:.2f} {ey:.2f}"
                ap(
                    f'<path d="{path}" stroke="{theme.conjunction_highlight_color}" stroke-width="{theme.conjunction_arc_stroke_width}" fill="none" stroke-linecap="round" />'
                )
    for pp in planet_positions:
        ang, sr = layout.get(pp.planet, ((pp.longitude) % 360, base_symbol_r))
        # Применяем ручные смещения, если заданы
        if theme.manual_shifts:
            sh = theme.manual_shifts.get(pp.planet.name, None)
        else:
            sh = None
        if sh:
            ang_shifted = (ang + sh.dangle) % 360
            sr_shifted = sr + sh.dr
            sx, sy = polar(ang_shifted, sr_shifted)
        else:
            sx, sy = polar(ang, sr)
        deg_sub = round(pp.angle_in_sign())
        extra_fonst_size = theme.planet_font_size * theme.extra_info_scale
        # Подпись планеты с градусом в знаке + R (если ретроградна)
        extra = ""
        # Индекс ретроградности
        if pp.is_retrograde():
            extra += (
                f"<tspan font-size='{theme.planet_font_size * theme.extra_info_scale:.1f}' "
                # f"baseline-shift='{theme.planet_retro_baseline_shift}'"
                f" dy='{extra_fonst_size*0.4:.1f}'"
                ">R</tspan>"
            )
        # Индекс градуса в знаке
        extra += (
            f"<tspan font-size='{extra_fonst_size:.1f}'"
            # f" baseline-shift='{theme.planet_angle_baseline_shift}'"
            f" dy='{-extra_fonst_size*(0.8 if pp.is_retrograde() else 0.4):.1f}'"
            # Смещение dx - чистая эвристика, ширина символа R шрифта FreeSerif примерно 0.7 от высоты
            f" dx='{-extra_fonst_size*0.7 if pp.is_retrograde() else 0:.1f}'"
            ">"
            f"{deg_sub}</tspan>"
        )
        planet_symbol = f"<tspan class='{pp.planet.name.lower()}'>{pp.planet.symbol}</tspan>{extra}"

        ap(
            f'<text class="planet" x="{sx:.2f}" y="{sy:.2f}" '
            f'font-size="{theme.planet_font_size}" fill="{theme.planet_color}" '
            f'text-anchor="middle" dominant-baseline="middle">{planet_symbol}</text>'
        )
    # Базовые точки планет поверх линий аспектов (перенесено вниз)
    if theme.show_planet_base_points:
        pr = theme.planet_base_point_radius
        for _, (bx, by) in planet_xy_base.items():
            ap(
                f'<circle cx="{bx:.2f}" cy="{by:.2f}" r="{pr:.2f}" fill="{theme.planet_base_point_fill}" stroke="{theme.planet_base_point_stroke}" stroke-width="{theme.planet_base_point_stroke_width}" />'
            )

    ap("</svg>")
    return "\n".join(out)


def to_svg(chart: Chart, svg_chart: Optional[str] = None, theme: SvgTheme | None = None):
    """Возвращает SVG строку документа натальной карты - натальная карта с информацией о человеке и таблицами планет и домов."""
    if svg_chart is None:
        round_chart = chart_to_svg(chart, theme)
    else:
        round_chart = svg_chart

    doc = []
    ap = doc.append

    width = theme.width + 400 if theme else 1200
    height = theme.height if theme else 800
    ap(
        f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">"""
    )
    ap('<style> text.text { font-family: serif; } </style>')

    ap(f'<svg x="200" y="0">{round_chart}</svg>')
    ap('<svg x="0" y="0">')
    ap(
        f'<rect x="0" y="0" width="200" height="{height}" fill="{theme.background if theme else "#fff"}" />'
    )
    ap('<text class="text" x="10" y="40" font-size="24" font-weight="bold">Натальная карта</text>')
    ap(
        f'<text class="text" x="10" y="80" font-size="18">Имя: {chart.name if chart.name else "Не указано"}</text>'
    )
    ap(
        f'<text class="text" x="10" y="110" font-size="18">'
        f'Дата: {chart.datetime.strftime("%Y-%m-%d %H:%M")} {chart.datetime.tzinfo}'
        f'</text>'
    )
    ap(
        f'<text class="text" x="10" y="140" font-size="20">'
        f'Место: {chart.location.place if chart.location.place else "Не указано"} '
        # f"({Latitude( chart.location.latitude)}, {Longitude(chart.location.longitude)})"
        f"</text>"
    )
    ap(f'<text class="text" x="20" y="165" font-size="18">Широта: {Latitude(chart.location.latitude)}</text>')
    ap(f'<text class="text" x="20" y="190" font-size="18">Долгота: {Longitude(chart.location.longitude)}</text>')
    ap('<text class="text" x="10" y="240" font-size="16" font-style="italic">Тропический зодиак</text>')
    ap('<text class="text" x="10" y="265" font-size="16" font-style="italic">Система домов: Плацидус</text>')
    ap("</svg>")
    ap(f'<svg x="{theme.width + 200 if theme else 1000}" y="0">')
    ap(
        f'<rect x="0" y="0" width="200" height="{height}" fill="{theme.background if theme else "#fff"}" />'
    )
    ap('<text class="text" x="0" y="40" font-size="20" font-weight="bold">Планеты</text>')
    start_y = 70
    line_h = 25
    for pp in sorted(chart.planet_positions, key=lambda p: p.planet.code):
        sign = pp.zodiac_sign
        angle = pp.angle_in_sign()
        retro = "R" if pp.is_retrograde() else ""
        ap(f'<g transform="translate(0,{start_y})">'
           f'<text font-size="18">{pp.planet.symbol}</text>'
           f'<text class="text" font-size="18" x="25">{retro}</text>'
           f'<text class="text" font-size="18" x="50">{Angle(angle)}</text>'
           f'<text font-size="18" x="140">{sign.symbol}</text>'
           f'</g>')
        start_y += line_h
    
    start_y += 20
    ap(f'<text x="0" y="{start_y}" font-size="20" font-weight="bold">Дома</text>')
    start_y += 30
    for house_pos in sorted(chart.houses, key=lambda h: h.house_number):
        house_name = house_pos.roman_number
        sign = house_pos.zodiac_sign
        angle = house_pos.angle_in_sign
        ap(f'<g transform="translate(0,{start_y})">'
           f'<text font-size="18">{house_name}</text>'
           f'<text class="text" font-size="18" x="50">{Angle(angle)}</text>'
           f'<text font-size="18" x="140">{sign.symbol}</text>'
           f'</g>')
        start_y += line_h
    ap("</svg>")
    ap("</svg>")

    return "\n".join(doc)


__all__ = ["SvgTheme", "chart_to_svg", "to_svg"]
