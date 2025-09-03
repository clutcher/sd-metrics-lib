import unittest

from sd_metrics_lib.utils.cache import CacheKeyBuilder
from sd_metrics_lib.sources.azure.tasks import AzureTaskProvider


class TestProviderCustomKey(unittest.TestCase):
    def test_uses_class_name_only_starts_with_provider_prefix(self):
        # given
        provider_class = AzureTaskProvider
        custom_parts = ["updates", "123"]
        # when
        generated_key = CacheKeyBuilder.create_provider_custom_key(provider_class, custom_parts)
        # then
        self.assertTrue(generated_key.startswith("custom||AzureTaskProvider||"))

    def test_uses_class_name_only_ends_with_sorted_suffix(self):
        # given
        provider_class = AzureTaskProvider
        custom_parts = ["updates", "123"]
        # when
        generated_key = CacheKeyBuilder.create_provider_custom_key(provider_class, custom_parts)
        # then
        self.assertTrue(generated_key.endswith("123_updates"))

    def test_empty_parts_keeps_provider_prefix(self):
        # given
        provider_class = AzureTaskProvider
        custom_parts = None
        # when
        generated_key = CacheKeyBuilder.create_provider_custom_key(provider_class, custom_parts)
        # then
        self.assertEqual(generated_key, "custom||AzureTaskProvider||")


if __name__ == "__main__":
    unittest.main()
