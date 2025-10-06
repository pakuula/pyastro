import logging
from typing import Any, Callable, get_args, get_origin

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def from_dict_dataclass[T](
    clazz: type[T],
    data: dict,
    special_fields: dict[str, Callable[[str, any], Any]] = None,
) -> T:
    """Создает тему из JSON-объекта."""
    obj = clazz.__new__(clazz)  # __init__ не вызван
    if special_fields is None:
        special_fields = {}
    processed_fields = set()
    logger.debug("from_json_dataclass: clazz=%s, data=%s", clazz, data)
    # Обработка полей
    # print(f"DEBUG: members: {obj.__dataclass_fields__}")  # pylint: disable=E1101
    for field, spec in obj.__dataclass_fields__.items():  # pylint: disable=E1101
        if field in data:
            logger.debug("Processing field '%s.%s'", clazz, field)
            processed_fields.add(field)
            value = data[field]
            if field in special_fields:
                value = special_fields[field](field, value)
                setattr(obj, field, value)
            elif hasattr(spec.type, "from_json") and callable(spec.type.from_json):
                # если в типе есть from_json, вызвать его
                value = spec.type.from_json(value)
                setattr(obj, field, value)
            else:
                # проверить, что тип совпадает (или совместим) с типом поля
                try:
                    # value = spec.type(value)  # попытка преобразования
                    value = _coerce_type(spec.type, value, field)
                except (TypeError, ValueError) as e:
                    raise ValueError(
                        f"Invalid type for field '{field}': expected {spec.type}, got {type(value)}({value}): {e}"
                    ) from e
                setattr(obj, field, value)
    # Проверка на отсутствие необходимых полей
    for field, spec in obj.__dataclass_fields__.items():  # pylint: disable=E1101
        if field not in processed_fields and spec.default is spec.default_factory:
            raise ValueError(f"Missing required field '{field}'")
    # Инициализация полей по умолчанию
    for field, spec in obj.__dataclass_fields__.items():  # pylint: disable=E1101
        if field not in processed_fields:
            if spec.default is not spec.default_factory:
                logger.debug("Set default for field '%s'", field)
                setattr(obj, field, spec.default)
            elif spec.default_factory is not None:
                logger.debug("Set default for field '%s' using factory", field)
                setattr(obj, field, spec.default_factory())
    # Дополнительные поля
    for field in data:
        if field not in processed_fields:
            setattr(obj, field, data[field])
    return obj

def _coerce_type(t: Any, val: Any, field_name: str) -> Any:
    origin = get_origin(t)
    if origin is None:
        # Простой тип
        if isinstance(t, type):
            if isinstance(val, t):
                return val
            try:
                return t(val)
            except Exception as e:  # noqa: BLE001
                raise ValueError(
                    f"Invalid value for '{field_name}': cannot cast {val!r} to {t}"
                ) from e
        # Аннотация без origin (например |) — просто вернуть как есть
        return val
    # Обработка generic
    if origin in (list, tuple):
        (elem_type,) = get_args(t) or (Any,)
        if not isinstance(val, list):
            raise ValueError(f"Field '{field_name}' must be a list")
        return [
            (
                _coerce_type(elem_type, x, f"{field_name}[{i}]")
                if elem_type is not Any
                else x
            )
            for i, x in enumerate(val)
        ]
    if origin is dict:
        key_t, val_t = get_args(t)
        if not isinstance(val, dict):
            raise ValueError(f"Field '{field_name}' must be a dict")
        out = {}
        for k, v in val.items():
            ck = _coerce_type(key_t, k, f"{field_name}.key") if key_t is not Any else k
            cv = _coerce_type(val_t, v, f"{field_name}[{k}]") if val_t is not Any else v
            out[ck] = cv
        return out
    # Иное generic — без строгой обработки
    return val