"""Модуль, содержащий класс Table для представления таблицы данных."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Table:
    """Таблица данных с заголовками и строками."""

    headers: list[str]
    rows: list[list[Any]] = field(default_factory=list)
    header_attrs: dict[str, Any] = field(default_factory=dict)
    row_attrs: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Инициализация таблицы."""
        if not self.headers:
            raise ValueError("Заголовки не могут быть пустыми.")
        for i, row in enumerate(self.rows):
            if len(row) != len(self.headers):
                raise ValueError(
                    f"Все строки должны иметь одинаковую длину с заголовками: строка {i} имеет длину {len(row)}, ожидаемая длина {len(self.headers)}."
                )

    def append(self, row: list[Any]) -> None:
        """Добавляет строку в таблицу."""
        if len(row) != len(self.headers):
            raise ValueError(
                f"Длина строки должна соответствовать количеству заголовков: ожидаемая длина {len(self.headers)}, фактическая длина {len(row)}."
            )
        self.rows.append(row)

    def get_column(self, index: int) -> list[Any]:
        """Возвращает столбец по индексу."""
        if index < 0 or index >= len(self.headers):
            raise IndexError("Индекс столбца вне диапазона.")
        return [row[index] for row in self.rows]

    def get_header_attributes(self, domain: str) -> dict[str, Any]:
        """Возвращает атрибуты заголовков для заданного домена."""
        return self.header_attrs.get(domain, {})

    def has_header_attributes(self, domain: str) -> bool:
        """Проверяет наличие атрибутов заголовков для заданного домена."""
        return domain in self.header_attrs

    def get_row_attributes(self, domain: str) -> dict[str, Any]:
        """Возвращает атрибуты строк для заданного домена."""
        return self.row_attrs.get(domain, {})

    def has_row_attributes(self, domain: str) -> bool:
        """Проверяет наличие атрибутов строк для заданного домена."""
        return domain in self.row_attrs
