import base64
from typing import Protocol, runtime_checkable, Any, Iterable, List, Tuple, Optional


@runtime_checkable
class CacheProtocol(Protocol):
    def get(self, key: str) -> Any: ...

    def set(self, key: str, value: Any) -> None: ...


@runtime_checkable
class DictProtocol(Protocol):
    def __getitem__(self, key: str) -> Any: ...

    def __setitem__(self, key: str, value: Any) -> None: ...


class DictToCacheProtocolAdapter(CacheProtocol):
    def __init__(self, mapping: DictProtocol) -> None:
        self._dict = mapping

    def get(self, key: str) -> Any:
        try:
            return self._dict[key]
        except KeyError:
            return None

    def set(self, key: str, value: Any) -> None:
        self._dict[key] = value


class CacheKeyBuilder:
    DATA_PREFIX = "data||"
    META_PREFIX = "meta||"

    @staticmethod
    def normalize_fields(fields: Optional[Iterable[str]]) -> List[str]:
        if not fields:
            return []
        return sorted(set(fields))

    @staticmethod
    def create_query_only_key_partial(query: Optional[str]) -> str:
        if query is None:
            return "none_query||"
        return base64.b64encode(query.encode("ascii")).decode("ascii") + "||"

    @staticmethod
    def create_full_data_key(query_only_key_partial: str, fields: Optional[Iterable[str]]) -> str:
        if not fields:
            return f"{CacheKeyBuilder.DATA_PREFIX}{query_only_key_partial}"
        normalized = CacheKeyBuilder.normalize_fields(fields)
        return f"{CacheKeyBuilder.DATA_PREFIX}{query_only_key_partial}" + "_".join(normalized)

    @staticmethod
    def create_meta_data_key(query_only_key_partial: str) -> str:
        return f"{CacheKeyBuilder.META_PREFIX}{query_only_key_partial}fieldsets"


class SupersetResolver:
    @staticmethod
    def find_superset_fieldset(requested_fields: Iterable[str], available_fieldsets: Iterable[Tuple[str, ...]]) -> \
            Optional[Tuple[str, ...]]:
        requested_set = set(requested_fields)
        for fieldset in available_fieldsets:
            if requested_set.issubset(fieldset):
                return fieldset
        return None
