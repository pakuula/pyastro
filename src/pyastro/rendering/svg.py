"""SVG rendering for natal chart (Chart object).

Orientation: 0° находится на направлении "3 часа" (точка справа), углы растут ПРОТИВ часовой стрелки.
Граница между Рыбами (330°–360°) и Овном (0°–30°) лежит на направлении 0°.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import cos, sin, radians, pi

from ..astro import Chart, AspectKind, Planet

_SUB_MAP = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
_ROMAN = {1:"I",2:"II",3:"III",4:"IV",5:"V",6:"VI",7:"VII",8:"VIII",9:"IX",10:"X",11:"XI",12:"XII"}

def int_to_subscript(n: int) -> str:
    return str(n % 30).translate(_SUB_MAP)

def to_roman(n: int) -> str:
    return _ROMAN.get(n, str(n))

@dataclass
class SvgTheme:
    width: int = 800
    height: int = 800
    margin: int = 40
    background: str = "#ffffff"
    circle_stroke: str = "#222"
    circle_stroke_width: float = 2.0
    zodiac_ring_fill: str = "#fafafa"
    zodiac_alt_fill: str = "#f0f0f0"
    zodiac_border: str = "#999"
    planet_font_size: int = 20
    planet_color: str = "#000"
    planet_symbol_offset: float = 25.0
    sign_font_size: int = 16
    sign_color: str = "#444"
    house_num_font_size: int = 12
    house_num_color: str = "#555"
    # Сдвиг нижнего индекса домов (относительно базовой линии номера). Отрицательный % поднимает.
    house_subscript_baseline_shift: str = "sub"  # чтобы baseline номера примерно проходила через центр индекса
    aspect_colors: dict[AspectKind, str] = None
    aspect_width: float = 1.6
    tick_length: float = 6.0
    tick_width: float = 1.6
    tick_color: str = "#333"
    tick_opacity: float = 0.85
    # Дополнительное тонкое кольцо с десятиградусными насечками
    tick_limb_width: float = 4.0  # planet_r - (planet_r - tick_limb_width) => ширина кольца для 10° насечек
    # Параметры разведения планет
    min_planet_separation_deg: float = 4.0      # кластерный порог (как было)
    cluster_min_pixel_gap: float = 16.0         # минимальный пиксельный зазор вдоль дуги между центрами символов
    max_cluster_fan_deg: float = 14.0           # ограничение общей веерной ширины кластера (если возможно)
    planet_stack_spacing_px: float = 14.0       # радиальное смещение при необходимости доп. слоёв
    max_planet_stack_layers: int = 2            # максимум слоёв (обычно достаточно 2)
    allow_radial_stack: bool = True             # включать ли радиальное дублирование при слишком плотных кластерах
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
    conjunction_arc_inner_inset: float = 2.0   # смещение внутрь (уменьшаем радиус дуги)
    conjunction_arc_end_padding_deg: float = 1.2  # срез по углам (чтобы не упираться в символы)
    # Базовые отметки позиций планет на окружности planet_r
    show_planet_base_points: bool = True
    planet_base_point_radius: float = 5.0
    planet_base_point_fill: str = "#cccccc"
    planet_base_point_stroke: str = "#000000"
    planet_base_point_stroke_width: float = 0.6
    # Масштаб нижних индексов (subscripts) относительно основного размера символа
    subscript_scale: float = 0.66
    # Коэффициент радиуса внешнего кольца зодиака относительно внешнего радиуса домов
    zodiac_outer_ratio: float = 0.86  # было 0.93; меньше -> шире кольцо домов
    # Смещения подписей домов, чтобы не пересекать линии куспидов
    house_label_tangent_offset_px: float = 8.0  # смещение вдоль касательной (CCW)
    house_label_angle_offset_deg: float = 0.5   # небольшой угловой сдвиг CCW

    def __post_init__(self):
        if self.aspect_colors is None:
            # Цвета: секстиль красный, квадрат тёмно-синий, трин оранжевый, оппозиция чёрная
            self.aspect_colors = {
                AspectKind.CONJUNCTION: "#000000",  # без изменения
                AspectKind.SEXTILE: "#ff0000",      # красный
                AspectKind.SQUARE: "#00008b",       # тёмно-синий
                AspectKind.TRINE: "#ff8800",        # оранжевый
                AspectKind.OPPOSITION: "#000000",   # чёрный
            }

# Geometry helpers

def polar(cx: float, cy: float, r: float, angle_deg: float) -> tuple[float, float]:
    a = radians(angle_deg)  # 0° = (r,0); CCW
    return cx + r * cos(a), cy - r * sin(a)

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
        if first and ((positions[0].longitude - positions[-1].longitude) % 360) < threshold_deg:
            clusters[0] = clusters[0] + current
        else:
            clusters.append(current)
    return clusters


def _distribute_cluster(cluster, base_angle: float, base_r: float, max_allowed_r: float, theme: SvgTheme) -> list[tuple[Planet, float, float]]:
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
        offsets = [-total_span/2, total_span/2]
    else:
        # distribute -span/2 .. +span/2
        step = total_span / (n - 1) if n > 1 else 0
        offsets = [-total_span / 2 + i * step for i in range(n)]
    # Check if we satisfied required gap; if not and allowed, add radial layer for overlap indices.
    need_radial = total_span < total_span_needed - 1e-6 and theme.allow_radial_stack and theme.max_planet_stack_layers > 1
    result = []
    for idx, pp in enumerate(cluster):
        ang = (base_angle + offsets[idx]) % 360
        rad = base_r
        if need_radial:
            # Alternate inner/outer slight offsets to disentangle subscripts
            layer = idx % 2  # 0,1
            direction = -1 if layer == 0 else 1
            rad = min(max(base_r + direction * theme.planet_stack_spacing_px * 0.6, 0), max_allowed_r)
        result.append((pp.planet, ang, min(rad, max_allowed_r)))
    return result


def _layout_planets(chart: Chart, base_symbol_r: float, zodiac_r_inner: float, theme: SvgTheme, rotation: float = 0.0) -> dict[Planet, tuple[float, float]]:
    clusters = _cluster_planet_positions(chart, theme.min_planet_separation_deg)
    layout: dict[Planet, tuple[float, float]] = {}
    max_allowed = zodiac_r_inner - theme.planet_font_size * 0.65
    for cluster in clusters:
        # базовый угол — средний (с учётом wrap modulo 360? упрощённо берем первого)
        base_angle = (cluster[0].longitude + rotation) % 360
        distributed = _distribute_cluster(cluster, base_angle, base_symbol_r, max_allowed, theme)
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


def chart_to_svg(chart: Chart, theme: SvgTheme | None = None, angle: float = 0.0) -> str:
    """Возвращает SVG строку натальной карты.

    angle: на сколько градусов ПОВЕРНУТЬ КОЛЬЦО ЗНАКОВ ЗОДИАКА ПРОТИВ часовой стрелки (только фоновые сектора, символы знаков и граничные 30° тики). Планеты, дома и аспекты остаются в гео-долготах без сдвига.
    """
    if theme is None:
        theme = SvgTheme()
    ring_angle_offset = angle % 360.0  # полный поворот диаграммы CCW
    rot = ring_angle_offset

    w, h = theme.width, theme.height
    cx, cy = w / 2, h / 2

    houses_r_outer = min(w, h) / 2 - theme.margin
    zodiac_r_outer = houses_r_outer * theme.zodiac_outer_ratio
    zodiac_r_inner = zodiac_r_outer * 0.82
    planet_r = zodiac_r_inner * 0.80

    planet_positions = chart.planet_positions
    planet_xy_base: dict[Planet, tuple[float, float]] = {
        pp.planet: polar(cx, cy, planet_r, (pp.longitude + rot) % 360) for pp in planet_positions
    }

    out: list[str] = []
    ap = out.append
    ap(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">')
    ap(f'<rect x="0" y="0" width="{w}" height="{h}" fill="{theme.background}" />')

    # Zodiac ring sectors CCW
    for i in range(12):
        start_angle = i * 30 + ring_angle_offset
        end_angle = start_angle + 30
        x1o, y1o = polar(cx, cy, zodiac_r_outer, start_angle)
        x2o, y2o = polar(cx, cy, zodiac_r_outer, end_angle)
        x2i, y2i = polar(cx, cy, zodiac_r_inner, end_angle)
        x1i, y1i = polar(cx, cy, zodiac_r_inner, start_angle)
        fill = theme.zodiac_alt_fill if i % 2 else theme.zodiac_ring_fill
        path = (
            f"M {x1o:.2f} {y1o:.2f} "
            f"A {zodiac_r_outer:.2f} {zodiac_r_outer:.2f} 0 0 0 {x2o:.2f} {y2o:.2f} "
            f"L {x2i:.2f} {y2i:.2f} "
            f"A {zodiac_r_inner:.2f} {zodiac_r_inner:.2f} 0 0 1 {x1i:.2f} {y1i:.2f} Z"
        )
        ap(f'<path d="{path}" fill="{fill}" stroke="{theme.zodiac_border}" stroke-width="0.5" />')

    # Zodiac signs glyphs
    zodiac_enum = planet_positions[0].zodiac_sign.__class__ if planet_positions else []
    for i, sign in enumerate(zodiac_enum):
        mid_angle = i * 30 + 15 + ring_angle_offset
        tx, ty = polar(cx, cy, (zodiac_r_outer + zodiac_r_inner)/2, mid_angle)
        ap(f'<text x="{tx:.2f}" y="{ty:.2f}" font-size="{theme.sign_font_size}" text-anchor="middle" dominant-baseline="middle" fill="{theme.sign_color}">{sign.symbol}</text>')

    # Houses outer circle and segmented cusps
    ap(f'<circle cx="{cx}" cy="{cy}" r="{houses_r_outer:.2f}" fill="none" stroke="{theme.circle_stroke}" stroke-width="{theme.circle_stroke_width}" />')
    for house in chart.houses:
        ang = (house.cusp_longitude + rot) % 360
        xpi, ypi = polar(cx, cy, planet_r, ang)
        xzi, yzi = polar(cx, cy, zodiac_r_inner, ang)
        ap(f'<line x1="{xpi:.2f}" y1="{ypi:.2f}" x2="{xzi:.2f}" y2="{yzi:.2f}" stroke="{theme.circle_stroke}" stroke-width="0.7" />')
        xzo, yzo = polar(cx, cy, zodiac_r_outer, ang)
        xho, yho = polar(cx, cy, houses_r_outer, ang)
        ap(f'<line x1="{xzo:.2f}" y1="{yzo:.2f}" x2="{xho:.2f}" y2="{yho:.2f}" stroke="{theme.circle_stroke}" stroke-width="0.7" />')
        # реальный угол в знаке без учёта поворота (оставляем физическое значение 0..29)
        deg_sub = round(house.cusp_longitude % 30)
        label = (
            f"{to_roman(house.house_number)}"
            f"<tspan font-size='{theme.house_num_font_size * theme.subscript_scale:.0f}' "
            f"baseline-shift='{theme.house_subscript_baseline_shift}'>{deg_sub}</tspan>"
        )
        base_r_label = (houses_r_outer + zodiac_r_outer) / 2
        # лёгкий угловой сдвиг (CCW)
        label_angle = ang + theme.house_label_angle_offset_deg
        ntx, nty = polar(cx, cy, base_r_label, label_angle)
        # касательное смещение вдоль направления увеличения угла (единичный тангенциальный вектор)
        a_rad = radians(ang)
        tx = -sin(a_rad) * theme.house_label_tangent_offset_px
        ty = -cos(a_rad) * theme.house_label_tangent_offset_px
        ntx += tx
        nty += ty
        ap(f"<text x='{ntx:.2f}' y='{nty:.2f}' font-size='{theme.house_num_font_size}' fill='{theme.house_num_color}' font-weight='bold' text-anchor='middle' dominant-baseline='middle'>{label}</text>")

    # Structural circles
    for r in (zodiac_r_outer, zodiac_r_inner, planet_r):
        ap(f'<circle cx="{cx}" cy="{cy}" r="{r:.2f}" fill="none" stroke="{theme.circle_stroke}" stroke-width="{theme.circle_stroke_width}" stroke-opacity="0.9" />')

    # Sign boundary ticks on planet_r (inward)
    tick_r_inner = max(planet_r - theme.tick_length, 0)
    for k in range(12):
        ang = (k * 30 + rot) % 360
        x1, y1 = polar(cx, cy, planet_r, ang)
        x2, y2 = polar(cx, cy, tick_r_inner, ang)
        ap(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{theme.tick_color}" stroke-width="{theme.tick_width}" stroke-linecap="round" stroke-opacity="{theme.tick_opacity}" />')

    # Внутреннее тонкое кольцо и 10° насечки в образованном кольце (planet_r - tick_limb_width .. planet_r)
    limb_r = max(planet_r - theme.tick_limb_width, 0)
    ap(f'<circle cx="{cx}" cy="{cy}" r="{limb_r:.2f}" fill="none" stroke="{theme.circle_stroke}" stroke-width="0.4" stroke-opacity="0.6" />')
    for base_ang in range(0, 360, 10):
        ang = (base_ang + rot) % 360
        x1, y1 = polar(cx, cy, planet_r, ang)
        x2, y2 = polar(cx, cy, limb_r, ang)
        ap(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{theme.tick_color}" stroke-width="0.5" stroke-opacity="0.65" />')


    # Aspects with symbols
    if chart.aspects:
        for aspect in chart.aspects:
            p1 = planet_xy_base.get(aspect.planet1)
            p2 = planet_xy_base.get(aspect.planet2)
            if not p1 or not p2:
                continue
            color = theme.aspect_colors.get(aspect.kind, "#888")
            x1, y1 = p1
            x2, y2 = p2
            ap(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{color}" stroke-width="{theme.aspect_width}" stroke-opacity="0.8" />')
            if theme.show_aspect_symbols and aspect.kind != AspectKind.CONJUNCTION:
                mx = (x1 + x2) / 2
                my = (y1 + y2) / 2
                ap(
                    f'<text x="{mx:.2f}" y="{my:.2f}" font-size="{theme.aspect_symbol_font_size}" text-anchor="middle" dominant-baseline="middle" fill="{color}">{aspect.kind.symbol}</text>'
                )

    # Planet symbols with improved collision avoidance (angular fan + optional radial slight staggering)
    base_symbol_r = min(planet_r + theme.planet_symbol_offset, zodiac_r_inner - theme.planet_font_size * 0.65)
    layout = _layout_planets(chart, base_symbol_r, zodiac_r_inner, theme, rotation=rot)

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
                base_angles = [((pp.longitude + rot) % 360) for pp in planet_positions if pp.planet in comp]
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
                # точки
                sx, sy = polar(cx, cy, arc_r, start_a)
                ex, ey = polar(cx, cy, arc_r, end_a)
                large_arc = 1 if raw_span > 180 else 0
                path = f"M {sx:.2f} {sy:.2f} A {arc_r:.2f} {arc_r:.2f} 0 {large_arc} 0 {ex:.2f} {ey:.2f}"
                ap(f'<path d="{path}" stroke="{theme.conjunction_highlight_color}" stroke-width="{theme.conjunction_arc_stroke_width}" fill="none" stroke-linecap="round" />')
    for pp in planet_positions:
        ang, sr = layout.get(pp.planet, ((pp.longitude + rot) % 360, base_symbol_r))
        sx, sy = polar(cx, cy, sr, ang)
        deg_sub = round(pp.angle_in_sign())
        ap(f'<text x="{sx:.2f}" y="{sy:.2f}" font-size="{theme.planet_font_size}" text-anchor="middle" dominant-baseline="middle" fill="{theme.planet_color}">{pp.planet.symbol}<tspan font-size="{theme.planet_font_size * theme.subscript_scale:.0f}" baseline-shift="sub">{deg_sub}</tspan></text>')
    # Базовые точки планет поверх линий аспектов (перенесено вниз)
    if theme.show_planet_base_points:
        pr = theme.planet_base_point_radius
        for _, (bx, by) in planet_xy_base.items():
            ap(f'<circle cx="{bx:.2f}" cy="{by:.2f}" r="{pr:.2f}" fill="{theme.planet_base_point_fill}" stroke="{theme.planet_base_point_stroke}" stroke-width="{theme.planet_base_point_stroke_width}" />')

    ap('</svg>')
    return "\n".join(out)

def asc_to_angle(chart: Chart, target: float) -> float:
    """Вычисляет угол поворота кольца зодиака, чтобы асцендент (дом 1) оказался на заданном направлении target (в градусах, 0°=3 часа, CCW).

    Возвращает угол в градусах CCW.
    """
    asc_cusp = next((h for h in chart.houses if h.house_number == 1), None)
    if not asc_cusp:
        return 0.0
    asc_angle = asc_cusp.cusp_longitude % 360
    # Нужно повернуть так, чтобы asc_angle оказался на target
    rotation = (target - asc_angle) % 360.0
    return rotation

__all__ = ["SvgTheme", "chart_to_svg", "asc_to_angle"] 
