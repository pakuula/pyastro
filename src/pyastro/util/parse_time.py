"""Утилиты для разбора времени, даты и часовых поясов."""

import datetime
import zoneinfo


_strptime = datetime.datetime.strptime

_formats = {
    "%H:%M:%S": "13:30:15",
    "%H:%M": "13:30",
    "%H": "13",
    "%I:%M:%S %p": "1:30:15 PM",
    "%I:%M %p": "1:30 PM",
    "%I %p": "1 PM",
}


def _parse_time_format(s: str, fmt: str) -> datetime.time | None:
    try:
        t = _strptime(s, fmt).time()
        return t
    except ValueError:
        return None


def parse_time_string(s: str) -> datetime.time:
    """Разбор строки времени в объект time.

    Поддерживаются следующие форматы (в указанном порядке):
    - Часы, минуты и секунды в 12-часовом формате с AM/PM: 1:30:15 PM
    - Часы и минуты в 12-часовом формате с AM/PM: 1:30 PM
    - Только часы в 12-часовом формате с AM/PM: 1 PM
    - Часы, минуты и секунды: 13:30:15
    - Часы и минуты: 13:30
    - Только часы: 13
    """
    for fmt in _formats:
        t = _parse_time_format(s, fmt)
        if t is not None:
            return t
    raise ValueError(
        f"Неверный формат времени, ожидается один из: {', '.join(_formats.values())}: {s}"
    )


def parse_timezone(tz_str: str) -> zoneinfo.ZoneInfo | datetime.timezone:
    """Разбор строки часового пояса в объект ZoneInfo.

    Поддерживаются два формата:
    - Часовой пояс в формате IANA, например Europe/Moscow
    - Часовой пояс в формате смещения, например +03:00 или -05:00
    """
    try:
        if tz_str.startswith(("+", "-")):
            hours_offset, minutes_offset = map(int, tz_str.split(":"))
            sign = 1 if hours_offset >= 0 else -1
            tzinfo = datetime.timezone(
                offset=datetime.timedelta(
                    hours=hours_offset, minutes=sign * minutes_offset
                ),
                name=f"GMT{'+' if hours_offset > 0 else '-'}{abs(hours_offset):02d}:{minutes_offset:02d}",
            )
        else:
            tzinfo = zoneinfo.ZoneInfo(tz_str)
    except Exception as e:
        raise ValueError(f"Неверный часовой пояс: {tz_str}: {e}") from e
    return tzinfo


def datetime_from_dict(data: dict) -> datetime.datetime:
    """Разбор JSON datetime в объект datetime"""
    date_str = data.get("date")
    time_str = data.get("time")
    tz_str = data.get(
        "time_zone", data.get("timezone", data.get("tz", None))
    )  # поддержка всех вариантов
    if date_str is None:
        raise ValueError("Объект datetime должен содержать поле 'date'")
    if time_str is None:
        raise ValueError("Объект datetime должен содержать поле 'time'")
    if tz_str is None:
        raise ValueError(
            "Объект datetime должен содержать поле 'time_zone', 'timezone' или 'tz'"
        )
    return _datetime_from_input(data["date"], data["time"], data["time_zone"])


def _datetime_from_input(
    date_input: str | datetime.date, time_str: str, tz_str: str
) -> datetime.datetime:
    """Разбор строки даты, времени и часового пояса в объект datetime"""
    try:
        if isinstance(date_input, str):
            date = datetime.datetime.fromisoformat(date_input).date()
        else:
            date = date_input
    except ValueError as e:
        raise ValueError(
            f"Неверный формат даты, ожидается ISO 8601 (например, 2025-30-09): {date_input}"
        ) from e
    if isinstance(time_str, str):
        time = parse_time_string(time_str)
    elif isinstance(time_str, datetime.time):  # тот же тип, что и time_module.time
        time = time_str
    else:
        raise ValueError(f"Неверный формат времени: {time_str} (type {type(time_str)})")

    tzinfo = parse_timezone(tz_str)
    return datetime.datetime.combine(date, time, tzinfo=tzinfo)
