import base64
from abc import abstractmethod, ABC
from typing import Optional


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

    def __init__(self, provider: TaskProvider, cache: Optional[dict] = None) -> None:
        self.cache = cache

        self.provider = provider
        self.query = getattr(provider, 'query', None)
        self.additional_fields = getattr(provider, 'additional_fields', None)

    def get_tasks(self):
        cached_tasks = self._search_in_cache()
        if cached_tasks is not None:
            return cached_tasks

        tasks = self.provider.get_tasks()
        self._set_in_cache(tasks)
        return tasks

    def _search_in_cache(self):
        if self.cache is None:
            return None

        # if query with same additional_fields is already present in cache
        cache_key_with_fields = self._create_cache_key_for_query()
        if self._is_key_in_cache(cache_key_with_fields):
            return self._get_from_cache(cache_key_with_fields)

        # searching for cached responses with not less additional_fields (superset)
        partial_key = self._create_partial_cache_key()
        for key in self._get_all_cache_keys():
            if key.startswith(partial_key):
                if self.additional_fields is None:
                    return self._get_from_cache(key)
                else:
                    all_fields_present = True
                    for field in self.additional_fields:
                        if "_" + field not in key:
                            all_fields_present = False
                    if all_fields_present:
                        return self._get_from_cache(key)

        return None

    def _get_from_cache(self, cache_key):
        return self.cache.get(cache_key)

    def _set_in_cache(self, tasks):
        if self.cache is None:
            return
        self.cache[self._create_cache_key_for_query()] = tasks

    def _is_key_in_cache(self, cache_key):
        return cache_key in self.cache

    def _get_all_cache_keys(self):
        return self.cache.keys()

    def _create_cache_key_for_query(self):
        if self.additional_fields is None:
            return self._create_partial_cache_key()
        return self._create_partial_cache_key() + "_".join(self.additional_fields)

    def _create_partial_cache_key(self):
        if self.query is None:
            return "none_query||"
        return base64.b64encode(self.query.encode("ascii")).decode("ascii") + "||"
