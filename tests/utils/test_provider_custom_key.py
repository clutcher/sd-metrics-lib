import unittest

from sd_metrics_lib.utils.cache import CacheKeyBuilder
from sd_metrics_lib.sources.azure.tasks import AzureTaskProvider


class TestProviderCustomKey(unittest.TestCase):
    def test_uses_class_name_only(self):
        key = CacheKeyBuilder.create_provider_custom_key(AzureTaskProvider, ["updates", "123"])
        # parts are normalized (sorted unique), so expect '123_updates' in some order sorted => ['123','updates']
        self.assertTrue(key.startswith("custom||AzureTaskProvider||"))
        self.assertTrue(key.endswith("123_updates"))

    def test_empty_parts(self):
        key = CacheKeyBuilder.create_provider_custom_key(AzureTaskProvider, None)
        self.assertEqual(key, "custom||AzureTaskProvider||")


if __name__ == "__main__":
    unittest.main()
