#! /usr/bin/env python3
import argparse
from dataclasses import dataclass
from datetime import date, datetime
import json
import logging
import os.path
from typing import Optional, Self

import yaml

from .astro import DatetimeLocation, GeoPosition
from .rendering import svg
from .util import CoordError, parse_lat, parse_lon
from .util import parse_time_string, parse_timezone
from .processor import process_data, OutputParams

logger = logging.getLogger(__name__)
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
    # dt = parse_json_datetime(event_data["datetime"])
    # if not "location" in event_data:
    #     raise ValueError("JSON должен содержать поле 'location'")
    # loc = parse_json_location(event_data["location"])
    dt = Datetime.from_dict(event_data["datetime"])
    loc = GeoPosition.from_dict(event_data["location"])
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
    return datetime_from_input(dt_json["date"], dt_json["time"], dt_json["time_zone"])

def datetime_from_input(date_input: str|date, time_str: str, tz_str: str) -> datetime:
    """Разбор строки даты, времени и часового пояса в объект datetime"""
    try:
        if isinstance(date_input, str):
            date = datetime.fromisoformat(date_input).date()
        else:
            date = date_input
    except ValueError as e:
        raise ValueError(f"Неверный формат даты, ожидается ISO 8601 (например, 2025-30-09): {date_input}") from e
    
    time = parse_time_string(time_str)
    tzinfo = parse_timezone(tz_str)
    return datetime.combine(date, time, tzinfo=tzinfo)


def parse_json_location(loc_json: dict) -> GeoPosition:
    """Разбор JSON location в объект GeoPosition"""

    if not "latitude" in loc_json:
        raise ValueError("JSON location должен содержать поле 'latitude'")
    if not "longitude" in loc_json:
        raise ValueError("JSON location должен содержать поле 'longitude'")
    place = loc_json.get("place", None)
    return location_from_str(loc_json["latitude"], loc_json["longitude"], place)


def location_from_str(lat_str: str, lon_str: str, place: str | None = None) -> GeoPosition:
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

    print(f"DEBUG: Parsed location: lat={latitude}, lon={longitude}, place={place}")
    return GeoPosition(latitude=latitude, longitude=longitude, place=place if place else "")


def _init_logging():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger.setLevel(logging.INFO)

@dataclass
class Datetime:
    date: str  # YYYY-MM-DD
    time: str  # HH:MM:SS
    time_zone: str  # e.g. Europe/Moscow or -08:00

    @staticmethod
    def from_dict(data: dict) -> Self:
        date_val = data.get("date")
        time_val = data.get("time")
        time_zone = data.get("time_zone", data.get("tz", data.get("timezone")))
        if not isinstance(date_val, (str, datetime, date)):
            # YAML парсит вход вида 2025-30-09 как datetime.date
            raise ValueError(f"Datetime 'date' must be a string, got {type(date_val)}: {date_val}")
        if not isinstance(time_val, str):
            raise ValueError(f"Datetime 'time' must be a string, got {type(time_val)}: {time_val}")
        if not isinstance(time_zone, str):
            raise ValueError(f"Datetime 'time_zone' must be a string, got {type(time_zone)}: {time_zone}")
        return Datetime(date=date_val, time=time_val, time_zone=time_zone)

    def value(self) -> datetime:
        return datetime_from_input(self.date, self.time, self.time_zone)
    
@dataclass
class Event:
    datetime: Datetime
    location: GeoPosition
    svg_theme: Optional[svg.SvgTheme] = None
    
    @staticmethod
    def from_dict(data: dict) -> Self:
        dt = Datetime.from_dict(data["datetime"])
        loc = GeoPosition.from_dict(data["location"])
        theme = svg.SvgTheme.from_dict(data["svg_theme"]) if "svg_theme" in data else svg.SvgTheme()
        return Event(datetime=dt, location=loc, svg_theme=theme)
    
    def dt_loc(self) -> DatetimeLocation:
        return DatetimeLocation(datetime=self.datetime.value(), location=self.location)
    
@dataclass
class JsonInput:
    name: str
    event: Event
    
    @staticmethod
    def from_dict(data: dict) -> Self:
        if "name" not in data or not isinstance(data["name"], str):
            raise ValueError("JsonInput must have a string 'name' field")
        if "event" not in data or not isinstance(data["event"], dict):
            raise ValueError("JsonInput must have an 'event' field of type object")
        event = Event.from_dict(data["event"])
        return JsonInput(name=data["name"], event=event)
    

def main():
    """
    Главная функция для запуска астрологических расчётов и генерации графики.

    Параметры командной строки:
    usage: pyastro [-h] [-n NAME] [-l LOCATION] [-d DATE] [-t TIME] [-z TIME_ZONE] [-i INPUT_FILE] [-o OUTPUT] [--png] [--svg] [--svg-chart] [--text] [--html] [--pdf] [-P] [-v]

    Астрологические расчёты и графика

    options:
    -h, --help            show this help message and exit
    -v, --verbose         Выводить отладочную информацию (по умолчанию False)

    Параметры натальной карты:
    Задание параметров натальной карты в командной строке

    -n NAME, --name NAME  Имя человека, для которого строится карта
    -l LOCATION, --location LOCATION
                            Местоположение в формате LAT,LON (широта, долгота)
    -d DATE, --date DATE  Дата в формате YYYY-MM-DD
    -t TIME, --time TIME  Время в формате H:M:S
    -z TIME_ZONE, --time-zone TIME_ZONE
                            Часовой пояс в формате Europe/Moscow или смещение от гринвича в формате -08:00

    Параметры входных файлов:
    Задание параметров из входных файлов (пока не реализовано)

    -i INPUT_FILE, --input-file INPUT_FILE
                            Имя входного файла с параметрами (пока не реализовано)

    Параметры выходных файлов:
    Настройка типов выходных файлов

    -o OUTPUT, --output OUTPUT
                            Имя для файлов вывода (без расширения), по умолчанию используется параметр -n
    --png                 Генерировать PNG (по умолчанию False)
    --svg                 Генерировать SVG документ (по умолчанию False)
    --svg-chart           Генерировать SVG диаграмму (по умолчанию False)
    --text                Генерировать Markdown (по умолчанию False)
    --html                Генерировать HTML (по умолчанию False)
    --pdf                 Генерировать PDF (по умолчанию False)
    -P, --no-print        Не выводить текстовую информацию в консоль (по умолчанию False)
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
        "--output-name",
        type=str,
        default="",
        help="Имя для файлов вывода (без расширения), по умолчанию используется параметр -n",
    )
    output_group.add_argument(
        "-D", "--output-dir", type=str, default=os.getcwd(), help="Каталог для файлов вывода",
    )
    output_group.add_argument(
        "--png", action="store_true", help="Генерировать PNG (по умолчанию False)"
    )
    output_group.add_argument(
        "--svg", action="store_true", help="Генерировать SVG документ (по умолчанию False)"
    )
    output_group.add_argument(
        "--svg-chart", action="store_true", help="Генерировать SVG диаграмму (по умолчанию False)"
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
        ext = os.path.basename(args.input_file).rsplit(".", 1)[-1].lower()
        if ext == "json":
            json_file = args.input_file
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    file_data = json.load(f)
            except (ValueError, OSError) as e:
                print(f"Ошибка чтения JSON файла {json_file}: {e}")
                return
        elif ext in ("yaml", "yml"):
            with open(args.input_file, "r", encoding="utf-8") as f:
                file_data = yaml.safe_load(f)
        else:
            print(f"Неизвестный формат входного файла: {ext}")
            exit(1)

        input_value : JsonInput = JsonInput.from_dict(file_data)
        name, dt_loc, svg_theme = input_value.name, input_value.event.dt_loc(), input_value.event.svg_theme
        logger.debug("Разобран файл параметров: name=%s, dt_loc=%s, extra=%s", name, dt_loc, svg_theme)
        output_name = (
                args.output_name
                if args.output_name
                else os.path.basename(args.input_file).rsplit(".", 1)[0]
            )
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
            dt = datetime_from_input(args.date, args.time, args.time_zone)
        except ValueError as e:
            print(f"Ошибка: {e}")
            return

        dt_loc = DatetimeLocation(datetime=dt, location=location)
        output_name = args.output_name if args.output_name else args.name
    
    output_dir = os.path.abspath(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)
    output_name = os.path.join(output_dir, output_name)
    logger.debug("Используется имя для вывода: %s", output_name)
    
    output_params = OutputParams(
        png_path=f"{output_name}.png" if args.png else None,
        svg_chart_path=f"{output_name}_chart.svg" if args.svg_chart else None,
        svg_doc_path=f"{output_name}.svg" if args.svg else None,
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
