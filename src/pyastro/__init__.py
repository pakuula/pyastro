"""Вычисление астрологических данных и построение натальных карт."""
from .main import main
from .parade import main as parade_main
from .validate import main as validate_main

__all__ = ["main", "parade_main", "validate_main"]
