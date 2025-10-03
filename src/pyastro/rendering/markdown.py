"""Модуль для генерации markdown отчётов по астрологическим картам"""

from pyastro.astro import Chart
from pyastro.util import Angle, Latitude, Longitude


def to_markdown(chart: Chart, svg_path: str) -> str:
    """Генерация markdown отчёта по гороскопу"""
    out = bytearray()

    def write(s: str):
        out.extend(s.encode("utf-8"))

    def writeln(*lines: str):
        if not lines:
            out.extend(b"\n")
        else:
            for line in lines:
                write(line)
                out.extend(b"\n")

    def para(*lines: str):
        for line in lines:
            writeln(line)
        writeln()

    para("# Астрологическая карта")
    para(
        f"- Имя: {chart.name}",
        f"- Дата и время: {chart.dt_loc.datetime.strftime('%Y-%m-%d %H:%M:%S')} ({chart.dt_loc.datetime.tzinfo})",
        f"- Местоположение: {Latitude(chart.dt_loc.location.latitude)} {Longitude(chart.dt_loc.location.longitude)}",
    )
    if svg_path:
        para(f"![Карта гороскопа]({svg_path})")
    
    para("## Позиции планет")

    headers = [
        # "Планета",
        "Символ",
        "Долгота",
        "Широта",
        "Знак",
        "Угол в знаке",
        "Ретроградность",
        "Дом",
    ]
    writeln("| " + " | ".join(headers) + " |")
    writeln("|" + "|".join(["---"] * len(headers)) + "|")

    for planet_pos in chart.planet_positions:
        
        planet_data = [
            # f"{planet_pos.planet.name}",
            f"{planet_pos.planet.symbol}",
            f"{Angle.Lon(planet_pos.longitude)}",
            f"{Angle.Lat(planet_pos.latitude)}",
            f"{planet_pos.zodiac_sign.symbol}",
            f"{Angle(planet_pos.angle_in_sign())}",
            "Да" if planet_pos.is_retrograde() else "Нет",
            f"{chart.planet_houses[planet_pos.planet].roman_number}",
        ]
        writeln("| " + " | ".join(planet_data) + " |")

    writeln()

    para("## Аспекты")
    headers = ["Планета 1", "Планета 2", "Аспект", "Угол", "Орбис"]
    writeln("| " + " | ".join(headers) + " |")
    writeln("|" + "|".join(["---"] * len(headers)) + "|")

    for aspect in chart.aspects:
        aspect_data = [
            f"{aspect.planet1.symbol}",
            f"{aspect.planet2.symbol}",
            f"{aspect.kind.name}",
            f"{Angle(aspect.angle)}",
            f"{Angle(aspect.orb)}",
        ]
        writeln("| " + " | ".join(aspect_data) + " |")

    para("## Дома по системе Плацидус")
    headers = ["Дом", "Куспид", "Длина", "Знак", "Угол в знаке", "Планеты"]
    writeln("| " + " | ".join(headers) + " |")
    writeln("|" + "|".join(["---"] * len(headers)) + "|")

    for house in chart.houses:
        house_data = [
            f"{house.roman_number}",
            f"{Angle.Lon(house.cusp_longitude)}",
            f"{Angle(house.length)}",
            f"{house.zodiac_sign.symbol}",
            f"{Angle(house.angle_in_sign)}",
            " ".join(p.symbol for p in chart.house_planets.get(house.house_number, [])) or " ",
        ]
        writeln("| " + " | ".join(house_data) + " |")

    writeln()

    return out.decode("utf-8")
