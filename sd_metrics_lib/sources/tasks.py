from abc import abstractmethod, ABC
from typing import Optional, List, Tuple, Set, Iterable
from typing import Union

from sd_metrics_lib.utils.cache import (
    DictProtocol,
    CacheProtocol,
    DictToCacheProtocolAdapter,
    CacheKeyBuilder,
    SupersetResolver
)


class TaskProvider(ABC):

    @abstractmethod
    def get_tasks(self) -> list:
        pass


class ProxyTaskProvider(TaskProvider):

    def __init__(self, tasks: list) -> None:
        self.tasks = tasks

    def get_tasks(self) -> list:
        return self.tasks


class CachingTaskProvider(TaskProvider):

    def __init__(self, provider: TaskProvider,
                 cache: Optional[Union[DictProtocol, CacheProtocol]] = None) -> None:
        if cache is not None and isinstance(cache, DictProtocol):
            self.cache: Optional[CacheProtocol] = DictToCacheProtocolAdapter(cache)
        else:
            self.cache = cache  # type: ignore[assignment]

        self.provider = provider
        self.query = getattr(provider, 'query', None)
        self.additional_fields = getattr(provider, 'additional_fields', None)

    def get_tasks(self):
        cached = self._try_fetch_from_cache()
        if cached is not None:
            return cached
        tasks = self.provider.get_tasks()
        self._store_in_cache(tasks)
        return tasks

    def _try_fetch_from_cache(self):
        if self.cache is None:
            return None

        exact = self._fetch_exact_cache_hit()
        if exact is not None:
            return exact

        superset = self._fetch_superset_cache_hit()
        if superset is not None:
            return superset

        return None

    def _store_in_cache(self, tasks):
        if self.cache is None:
            return
        normalized_fields = CacheKeyBuilder.normalize_fields(self.additional_fields)
        self._store_tasks_under_data_key(tasks, normalized_fields)
        self._ensure_fieldset_list_updated(normalized_fields)

    def _fetch_exact_cache_hit(self):
        partial_key = CacheKeyBuilder.create_query_only_key_partial(self.query)
        data_key = CacheKeyBuilder.create_full_data_key(partial_key,
                                                        CacheKeyBuilder.normalize_fields(self.additional_fields))
        hit = self.cache.get(data_key)  # type: ignore[union-attr]
        if hit is not None:
            return hit
        return None

    def _fetch_superset_cache_hit(self):
        requested_fields = CacheKeyBuilder.normalize_fields(self.additional_fields)
        meta_key = CacheKeyBuilder.create_meta_data_key(CacheKeyBuilder.create_query_only_key_partial(self.query))
        available_fieldsets = self._load_cached_fieldsets(meta_key)
        compatible_available_fieldset = SupersetResolver.find_superset_fieldset(requested_fields, available_fieldsets)
        if compatible_available_fieldset is not None:
            superset_data_key = CacheKeyBuilder.create_full_data_key(
                CacheKeyBuilder.create_query_only_key_partial(self.query),
                compatible_available_fieldset)
            superset_value = self.cache.get(superset_data_key)  # type: ignore[union-attr]
            if superset_value is not None:
                return superset_value
        return None

    def _store_tasks_under_data_key(self, tasks, fields: Iterable[str]):
        partial_key = CacheKeyBuilder.create_query_only_key_partial(self.query)
        data_key = CacheKeyBuilder.create_full_data_key(partial_key, fields)
        self.cache.set(data_key, tasks)  # type: ignore[union-attr]

    def _ensure_fieldset_list_updated(self, fields: Iterable[str]):
        meta_key = self._create_meta_key_for_query()
        fieldsets = self._load_cached_fieldsets(meta_key)
        fieldset_tuple = tuple(fields)
        if fieldset_tuple not in fieldsets:
            fieldsets.add(fieldset_tuple)
            self._save_cached_fieldsets(meta_key, fieldsets)

    def _create_meta_key_for_query(self) -> str:
        return CacheKeyBuilder.create_meta_data_key(CacheKeyBuilder.create_query_only_key_partial(self.query))

    def _load_cached_fieldsets(self, meta_key: str) -> Set[Tuple[str, ...]]:
        raw = self.cache.get(meta_key)  # type: ignore[union-attr]
        if raw is None:
            return set()
        result: Set[Tuple[str, ...]] = set()
        try:
            for fieldset in raw:
                result.add(tuple(fieldset))
        except Exception:
            return set()
        return result

    def _save_cached_fieldsets(self, meta_key: str, fieldsets: Set[Tuple[str, ...]]):
        serializable: List[List[str]] = [list(t) for t in fieldsets]
        self.cache.set(meta_key, serializable)  # type: ignore[union-attr]
