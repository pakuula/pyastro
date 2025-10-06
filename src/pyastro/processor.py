from dataclasses import dataclass
import logging
import os.path
import shutil
import subprocess
from tempfile import NamedTemporaryFile
from typing import Optional



from .rendering import svg, markdown, html, pdf

from .astro import Chart, DatetimeLocation, HouseSystem
from .util import Angle

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
            f"{aspect.kind.short_name} {aspect.kind.symbol} {Angle(aspect.angle)} "
            f"(орб: {Angle(aspect.orb)})"
        )


@dataclass
class OutputParams:
    png_path: Optional[str] = None
    svg_doc_path: Optional[str] = None
    svg_chart_path: Optional[str] = None
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

    if svg_theme is None:
        svg_theme = svg.SvgTheme()
    svg_chart = svg.chart_to_svg(
        chart,
        svg_theme,
        # Асцендент на востоке
        angle=-chart.ascendant,
    )
    svg_doc = svg.to_svg(chart, svg_chart, svg_theme)
    
    logger.debug("Output params: %s", output_params)
    if output_params.svg_chart_path:
        with open(output_params.svg_chart_path, "w", encoding="utf-8") as f:
            f.write(svg_chart)
        logger.info("SVG диаграмма сохранёна в %s", output_params.svg_chart_path)
    if output_params.svg_doc_path:
        with open(output_params.svg_doc_path, "w", encoding="utf-8") as f:
            f.write(svg_doc)
        logger.info("SVG сохранён в %s", output_params.svg_doc_path)
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
    
    if output_params.html_path:
        html_doc = html.to_html(chart, svg_chart=svg_chart)
        with open(output_params.html_path, "w", encoding="utf-8") as f:
            f.write(html_doc)
        logger.info("HTML сохранён в %s", output_params.html_path)
        
    if output_params.png_path:
        try:
            export_as_png(svg_doc, output_params.png_path, throw_if_error=True)
            logger.info("PNG сохранён в %s", output_params.png_path)
        except ValueError as e:
            logger.error("Ошибка генерации PNG: %s", e)

    if output_params.pdf_path:
        with NamedTemporaryFile(
            delete=True, suffix=".svg"
        ) as tmp_svg_file, NamedTemporaryFile(delete=True, suffix=".md") as tmp_md_file:
            tmp_svg_file.write(svg_chart.encode("utf-8"))
            tmp_svg_file.flush()
            # tmp_svg_file.close()

            mdown = markdown.to_markdown(chart, svg_path=tmp_svg_file.name)
            mdown = mdown.replace("⯓", "♇") # в шрифте FreeSerif нет символа ⯓
            tmp_md_file.write(mdown.encode("utf-8"))
            tmp_md_file.flush()
            # tmp_md_file.close()

            pdf.export_as_pdf(tmp_md_file.name, output_params.pdf_path)
        # pdf.to_pdf_weasy(chart, svg_chart, output_params.pdf_path)
        logger.info("PDF сохранён в %s", output_params.pdf_path)

def export_as_png(svg_doc, png_path, throw_if_error=False):
    rsvg_convert = shutil.which("rsvg-convert")
    if rsvg_convert is None:
        if not throw_if_error:
            logger.error("Команда 'rsvg-convert' не найдена в PATH, пропуск PNG")
        else:
            raise ValueError("Команда 'rsvg-convert' не найдена в PATH")
    else:
        cmd = [
                rsvg_convert,
                "-f", "png",
                "-o",
                png_path,
                "-",
            ]
        logger.debug("Running command: %s", " ".join(cmd))
        proc = subprocess.run(
                cmd,
                input=svg_doc,
                capture_output=True,
                text=True,
                check=False,
            )
        if proc.returncode != 0:
            if throw_if_error:
                raise ValueError(f"Ошибка генерации PNG с помощью rsvg-convert: {proc.stderr.strip()}")
            else:
                logger.error(
                        "Ошибка генерации PNG с помощью rsvg-convert: %s",
                        proc.stderr.strip(),
                    )
        