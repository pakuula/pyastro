import subprocess
import logging
import shutil

logger = logging.getLogger(__name__)

def export_as_png(svg_doc: str, png_path: str, throw_if_error=False):
    """Генерация PNG из SVG с помощью rsvg-convert.
    
    :param svg_doc: SVG документ в виде строки
    :param png_path: Путь для сохранения PNG файла
    :param throw_if_error: Выбрасывать исключение при ошибке (иначе логировать ошибку)
    """
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
                # Читает SVG из stdin
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
