
import datetime
import zoneinfo

_strptime = datetime.datetime.strptime

_formats = {
    "%H:%M:%S" : "13:30:15",
    "%H:%M" : "13:30",
    "%H" : "13",
    "%I:%M:%S %p" : "1:30:15 PM",
    "%I:%M %p" : "1:30 PM",
    "%I %p" : "1 PM"
}

def _parse_time_format(s : str, fmt: str) -> datetime.time | None:
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
    raise ValueError(f"Неверный формат времени, ожидается один из: {', '.join(_formats.values())}: {s}")



def parse_timezone(tz_str: str) -> zoneinfo.ZoneInfo:
    """Разбор строки часового пояса в объект ZoneInfo.
    
    Поддерживаются два формата:
    - Часовой пояс в формате IANA, например Europe/Moscow
    - Часовой пояс в формате смещения, например +03:00 или -05:00
    """
    try:
        if tz_str.startswith(("+", "-")):
            hours_offset, minutes_offset = map(int, tz_str.split(":"))
            tzinfo = datetime.timezone(
                offset=datetime.timedelta(hours=hours_offset, minutes=minutes_offset),
                name=f"GMT{'+' if hours_offset > 0 else '-'}{abs(hours_offset):02d}:{minutes_offset:02d}",
            )
        else:
            tzinfo = zoneinfo.ZoneInfo(tz_str)
    except Exception as e:
        raise ValueError(f"Неверный часовой пояс: {tz_str}: {e}") from e
    return tzinfo
