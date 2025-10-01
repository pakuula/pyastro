#! /usr/bin/env python3
from datetime import datetime
from zoneinfo import ZoneInfo

from .astro import Chart, DatetimeLocation, GeoPosition, Angle, HouseSystem
from .rendering import chart_to_svg, SvgTheme

# Helper to convert integer to Unicode subscript digits (0-29)
_SUB_MAP = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")

_ROMAN = {
    1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI",
    7: "VII", 8: "VIII", 9: "IX", 10: "X", 11: "XI", 12: "XII"
}

def int_to_subscript(n: int) -> str:
    n = n % 30
    return str(n).translate(_SUB_MAP)

def to_roman(n: int) -> str:
    return _ROMAN.get(n, str(n))


def main():
    # Пример использования
    dt_loc = DatetimeLocation(
        datetime=datetime(
            2001, 1, 1, 0, 0, 0, tzinfo=ZoneInfo("Europe/Moscow")
        ),  # 1 января 2001 года, полночь по Москве
        location=GeoPosition(latitude=55.75, longitude=37.35),  # Москва
    )

    chart = Chart(dt_loc)
    print(f"Дата и время: {dt_loc.datetime.isoformat()}")
    print(f"Местоположение: широта={dt_loc.location.latitude}, долгота={dt_loc.location.longitude}\n")
    print("Позиции планет:")
    for planet_pos in chart.planet_positions:
        deg_sub = int_to_subscript(round(planet_pos.angle_in_sign()))
        print(
            f"{planet_pos.planet.name:10s}: "
            f"{planet_pos.planet.symbol}{deg_sub} "
            f"Долгота={Angle.Lon(planet_pos.longitude)}, "
            f"Широта={Angle.Lat(planet_pos.latitude)}, "
            f"знак={planet_pos.zodiac_sign.name}, "
            f"угол в знаке={Angle(planet_pos.angle_in_sign())}, "
            f"Ретроградность={'Да' if planet_pos.is_retrograde() else 'Нет'}"
        )

    print("\nКуспиды домов (Placidus):")
    for house_cusp in dt_loc.get_house_cusps(HouseSystem.PLACIDUS):
        deg_sub = int_to_subscript(round(house_cusp.angle_in_sign))
        roman = to_roman(house_cusp.house_number)
        print(
            f"Дом {roman}{deg_sub}:"
            f" Куспид={Angle(house_cusp.cusp_longitude)}, "
            f"Длина={Angle(house_cusp.length)}, "
            f"Знак={house_cusp.zodiac_sign.symbol}, "
            f"Угол={Angle(house_cusp.angle_in_sign)}"
        )

    print("\nАспекты между планетами:")
    for aspect in chart.aspects:
        print(
            f"{aspect.planet1.name} {aspect.planet1.symbol} - "
            f"{aspect.planet2.name} {aspect.planet2.symbol}: "
            f"{aspect.kind.name} {aspect.kind.symbol} {Angle(aspect.angle)} "
            f"(oрб: {Angle(aspect.orb)})"
        )

    # Экспортируем SVG
    svg = chart_to_svg(chart, SvgTheme())
    svg_path = "chart.svg"
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"\nSVG сохранён в {svg_path}")

    # Генерация PNG из SVG
    png_path = "chart.png"
    try:
        import cairosvg  # type: ignore
    except ImportError as e:  # pragma: no cover
        print(f"Не установлен cairosvg, пропуск PNG: {e}")
    else:
        try:
            cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=png_path, output_width=1600, output_height=1600)
            print(f"PNG сохранён в {png_path}")
        except (ValueError, OSError) as e:  # pragma: no cover
            print(f"Ошибка конвертации PNG: {e}")


if __name__ == "__main__":
    main()
