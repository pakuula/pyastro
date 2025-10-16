#!/usr/bin/env python3
"""
Валидатор JSON/YAML файлов по JSON Schema
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any
from urllib.parse import urlparse
from urllib.request import urlopen
from urllib.error import URLError

import yaml
import jsonschema
from jsonschema import validate, ValidationError, Draft7Validator

def load_json(file_path: Path) -> Dict[str, Any]:
    """Загружает JSON файл"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Ошибка парсинга JSON: {e}") from e


def load_yaml(file_path: Path) -> Dict[str, Any]:
    """Загружает YAML файл с ограниченными преобразованиями типов"""
    if yaml is None:
        raise ImportError("PyYAML не установлен. Установите: pip install PyYAML")

    class NoDateLoader(yaml.SafeLoader):  # pylint: disable=too-many-ancestors
        """Загрузчик YAML без преобразования дат"""

        pass  # pylint: disable=unnecessary-pass

    # Удаляем timestamp resolver (даты остаются строками)
    NoDateLoader.yaml_implicit_resolvers = {
        key: [
            resolver
            for resolver in resolvers
            if resolver[0] != "tag:yaml.org,2002:timestamp"
        ]
        for key, resolvers in NoDateLoader.yaml_implicit_resolvers.items()
    }

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.load(f, Loader=NoDateLoader)
    except yaml.YAMLError as e:
        raise ValueError("Ошибка парсинга YAML") from e


def load_schema_from_url(url: str) -> Dict[str, Any]:
    """Загружает схему из URL"""
    try:
        with urlopen(url) as response:
            content = response.read().decode("utf-8")
            return json.loads(content)
    except URLError as e:
        raise ValueError(f"Ошибка загрузки схемы с URL {url}: {e}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"Ошибка парсинга JSON схемы с URL {url}: {e}") from e


def is_url(path_or_url: str) -> bool:
    """Проверяет, является ли строка URL"""
    parsed = urlparse(path_or_url)
    return parsed.scheme in ("http", "https")


def load_data(file_path: Path) -> Dict[str, Any]:
    """Автоматически определяет тип файла и загружает данные"""
    suffix = file_path.suffix.lower()

    # pylint: disable=no-else-return
    if suffix == ".json":
        return load_json(file_path)
    elif suffix in [".yaml", ".yml"]:
        return load_yaml(file_path)
    else:
        # Пробуем сначала JSON, потом YAML
        print(f"Неизвестное расширение файла {suffix}, поддерживаются только .json, .yaml, .yml")
        sys.exit(1)

def load_schema(schema_path_or_url: str) -> Dict[str, Any]:
    """Загружает схему из файла или URL"""
    # pylint: disable=no-else-return
    if is_url(schema_path_or_url):
        return load_schema_from_url(schema_path_or_url)
    else:
        return load_data(Path(schema_path_or_url))


def validate_file(
    data_file: Path, schema_path_or_url: str, verbose: bool = False
) -> bool:
    """
    Валидирует файл данных по схеме

    Returns:
        True если валидация прошла успешно, False если есть ошибки
    """
    try:
        # Загружаем схему
        if verbose:
            print(f"Загружаем схему: {schema_path_or_url}")

        schema = load_schema(schema_path_or_url)

        # Проверяем корректность самой схемы
        try:
            Draft7Validator.check_schema(schema)
            if verbose:
                print("✓ Схема корректна")
        except jsonschema.SchemaError as e:
            print(f"ERROR: Некорректная схема: {e}")
            return False

        # Загружаем данные
        if verbose:
            print(f"Загружаем данные: {data_file}")

        data = load_data(data_file)

        # Валидируем данные по схеме
        try:
            validate(instance=data, schema=schema)
            print(f"✓ Файл {data_file} соответствует схеме")
            return True

        except ValidationError as e:
            print(f"✗ Ошибка валидации в файле {data_file}:")
            print(f"  Путь: {' -> '.join(str(p) for p in e.absolute_path)}")
            print(f"  Сообщение: {e.message}")
            if e.validator_value:
                print(f"  Ожидалось: {e.validator_value}")
            if hasattr(e, "instance") and e.instance is not None:
                print(f"  Получено: {e.instance}")
            return False

    except FileNotFoundError as e:
        print(f"ERROR: Файл не найден: {e}")
        return False
    except ValueError as e:
        print(f"ERROR: {e}")
        return False
    except Exception as e: # pylint: disable=broad-except
        print(f"ERROR: Неожиданная ошибка: {e}")
        return False


def main():
    """Главная функция для запуска из командной строки валидатора входных данных."""
    parser = argparse.ArgumentParser(
        description="Валидатор JSON/YAML файлов по JSON Schema"
    )
    parser.add_argument(
        "data_file", type=Path, help="Путь к файлу данных (JSON или YAML)"
    )
    parser.add_argument(
        "-s",
        "--schema",
        type=str,
        default="schema.json",
        help="Путь к файлу схемы или URL (по умолчанию: schema.json)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Подробный вывод")

    args = parser.parse_args()

    if args.verbose:
        print(f"Файл данных: {args.data_file}")
        print(f"Схема: {args.schema}")

    # Проверяем существование схемы только если это не URL
    if not is_url(args.schema) and not Path(args.schema).exists():
        print(f"ERROR: Файл схемы не существует: {args.schema}")
        sys.exit(1)

    if not args.data_file.exists():
        print(f"ERROR: Файл данных не существует: {args.data_file}")
        sys.exit(1)

    success = validate_file(args.data_file, args.schema, args.verbose)

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
