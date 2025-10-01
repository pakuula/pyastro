#! /usr/bin/env python3
from datetime import datetime
from zoneinfo import ZoneInfo

from .astro import Chart, DatetimeLocation, GeoPosition, Angle, HouseSystem

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
        print(
            f"{planet_pos.planet.name:10s}: "
            f"Долгота={Angle.Lon(planet_pos.longitude)}, "
            f"Широта={Angle.Lat(planet_pos.latitude)}, "
            f"знак={planet_pos.zodiac_sign.name}, "
            f"угол в знаке={Angle(planet_pos.angle_in_sign())}, "
            f"Ретроградность={'Да' if planet_pos.is_retrograde() else 'Нет'}"
        )

    print("\nКуспиды домов (Placidus):")
    for house_cusp in dt_loc.get_house_cusps(HouseSystem.PLACIDUS):
        print(
            f"Дом {house_cusp.house_number}:"
            f"Куспид={Angle(house_cusp.cusp_longitude)}, "
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
if __name__ == "__main__":
    main()
