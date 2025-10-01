#! /usr/bin/env python3
from datetime import datetime
from zoneinfo import ZoneInfo

from .astro import DatetimeLocation, GeoPosition, Angle, HouseSystem

def main():
    # Пример использования
    dt_loc = DatetimeLocation(
        datetime=datetime(
            2001, 1, 1, 0, 0, 0, tzinfo=ZoneInfo("Europe/Moscow")
        ),  # 1 января 2001 года, полночь по Москве
        location=GeoPosition(latitude=55.7558, longitude=37.6176),  # Москва
    )

    print("Позиции планет:")
    for planet_pos in dt_loc.get_all_planet_positions():
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


if __name__ == "__main__":
    main()
