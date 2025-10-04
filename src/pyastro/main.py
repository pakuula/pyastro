#! /usr/bin/env python3
import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import logging
import os.path
from tempfile import NamedTemporaryFile
from typing import Optional, Self
from zoneinfo import ZoneInfo

from .rendering import svg, markdown, html, pdf

from .astro import Chart, DatetimeLocation, GeoPosition, HouseSystem
from .util import CoordError, parse_lat, parse_lon, Angle

logger = logging.getLogger(__name__)

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


def print_chart_info(chart: Chart):
    print(f"Астрологическая карта для: {chart.name}")
    dt_loc = chart.dt_loc
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
    for house_cusp in chart.dt_loc.get_house_cusps(HouseSystem.PLACIDUS):
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


@dataclass
class OutputParams:
    png_path: Optional[str] = None
    svg_path: Optional[str] = None
    mdown_path: Optional[str] = None
    html_path: Optional[str] = None
    pdf_path: Optional[str] = None
    print_flag: bool = True


def process_data(
    person_name: str,
    dt_loc: DatetimeLocation,
    output_params: OutputParams,
    svg_theme: Optional[svg.SvgTheme] = None,
):
    """Генерация астрологической карты и вывод отчётов в разные форматы."""
    chart = Chart(person_name, dt_loc)

    if output_params.print_flag:
        print_chart_info(chart)

    svg_chart = svg.chart_to_svg(
        chart,
        svg_theme or svg.SvgTheme(),
        angle=svg.asc_to_angle(chart, 180),
    )
    logger.debug("Output params: %s", output_params)
    if output_params.svg_path:
        with open(output_params.svg_path, "w", encoding="utf-8") as f:
            f.write(svg_chart)
        logger.info("SVG сохранён в %s", output_params.svg_path)
    if output_params.mdown_path:
        mdown_path = output_params.mdown_path
        svg_path = output_params.mdown_path.rsplit(".", 1)[0] + ".svg"
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg_chart)
            logger.debug("SVG для markdown сохранён в %s", svg_path)
        with open(mdown_path, "w", encoding="utf-8") as f:
            mdown = markdown.to_markdown(chart, svg_path=os.path.basename(svg_path))
            f.write(mdown)
        logger.info("Markdown сохранён в %s", output_params.mdown_path)
    if output_params.pdf_path:
        with NamedTemporaryFile(
            delete=True, suffix=".svg"
        ) as tmp_svg_file, NamedTemporaryFile(delete=True, suffix=".md") as tmp_md_file:
            tmp_svg_file.write(svg_chart.encode("utf-8"))
            tmp_svg_file.flush()
            # tmp_svg_file.close()

            mdown = markdown.to_markdown(chart, svg_path=tmp_svg_file.name)
            tmp_md_file.write(mdown.encode("utf-8"))
            tmp_md_file.flush()
            # tmp_md_file.close()

            pdf.to_pdf(tmp_md_file.name, output_params.pdf_path)
        # pdf.to_pdf_weasy(chart, svg_chart, output_params.pdf_path)
        logger.info("PDF сохранён в %s", output_params.pdf_path)
    if output_params.html_path:
        html_doc = html.to_html(chart, svg_chart=svg_chart)
        with open(output_params.html_path, "w", encoding="utf-8") as f:
            f.write(html_doc)
        logger.info("HTML сохранён в %s", output_params.html_path)
    if output_params.png_path:
        try:
            import cairosvg  # type: ignore
        except ImportError as e:  # pragma: no cover
            logging.error("Не установлен cairosvg, пропуск PNG: %s", e)
        else:
            try:
                cairosvg.svg2png(
                    bytestring=svg_chart.encode("utf-8"),
                    write_to=output_params.png_path,
                    output_width=1600,
                    output_height=1600,
                )
                logger.info("PNG сохранён в %s", output_params.png_path)
            except (ValueError, OSError) as e:  # pragma: no cover
                logging.error("Ошибка конвертации PNG: %s", e)


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
    extra = {k: v for k, v in json_data.items() if k not in ("name", "event")}
    extra.update({k: v for k, v in event_data.items() if k not in ("datetime", "location")})
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
            raise ValueError(f"Неверный формат широты: {lat_str}") from e
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
            raise ValueError(f"Неверный формат долготы: {lon_str}") from e
    elif isinstance(lon_str, (int, float)):
        longitude = float(lon_str)
        if not (-180.0 <= longitude <= 180.0):
            raise ValueError(f"Долгота вне диапазона [-180, 180]: {longitude}")
    else:
        raise ValueError(f"Неверный тип долготы: {type(lon_str)}")

    return GeoPosition(latitude=latitude, longitude=longitude)


def _init_logging():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger.setLevel(logging.INFO)

@dataclass
class Datetime:
    date: str  # YYYY-MM-DD
    time: str  # HH:MM:SS
    time_zone: str  # e.g. Europe/Moscow or -08:00

    @staticmethod
    def from_json(data: dict) -> Self:
        date = data.get("date")
        time = data.get("time")
        time_zone = data.get("time_zone")
        if not isinstance(date, str):
            raise ValueError("Datetime 'date' must be a string")
        if not isinstance(time, str):
            raise ValueError("Datetime 'time' must be a string")
        if not isinstance(time_zone, str):
            raise ValueError("Datetime 'time_zone' must be a string")
        return Datetime(date=date, time=time, time_zone=time_zone)

    def value(self) -> datetime:
        return datetime_from_str(self.date, self.time, self.time_zone)
    
@dataclass
class Event:
    datetime: Datetime
    location: GeoPosition
    svg_theme: Optional[svg.SvgTheme] = None
    
    @staticmethod
    def from_json(data: dict) -> Self:
        dt = Datetime.from_json(data["datetime"])
        loc = GeoPosition.from_json(data["location"])
        theme = svg.SvgTheme.from_json(data["svg_theme"]) if "svg_theme" in data else svg.SvgTheme()
        return Event(datetime=dt, location=loc, svg_theme=theme)
    
    def dt_loc(self) -> DatetimeLocation:
        print(f"DEBUG: Event.dt_loc: datetime={self.datetime}, location={self.location}")
        return DatetimeLocation(datetime=self.datetime.value(), location=self.location)
    
@dataclass
class JsonInput:
    name: str
    event: Event
    
    @staticmethod
    def from_json(data: dict) -> Self:
        if "name" not in data or not isinstance(data["name"], str):
            raise ValueError("JsonInput must have a string 'name' field")
        if "event" not in data or not isinstance(data["event"], dict):
            raise ValueError("JsonInput must have an 'event' field of type object")
        event = Event.from_json(data["event"])
        return JsonInput(name=data["name"], event=event)
    

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
    _init_logging()
    parser = argparse.ArgumentParser(description="Астрологические расчёты и графика")

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

    output_group = parser.add_argument_group(
        "Параметры выходных файлов", "Настройка типов выходных файлов"
    )
    output_group.add_argument(
        "-o",
        "--output",
        type=str,
        default="",
        help="Имя для файлов вывода (без расширения), по умолчанию используется параметр -n",
    )
    output_group.add_argument(
        "--png", action="store_true", help="Генерировать PNG (по умолчанию False)"
    )
    output_group.add_argument(
        "--svg", action="store_true", help="Генерировать SVG (по умолчанию False)"
    )
    output_group.add_argument(
        "--text", action="store_true", help="Генерировать Markdown (по умолчанию False)"
    )
    output_group.add_argument(
        "--html", action="store_true", help="Генерировать HTML (по умолчанию False)"
    )
    output_group.add_argument(
        "--pdf", action="store_true", help="Генерировать PDF (по умолчанию False)"
    )
    output_group.add_argument(
        "-P",
        "--no-print",
        action="store_true",
        help="Не выводить текстовую информацию в консоль (по умолчанию False)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Выводить отладочную информацию (по умолчанию False)",
    )

    args = parser.parse_args()
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Включён подробный вывод")
    svg_theme = None

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
        input_value : JsonInput = JsonInput.from_json(json_data)
        name, dt_loc, svg_theme = input_value.name, input_value.event.dt_loc(), input_value.event.svg_theme
        # name, dt_loc, extra = parse_json_input(json_data)
        output_name = (
            args.output
            if args.output
            else os.path.basename(json_file).rsplit(".", 1)[0]
        )
        logger.debug("Разобран JSON: name=%s, dt_loc=%s, extra=%s", name, dt_loc, svg_theme)
        # if "svg_theme" in extra:
        #     logging.debug("Разбор темы SVG из JSON")
        #     try:
        #         svg_theme = svg.SvgTheme.from_json(extra["svg_theme"])
        #     except ValueError as e:
        #         print(f"Ошибка разбора темы SVG из JSON: {e}")
        #         return
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

    output_params = OutputParams(
        png_path=f"{output_name}.png" if args.png else None,
        svg_path=f"{output_name}.svg" if args.svg else None,
        mdown_path=f"{output_name}.md" if args.text else None,
        html_path=f"{output_name}.html" if args.html else None,
        pdf_path=f"{output_name}.pdf" if args.pdf else None,
        print_flag=not args.no_print,
    )

    process_data(
        person_name=name,
        dt_loc=dt_loc,
        output_params=output_params,
        svg_theme=svg_theme,
    )


if __name__ == "__main__":

    logger.error("Запуск pyastro")
    main()
