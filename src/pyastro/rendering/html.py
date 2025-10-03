"""Модуль для генерации HTML отчётов по астрологическим картам"""

from typing import Optional
from pyastro.astro import Chart
from pyastro.rendering import svg
from pyastro.util import Angle, Latitude, Longitude


def to_html(chart: Chart, svg_chart: Optional[str] = None, svg_path: Optional[str] = None) -> str:
    """Генерация HTML отчёта по гороскопу"""
    out = []

    def writeln(*lines: str):
        if not lines:
            out.append("")
        else:
            for line in lines:
                out.append(line)
    if not svg_chart and svg_path:
        try:
            with open(svg_path, 'r', encoding='utf-8') as svg_file:
                svg_chart = svg_file.read()
        except (FileNotFoundError, IOError):
            svg_chart = f'<p style="color: red;">Ошибка: не удалось загрузить SVG файл: {svg_path}</p>'
    elif svg_chart:
        pass
    else:
        svg_chart = svg.chart_to_svg(chart, svg.SvgTheme())
        
    # HTML header
    writeln('<!DOCTYPE html>')
    writeln('<html lang="ru">')
    writeln('<head>')
    writeln('    <meta charset="UTF-8">')
    writeln('    <meta name="viewport" content="width=device-width, initial-scale=1.0">')
    writeln('    <title>Астрологическая карта</title>')
    writeln('    <style>')
    writeln('        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }')
    writeln('        h1 { color: #333; border-bottom: 2px solid #333; padding-bottom: 10px; }')
    writeln('        h2 { color: #555; margin-top: 30px; }')
    writeln('        table { border-collapse: collapse; width: 100%; margin: 20px 0; }')
    writeln('        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }')
    writeln('        th { background-color: #f2f2f2; font-weight: bold; }')
    writeln('        tr:nth-child(even) { background-color: #f9f9f9; }')
    writeln('        .chart-info { background-color: #f5f5f5; padding: 15px; border-radius: 15px; margin: 20px 0; }')
    writeln('        .chart-info ul { list-style-type: none; padding: 0; }')
    writeln('        .chart-info li { margin: 5px 0; }')
    writeln('        .chart-container { text-align: center; margin: 30px 0; }')
    writeln('        .chart-container svg { max-width: 100%; height: auto; }')
    writeln('    </style>')
    writeln('</head>')
    writeln('<body>')
    
    # Main content
    writeln('<h1>Астрологическая карта</h1>')
    
    # Chart info
    writeln('<div class="chart-info">')
    writeln('    <ul>')
    writeln(f'        <li><strong>Имя:</strong> {chart.name}</li>')
    writeln(f'        <li><strong>Дата и время:</strong> {chart.dt_loc.datetime.strftime("%Y-%m-%d %H:%M:%S")} ({chart.dt_loc.datetime.tzinfo})</li>')
    writeln(f'        <li><strong>Местоположение:</strong> {Latitude(chart.dt_loc.location.latitude)} {Longitude(chart.dt_loc.location.longitude)}</li>')
    writeln('    </ul>')
    writeln('</div>')
    
    # Embed SVG chart
    if svg_path:
        try:
            writeln('<h2>Карта гороскопа</h2>')
            writeln('<div class="chart-container">')
            writeln(f'    {svg_chart}')
            writeln('</div>')
        except (FileNotFoundError, IOError):
            writeln('<div class="chart-container">')
            writeln('    <h2>Карта гороскопа</h2>')
            writeln(f'    <p style="color: red;">Ошибка: не удалось загрузить SVG файл: {svg_path}</p>')
            writeln('</div>')
    
    # Planets table
    writeln('<h2>Позиции планет</h2>')
    writeln('<table>')
    writeln('    <thead>')
    writeln('        <tr>')
    writeln('            <th>Символ</th>')
    writeln('            <th>Долгота</th>')
    writeln('            <th>Широта</th>')
    writeln('            <th>Знак</th>')
    writeln('            <th>Угол в знаке</th>')
    writeln('            <th>Ретроградность</th>')
    writeln('            <th>Дом</th>')
    writeln('        </tr>')
    writeln('    </thead>')
    writeln('    <tbody>')
    
    for planet_pos in chart.planet_positions:
        writeln('        <tr>')
        writeln(f'            <td>{planet_pos.planet.symbol}</td>')
        writeln(f'            <td>{Angle.Lon(planet_pos.longitude)}</td>')
        writeln(f'            <td>{Angle.Lat(planet_pos.latitude)}</td>')
        writeln(f'            <td>{planet_pos.zodiac_sign.symbol}</td>')
        writeln(f'            <td>{Angle(planet_pos.angle_in_sign())}</td>')
        writeln(f'            <td>{"Да" if planet_pos.is_retrograde() else "Нет"}</td>')
        writeln(f'            <td>{chart.planet_houses[planet_pos.planet].roman_number}</td>')
        writeln('        </tr>')
    
    writeln('    </tbody>')
    writeln('</table>')
    
    # Houses table
    writeln('<h2>Дома по системе Плацидус</h2>')
    writeln('<table>')
    writeln('    <thead>')
    writeln('        <tr>')
    writeln('            <th>Дом</th>')
    writeln('            <th>Куспид</th>')
    writeln('            <th>Длина</th>')
    writeln('            <th>Знак</th>')
    writeln('            <th>Угол в знаке</th>')
    writeln('            <th>Планеты</th>')
    writeln('        </tr>')
    writeln('    </thead>')
    writeln('    <tbody>')
    
    for house in chart.houses:
        writeln('        <tr>')
        writeln(f'            <td>{house.roman_number}</td>')
        writeln(f'            <td>{Angle.Lon(house.cusp_longitude)}</td>')
        writeln(f'            <td>{Angle(house.length)}</td>')
        writeln(f'            <td>{house.zodiac_sign.symbol}</td>')
        writeln(f'            <td>{Angle(house.angle_in_sign)}</td>')
        planets_in_house = chart.house_planets.get(house.house_number, [])
        planet_symbols = ' '.join([p.symbol for p in planets_in_house])
        writeln(f'            <td>{planet_symbols}</td>')
        writeln('        </tr>')
    
    writeln('    </tbody>')
    writeln('</table>')
    
    # Aspects table
    writeln('<h2>Аспекты</h2>')
    writeln('<table>')
    writeln('    <thead>')
    writeln('        <tr>')
    writeln('            <th>Планета 1</th>')
    writeln('            <th>Планета 2</th>')
    writeln('            <th>Аспект</th>')
    writeln('            <th>Угол</th>')
    writeln('            <th>Орбис</th>')
    writeln('        </tr>')
    writeln('    </thead>')
    writeln('    <tbody>')
    
    for aspect in chart.aspects:
        writeln('        <tr>')
        writeln(f'            <td>{aspect.planet1.symbol}</td>')
        writeln(f'            <td>{aspect.planet2.symbol}</td>')
        writeln(f'            <td>{aspect.kind.name}</td>')
        writeln(f'            <td>{Angle(aspect.angle)}</td>')
        writeln(f'            <td>{Angle(aspect.orb)}</td>')
        writeln('        </tr>')
    
    writeln('    </tbody>')
    writeln('</table>')
    
    # HTML footer
    writeln('</body>')
    writeln('</html>')
    
    return '\n'.join(out)