import unittest
from typing import Optional, List

from sd_metrics_lib.sources.tasks import TaskProvider, CachingTaskProvider
from sd_metrics_lib.utils.cache import CacheProtocol, CacheKeyBuilder


class CountingProvider(TaskProvider):
    def __init__(self, tasks: list, query: Optional[str] = None, additional_fields: Optional[List[str]] = None):
        self._tasks = tasks
        self.calls = 0
        self.query = query
        self.additional_fields = additional_fields

    def get_tasks(self) -> list:
        self.calls += 1
        return list(self._tasks)


class FakeDjangoCache(CacheProtocol):
    def __init__(self):
        self._store = {}

    def get(self, key: str):
        return self._store.get(key, None)

    def set(self, key: str, value):
        self._store[key] = value


class CachingTaskProviderTestCase(unittest.TestCase):

    def test_should_use_cache_on_exact_hit(self):
        # given
        cache = {}
        provider = CountingProvider(tasks=[{"id": 1}], query="project = X", additional_fields=["a", "b"])
        caching = CachingTaskProvider(provider, cache)

        # when
        result1 = caching.get_tasks()
        result2 = caching.get_tasks()

        # then
        self.assertEqual(result1, [{"id": 1}])
        self.assertEqual(result2, [{"id": 1}])
        self.assertEqual(provider.calls, 1)

    def test_should_reuse_superset_when_exact_missing(self):
        # given
        cache = {}
        superset_provider = CountingProvider(tasks=[{"id": 1, "a": 1, "b": 2}], query="Q", additional_fields=["a", "b"])
        CachingTaskProvider(superset_provider, cache).get_tasks()
        self.assertEqual(superset_provider.calls, 1)

        # when
        subset_provider = CountingProvider(tasks=[{"id": 999}], query="Q", additional_fields=["a"])  # would be used only if miss
        result = CachingTaskProvider(subset_provider, cache).get_tasks()

        # then
        self.assertEqual(result, [{"id": 1, "a": 1, "b": 2}])
        self.assertEqual(subset_provider.calls, 0)

    def test_should_normalize_fields_to_avoid_duplicates(self):
        # given
        cache = {}
        provider1 = CountingProvider(tasks=[1, 2, 3], query="Q2", additional_fields=["b", "a", "a"])  # unsorted + dup
        caching1 = CachingTaskProvider(provider1, cache)
        caching1.get_tasks()  # warm cache
        provider2 = CountingProvider(tasks=[9], query="Q2", additional_fields=["a", "b"])  # would be used on miss
        caching2 = CachingTaskProvider(provider2, cache)

        # when
        result2 = caching2.get_tasks()

        # then
        self.assertEqual(result2, [1, 2, 3])
        self.assertEqual(provider2.calls, 0)
        self.assertEqual(provider1.calls, 1)

    def test_should_hit_superset_even_if_metadata_unsorted(self):
        # given
        cache = {}
        superset_provider = CountingProvider(tasks=[{"id": 7, "a": 10, "b": 20}], query="Q3", additional_fields=["a", "b"])
        CachingTaskProvider(superset_provider, cache).get_tasks()
        self.assertEqual(superset_provider.calls, 1)
        partial = CacheKeyBuilder.create_query_only_key_partial("Q3")
        meta_key = CacheKeyBuilder.create_meta_data_key(partial)
        cache[meta_key] = [["b", "a"]]

        # when
        subset_provider = CountingProvider(tasks=[{"id": 999}], query="Q3", additional_fields=["a"])  # used only on miss
        result = CachingTaskProvider(subset_provider, cache).get_tasks()

        # then
        self.assertEqual(result, [{"id": 7, "a": 10, "b": 20}])
        self.assertEqual(subset_provider.calls, 0)

    def test_should_work_with_none_query_and_empty_fields(self):
        # given
        cache = {}
        provider1 = CountingProvider(tasks=["x"], query=None, additional_fields=None)
        caching1 = CachingTaskProvider(provider1, cache)
        caching1.get_tasks()  # warm cache
        provider2 = CountingProvider(tasks=["y"], query=None, additional_fields=None)
        caching2 = CachingTaskProvider(provider2, cache)

        # when
        result2 = caching2.get_tasks()

        # then
        self.assertEqual(result2, ["x"])  # cached value
        self.assertEqual(provider2.calls, 0)
        self.assertEqual(provider1.calls, 1)

    def test_should_support_django_style_cache(self):
        # given
        django_cache = FakeDjangoCache()
        provider = CountingProvider(tasks=[{"id": 42}], query="D", additional_fields=["f1"])
        caching = CachingTaskProvider(provider, django_cache)
        caching.get_tasks()  # warm cache through adapter
        provider2 = CountingProvider(tasks=[{"id": 999}], query="D", additional_fields=["f1"])  # ignored if hit
        caching2 = CachingTaskProvider(provider2, django_cache)

        # when
        result2 = caching2.get_tasks()

        # then
        self.assertEqual(result2, [{"id": 42}])
        self.assertEqual(provider2.calls, 0)
        self.assertEqual(provider.calls, 1)


if __name__ == "__main__":
    unittest.main()
