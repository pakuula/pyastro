import shutil
from pyastro.astro import Chart
import subprocess
import tempfile

PANDOC_DEFAULTS = """
pdf-engine: xelatex

variables:
  # Формат бумаги
  papersize: a4

  # Поля страницы
  geometry: top=15mm, right=15mm, bottom=15mm, left=20mm

  # Шрифты
  mainfont: FreeSerif
  sansfont: FreeSans
  monofont: FreeMono
  fontsize: 14pt
  linestretch: 1.2
"""


_which = shutil.which

def _has_font(fontname: str) -> bool:
    """Проверка наличия шрифта в системе"""
    subproc = subprocess.run(
        ["fc-list", ":", "family"],
        capture_output=True,
        text=True,
        check=False,
    )
    if subproc.returncode != 0:
        return False
    fonts = subproc.stdout.splitlines()
    for font in fonts:
        families = [f.strip().lower() for f in font.split(",")]
        if fontname.lower() in families:
            return True
    return False

def export_as_pdf(
    markdown_path: str,
    pdf_path: str,
    pandoc_path: str = "pandoc",
    pandoc_defaults_file: str = None,
) -> None:
    """Генерация PDF отчёта по гороскопу из markdown файла"""
    if not _which(pandoc_path):
        raise ValueError(f"Команда '{pandoc_path}' не найдена в PATH")
    if not _which("xelatex"):
        raise ValueError("Команда 'xelatex' не найдена в PATH")
    if not _which("rsvg-convert"):
        raise ValueError(
            "Команда 'rsvg-convert' не найдена в PATH, требуется для включения SVG в PDF"
        )
    if pandoc_defaults_file is None:
        if not _which("fc-list"):
            raise ValueError("Команда 'fc-list' не найдена в PATH, требуется для проверки шрифтов")
        
        for font in ["FreeSerif", "FreeSans", "FreeMono"]:
            if not _has_font(font):
                raise ValueError(f"Шрифт '{font}' не найден в системе, установите его: https://www.gnu.org/software/freefont/")
        
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmpf:
        if pandoc_defaults_file:
            with open(pandoc_defaults_file, "r", encoding="utf-8") as f:
                tmpf.write(f.read())
                if not f.read().endswith("\n"):
                    tmpf.write("\n")
        else:
            tmpf.write(PANDOC_DEFAULTS)
        tmpf.flush()
        # tmpf.close()

        cmd = [pandoc_path, "--defaults", tmpf.name, markdown_path, "-o", pdf_path]
        subproc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        if subproc.returncode != 0:
            raise ValueError(f"Ошибка генерации PDF: {subproc.stderr.strip()}")
    
def to_pdf_weasy(chart: Chart, svg_chart: str, pdf_path: str) -> None:
    """Генерация PDF отчёта по гороскопу из SVG файла с помощью WeasyPrint"""
    try:
        import weasyprint
    except ImportError as e:
        raise ValueError("WeasyPrint не установлен, установите его: pip install weasyprint") from e
    
    from pyastro.rendering import html
    content = html.to_html(chart, svg_chart=svg_chart)

    weasyprint.HTML(string=content, base_url=".").write_pdf(pdf_path)