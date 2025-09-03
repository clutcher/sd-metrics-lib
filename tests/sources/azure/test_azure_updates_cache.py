import unittest
from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor

from sd_metrics_lib.sources.azure.tasks import AzureTaskProvider
from sd_metrics_lib.utils.cache import CacheProtocol, CacheKeyBuilder


class InMemoryCache(CacheProtocol):
    def __init__(self):
        self.store = {}

    def get(self, key: str):
        return self.store.get(key)

    def set(self, key: str, value):
        self.store[key] = value


class StubAzureClient:
    def __init__(self, work_item_ids=(1,)):
        self._ids = list(work_item_ids)
        self.get_updates_calls = []
        self.get_work_items_calls = []

    def query_by_wiql(self, wiql, top=None):
        refs = [SimpleNamespace(id=i) for i in self._ids]
        # mimic azure SDK contract pieces used by provider
        return SimpleNamespace(work_items=refs, work_item_relations=None)

    def get_work_items(self, ids, fields):
        self.get_work_items_calls.append(list(ids))
        # Return simple items with fields dict as provider expects
        return [SimpleNamespace(id=i, fields={}) for i in ids]

    def get_updates(self, item_id: int):
        self.get_updates_calls.append(item_id)
        return [f"update_for_{item_id}"]


class AzureUpdatesCachingTests(unittest.TestCase):
    def _create_provider(self, azure_client, cache: CacheProtocol, use_threads=False):
        executor = ThreadPoolExecutor(max_workers=4) if use_threads else None
        return AzureTaskProvider(
            azure_client=azure_client,
            query="SELECT [System.Id] FROM WorkItems WHERE [System.Id] >= 1",
            additional_fields=[],
            custom_expand_fields=[AzureTaskProvider.WORK_ITEM_UPDATES_CUSTOM_FIELD_NAME],
            page_size=200,
            thread_pool_executor=executor,
            cache=cache,
        )

    def _run_cache_hit_scenario(self):
        # given: pre-populated cache entry for item id 1
        cache = InMemoryCache()
        azure = StubAzureClient(work_item_ids=(1,))
        provider = self._create_provider(azure, cache)
        cache_key = CacheKeyBuilder.create_provider_custom_key(AzureTaskProvider, ["updates", "1"])
        cached_value = ["CACHED_UPDATE_1"]
        cache.set(cache_key, cached_value)
        # when
        tasks = provider.get_tasks()
        return azure, tasks, cached_value

    def test_cache_hit_skips_azure_get_updates_has_no_calls(self):
        # when
        azure, tasks, cached_value = self._run_cache_hit_scenario()
        # then
        self.assertEqual(azure.get_updates_calls, [])

    def test_cache_hit_skips_azure_get_updates_returns_cached_value(self):
        # when
        azure, tasks, cached_value = self._run_cache_hit_scenario()
        # then
        self.assertEqual(
            tasks[0].fields[AzureTaskProvider.WORK_ITEM_UPDATES_CUSTOM_FIELD_NAME],
            cached_value,
        )

    def test_cache_hit_skips_azure_get_updates_returns_single_task(self):
        # when
        azure, tasks, cached_value = self._run_cache_hit_scenario()
        # then
        self.assertEqual(len(tasks), 1)

    def _run_cache_miss_then_hit_scenario(self):
        # given
        cache = InMemoryCache()
        azure = StubAzureClient(work_item_ids=(1,))
        provider = self._create_provider(azure, cache)
        # when: first run should miss and fetch updates from Azure
        tasks_first = provider.get_tasks()
        expected_key = CacheKeyBuilder.create_provider_custom_key(AzureTaskProvider, ["updates", "1"])
        # when: second run should be cache hit (no extra azure calls)
        tasks_second = provider.get_tasks()
        return azure, cache, expected_key, tasks_first, tasks_second

    def test_cache_miss_fetches_and_populates_cache_once(self):
        # when
        azure, cache, expected_key, tasks_first, tasks_second = self._run_cache_miss_then_hit_scenario()
        # then
        self.assertEqual(azure.get_updates_calls, [1])

    def test_cache_miss_populates_cache_key(self):
        # when
        azure, cache, expected_key, tasks_first, tasks_second = self._run_cache_miss_then_hit_scenario()
        # then
        self.assertIn(expected_key, cache.store)

    def test_cache_miss_then_reuse_tasks_first_contains_update(self):
        # when
        azure, cache, expected_key, tasks_first, tasks_second = self._run_cache_miss_then_hit_scenario()
        # then
        self.assertEqual(
            tasks_first[0].fields[AzureTaskProvider.WORK_ITEM_UPDATES_CUSTOM_FIELD_NAME],
            ["update_for_1"],
        )

    def test_cache_miss_then_reuse_tasks_second_contains_update(self):
        # when
        azure, cache, expected_key, tasks_first, tasks_second = self._run_cache_miss_then_hit_scenario()
        # then
        self.assertEqual(
            tasks_second[0].fields[AzureTaskProvider.WORK_ITEM_UPDATES_CUSTOM_FIELD_NAME],
            ["update_for_1"],
        )

    def _run_concurrent_execution_scenario(self):
        cache = InMemoryCache()
        item_ids = (1, 2, 3)
        azure = StubAzureClient(work_item_ids=item_ids)
        provider = self._create_provider(azure, cache, use_threads=True)
        provider.get_tasks()  # first run invokes get_updates per id
        return cache, item_ids, azure, provider

    def test_concurrent_execution_populates_cache_for_each_item_all_ids_fetched(self):
        # when
        cache, item_ids, azure, provider = self._run_concurrent_execution_scenario()
        # then
        self.assertCountEqual(azure.get_updates_calls, list(item_ids))

    def test_concurrent_execution_second_run_uses_cache_no_new_calls(self):
        # given
        cache, item_ids, azure, provider = self._run_concurrent_execution_scenario()
        # when
        azure.get_updates_calls.clear()
        provider.get_tasks()
        # then
        self.assertEqual(azure.get_updates_calls, [])

    def test_concurrent_execution_cache_contains_keys(self):
        # when
        cache, item_ids, azure, provider = self._run_concurrent_execution_scenario()
        # then
        for item_id in item_ids:
            key = CacheKeyBuilder.create_provider_custom_key(AzureTaskProvider, ["updates", str(item_id)])
            self.assertIn(key, cache.store)


if __name__ == "__main__":
    unittest.main()
