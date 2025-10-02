#! /usr/bin/env python3
from datetime import datetime
from zoneinfo import ZoneInfo

from pyastro.rendering.svg import Shift, asc_to_angle

from .astro import Chart, DatetimeLocation, GeoPosition, Angle, HouseSystem, Planet
from .rendering import chart_to_svg, SvgTheme

# Helper to convert integer to Unicode subscript digits (0-29)
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
    n = n % 30
    return str(n).translate(_SUB_MAP)


def to_roman(n: int) -> str:
    return _ROMAN.get(n, str(n))


inputs = {
    "Жириновский": DatetimeLocation(
        datetime=datetime(1946, 4, 25, 23, 00, tzinfo=ZoneInfo("Asia/Almaty")),
        location=GeoPosition(latitude=43.2380, longitude=76.8829),  # Алматы
    ),
    "Монро": DatetimeLocation(
        datetime=datetime(1926, 6, 1, 9, 30, tzinfo=ZoneInfo("America/Los_Angeles")),
        location=GeoPosition(latitude=34.0522, longitude=-118.2437),  # Лос-Анджелес
    ),
    "я": DatetimeLocation(
        datetime=datetime(1977, 6, 4, 9, 45, tzinfo=ZoneInfo("Asia/Yekaterinburg")),
        location=GeoPosition(latitude=57.248833, longitude=60.0889),  # Новоуральск
    ),
}

def process_data(dt_loc: DatetimeLocation, name: str = "chart", no_png: bool =True):
    chart = Chart(dt_loc)
    print(f"Дата и время: {dt_loc.datetime.isoformat()}")
    print(
        f"Местоположение: широта={dt_loc.location.latitude}, долгота={dt_loc.location.longitude}\n"
    )
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
    svg = chart_to_svg(
        chart,
        SvgTheme(manual_shifts={Planet.VENUS: Shift(dr=10), Planet.MARS: Shift(dr=-5)}),
        angle=asc_to_angle(chart, 180),
    )
    svg_path = f"{name}.svg"
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"\nSVG сохранён в {svg_path}")

    # Генерация PNG из SVG
    if not no_png:
        png_path = f"{name}.png"
        try:
            import cairosvg  # type: ignore
        except ImportError as e:  # pragma: no cover
            print(f"Не установлен cairosvg, пропуск PNG: {e}")
        else:
            try:
                cairosvg.svg2png(
                    bytestring=svg.encode("utf-8"),
                    write_to=png_path,
                    output_width=1600,
                    output_height=1600,
                )
                print(f"PNG сохранён в {png_path}")
            except (ValueError, OSError) as e:  # pragma: no cover
                print(f"Ошибка конвертации PNG: {e}")
            
def main():
    """
    Главная функция для запуска астрологических расчётов и генерации графики.
    
    Параметры командной строки:
    -n --name NAME - имя. Нужно сгенерировать вывод NAME.svg, NAME.png (потом добавятся другие виды выводов)
    -l --location местоположение в формате LAT,LON где LAT широта, float, LON долгота float
    -d --date дата в формате YYYY-MM-DD
    -t --time время в формате H:M:S 
    -z --time-zone часовй пояс в формате Europe/Moscow ЛИБО смещение от гринвича в формате -08:00
    --png генерировать PNG, по умолчанию False
    """
    import argparse
    parser = argparse.ArgumentParser(description="Астрологические расчёты и графика")
    parser.add_argument("-n", "--name", type=str, required=True, help="Имя для файлов вывода (без расширения)")
    parser.add_argument("-l", "--location", type=str, required=True, help="Местоположение в формате LAT,LON (широта, долгота)")
    parser.add_argument("-d", "--date", type=str, required=True, help="Дата в формате YYYY-MM-DD")
    parser.add_argument("-t", "--time", type=str, required=True, help="Время в формате H:M:S")
    parser.add_argument("-z", "--time-zone", type=str, required=True, help="Часовой пояс в формате Europe/Moscow или смещение от гринвича в формате -08:00")
    parser.add_argument("--png", action="store_true", help="Генерировать PNG (по умолчанию False)")
    args = parser.parse_args()
    
    try:
        lat_str, lon_str = args.location.split(",")
    except ValueError:
        print(f"Ошибка: местоположение должно быть в формате LAT,LON: {args.location}")
        return
    try:
        latitude = float(lat_str)
        longitude = float(lon_str)
    except ValueError:
        print(f"Ошибка: широта и долгота должны быть числами с плавающей точкой: {lat_str}, {lon_str}")
        return
    try:
        date = datetime.strptime(args.date, "%Y-%m-%d").date()
    except ValueError:
        print(f"Ошибка: дата должна быть в формате YYYY-MM-DD: {args.date}")
        return
    try:
        time = datetime.strptime(args.time, "%H:%M:%S").time()
    except ValueError:
        print(f"Ошибка: время должно быть в формате H:M:S: {args.time}")
        return
    try:
        if args.time_zone.startswith(("+", "-")):
            hours_offset, minutes_offset = map(int, args.time_zone.split(":"))
            tzinfo = ZoneInfo(f"Etc/GMT{'+' if hours_offset < 0 else '-'}{abs(hours_offset)}")
        else:
            tzinfo = ZoneInfo(args.time_zone)
    except Exception as e:
        print(f"Ошибка: неверный часовой пояс: {args.time_zone}: {e}")
        return
    
    dt = datetime.combine(date, time, tzinfo=tzinfo)
    location = GeoPosition(latitude=latitude, longitude=longitude)
    dt_loc = DatetimeLocation(datetime=dt, location=location)
    process_data(dt_loc, name=args.name, no_png=not args.png)
    
def main0():
    # Пример использования
    # dt_loc = DatetimeLocation(
    #     datetime=datetime(
    #         2001, 1, 1, 0, 0, 0, tzinfo=ZoneInfo("Europe/Moscow")
    #     ),  # 1 января 2001 года, полночь по Москве
    #     location=GeoPosition(latitude=55.75, longitude=37.35),  # Москва
    # )

    # dt_loc = DatetimeLocation(
    #     datetime=datetime(
    #         1977, 6, 6, 9, 45, 0, tzinfo=ZoneInfo("Asia/Yekaterinburg")
    #     ),
    #     location=GeoPosition(latitude=57.248833, longitude=60.112745),  # Новоуральск
    # )
    #
    # dt_loc = inputs["Жириновский"]
    # dt_loc = inputs["Монро"]
    dt_loc = inputs["я"]
    process_data(dt_loc, name="я", no_png=False)


if __name__ == "__main__":
    main()
