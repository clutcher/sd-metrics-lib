from typing import Any


def get_attribute_by_path(obj: Any, path: str, default: Any = None) -> Any:
    cur = obj
    if not path:
        return cur
    for part in path.split('.'):
        if cur is None:
            return default
        try:
            cur = getattr(cur, part)
        except Exception:
            return default
    return cur
