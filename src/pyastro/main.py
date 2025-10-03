#! /usr/bin/env python3
import argparse
from datetime import datetime, timedelta, timezone
import json
import os.path
from zoneinfo import ZoneInfo

from pyastro.rendering import pdf
from pyastro.rendering.markdown import to_markdown
from pyastro.rendering.svg import Shift, asc_to_angle

from .astro import Chart, DatetimeLocation, GeoPosition, Angle, HouseSystem, Planet
from .rendering import chart_to_svg, SvgTheme
from .util import CoordError, parse_lat, parse_lon

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


def process_data(
    person_name: str,
    dt_loc: DatetimeLocation,
    output_name: str = "chart",
    no_png: bool = True,
):
    chart = Chart(person_name, dt_loc)
    print(f"Астрологическая карта для: {person_name}")
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
            f"знак={planet_pos.zodiac_sign.symbol}, "
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
    svg_path = f"{output_name}.svg"
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"\nSVG сохранён в {svg_path}")

    # Генерация PNG из SVG
    if not no_png:
        png_path = f"{output_name}.png"
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
    mdown = to_markdown(chart, svg_path)
    mdown_path = f"{output_name}.md"
    with open(mdown_path, "w", encoding="utf-8") as f:
        f.write(mdown)
    print(f"Markdown сохранён в {mdown_path}")

    pdf.to_pdf(mdown_path, f"{output_name}.pdf")


def parse_json_input(json_data: dict) -> tuple[str, DatetimeLocation, dict]:
    """Разбор JSON входных данных в кортеж (имя, DatetimeLocation, доп. данные)"""

    if not "name" in json_data:
        raise ValueError("JSON должен содержать поле 'name'")
    name = json_data["name"]
    if not isinstance(name, str):
        raise ValueError("JSON поле 'name' должно быть строкой")
    if not "event" in json_data:
        raise ValueError("JSON должен содержать поле 'event'")
    event_data = json_data["event"]
    if not isinstance(event_data, dict):
        raise ValueError("JSON поле 'event' должно быть объектом")
    if not "datetime" in event_data:
        raise ValueError("JSON должен содержать поле 'datetime'")
    dt = parse_json_datetime(event_data["datetime"])
    if not "location" in event_data:
        raise ValueError("JSON должен содержать поле 'location'")
    loc = parse_json_location(event_data["location"])
    extra = {
        k: v for k, v in json_data.items() if k not in ("name", "event")
    }
    return name, DatetimeLocation(datetime=dt, location=loc), extra


def parse_json_datetime(dt_json: dict) -> datetime:
    """Разбор JSON datetime в объект datetime"""

    if not "date" in dt_json:
        raise ValueError("JSON datetime должен содержать поле 'date'")
    if not "time" in dt_json:
        raise ValueError("JSON datetime должен содержать поле 'time'")
    if not "time_zone" in dt_json:
        raise ValueError("JSON datetime должен содержать поле 'tz'")
    return datetime_from_str(dt_json["date"], dt_json["time"], dt_json["time_zone"])


def datetime_from_str(date_str: str, time_str: str, tz_str: str) -> datetime:
    """Разбор строки даты, времени и часового пояса в объект datetime"""
    try:
        date = datetime.fromisoformat(date_str).date()
    except ValueError as e:
        raise ValueError(f"Неверный формат даты, ожидается ISO 8601: {date_str}") from e
    try:
        time = datetime.strptime(time_str, "%H:%M:%S").time()
    except ValueError as e:
        raise ValueError(
            f"Неверный формат времени, ожидается ISO 8601: {time_str}"
        ) from e
    try:
        if tz_str.startswith(("+", "-")):
            hours_offset, minutes_offset = map(int, tz_str.split(":"))
            tzinfo = timezone(
                offset=timedelta(hours=hours_offset, minutes=minutes_offset),
                name=f"GMT{'+' if hours_offset > 0 else '-'}{abs(hours_offset):02d}:{minutes_offset:02d}",
            )
        else:
            tzinfo = ZoneInfo(tz_str)
    except Exception as e:
        raise ValueError(f"Неверный часовой пояс: {tz_str}: {e}") from e
    return datetime.combine(date, time, tzinfo=tzinfo)


def parse_json_location(loc_json: dict) -> GeoPosition:
    """Разбор JSON location в объект GeoPosition"""

    if not "latitude" in loc_json:
        raise ValueError("JSON location должен содержать поле 'latitude'")
    if not "longitude" in loc_json:
        raise ValueError("JSON location должен содержать поле 'longitude'")
    return location_from_str(loc_json["latitude"], loc_json["longitude"])


def location_from_str(lat_str: str, lon_str: str) -> GeoPosition:
    """Разбор строки широты и долготы в объект GeoPosition.
    
    Возможные форматы:
    - число с плавающей точкой, например 55.7558, -37.6173
    """
    if isinstance(lat_str, str):
        try:
            latitude = parse_lat(lat_str)
        except CoordError as e:
            raise ValueError(
                f"Неверный формат широты: {lat_str}"
            ) from e
    elif isinstance(lat_str, (int, float)):
        latitude = float(lat_str)
        if not (-90.0 <= latitude <= 90.0):
            raise ValueError(f"Широта вне диапазона [-90, 90]: {latitude}")
    else:
        raise ValueError(f"Неверный тип широты: {type(lat_str)}")

    if isinstance(lon_str, str):
        try:
            longitude = parse_lon(lon_str)
        except CoordError as e:
            raise ValueError(
                f"Неверный формат долготы: {lon_str}"
            ) from e
    elif isinstance(lon_str, (int, float)):
        longitude = float(lon_str)
        if not (-180.0 <= longitude <= 180.0):
            raise ValueError(f"Долгота вне диапазона [-180, 180]: {longitude}")
    else:
        raise ValueError(f"Неверный тип долготы: {type(lon_str)}")

    return GeoPosition(latitude=latitude, longitude=longitude)


def main():
    """
    Главная функция для запуска астрологических расчётов и генерации графики.

    Параметры командной строки:
    -n --name NAME - имя. Нужно сгенерировать вывод NAME.svg, NAME.png (потом добавятся другие виды выводов)
    -l --location местоположение в формате LAT,LON где LAT широта, float, LON долгота float
    -d --date дата в формате YYYY-MM-DD
    -t --time время в формате H:M:S
    -z --time-zone часовй пояс в формате Europe/Moscow ЛИБО смещение от гринвича в формате -08:00
    -o --output имя для файлов вывода (без расширения), по умолчанию используется параметр -n
    --png генерировать PNG, по умолчанию False
    """
    parser = argparse.ArgumentParser(description="Астрологические расчёты и графика")
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="",
        help="Имя для файлов вывода (без расширения), по умолчанию используется параметр -n",
    )
    parser.add_argument(
        "--png", action="store_true", help="Генерировать PNG (по умолчанию False)"
    )

    direct_args = parser.add_argument_group(
        "Параметры натальной карты",
        "Задание параметров натальной карты в командной строке",
    )
    direct_args.add_argument(
        "-n",
        "--name",
        type=str,
        required=False,
        help="Имя человека, для которого строится карта",
    )
    direct_args.add_argument(
        "-l",
        "--location",
        type=str,
        required=False,
        help="Местоположение в формате LAT,LON (широта, долгота)",
    )
    direct_args.add_argument(
        "-d", "--date", type=str, required=False, help="Дата в формате YYYY-MM-DD"
    )
    direct_args.add_argument(
        "-t", "--time", type=str, required=False, help="Время в формате H:M:S"
    )
    direct_args.add_argument(
        "-z",
        "--time-zone",
        type=str,
        required=False,
        help="Часовой пояс в формате Europe/Moscow или смещение от гринвича в формате -08:00",
    )

    file_args = parser.add_argument_group(
        "Параметры входных файлов",
        "Задание параметров из входных файлов (пока не реализовано)",
    )
    file_args.add_argument(
        "-i",
        "--input-file",
        type=str,
        help="Имя входного файла с параметрами (пока не реализовано)",
    )

    args = parser.parse_args()

    if not args.name and not args.input_file:
        print("Ошибка: нужно указать имя человека (-n) или входной файл (-i)")
        return
    if args.name:
        if not args.location or not args.date or not args.time or not args.time_zone:
            print(
                "Ошибка: при указании имени (-n) нужно также указать местоположение (-l), дату (-d), время (-t) и часовой пояс (-z)"
            )
            return

    if args.input_file:
        json_file = args.input_file
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                json_data = json.load(f)
        except (ValueError, OSError) as e:
            print(f"Ошибка чтения JSON файла {json_file}: {e}")
            return
        name, dt_loc, _ = parse_json_input(json_data)
        output_name = args.output if args.output else os.path.basename(json_file).rsplit(".", 1)[0]
    else:
        name = args.name
        try:
            lat_str, lon_str = args.location.split(",")
        except ValueError:
            print(
                f"Ошибка: местоположение должно быть в формате LAT,LON: {args.location}"
            )
            return
        try:
            location = location_from_str(lat_str, lon_str)
            dt = datetime_from_str(args.date, args.time, args.time_zone)
        except ValueError as e:
            print(f"Ошибка: {e}")
            return

        dt_loc = DatetimeLocation(datetime=dt, location=location)
        output_name = args.output if args.output else args.name
        
    process_data(
        person_name=name, dt_loc=dt_loc, output_name=output_name, no_png=not args.png
    )


if __name__ == "__main__":
    main()
