from concurrent.futures import ThreadPoolExecutor

from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication

from sd_metrics_lib.sources.azure.query import AzureSearchQueryBuilder
from sd_metrics_lib.sources.azure.tasks import AzureTaskProvider

thread_pool = ThreadPoolExecutor(max_workers=20, thread_name_prefix="test-fetch")


def azure_search_more_than_limit_example(wit_client):
    def create_task_provider(client):
        qb = AzureSearchQueryBuilder(
            projects=['Empower'],
            teams=['Empower\\Flow'],
            order_by='[System.ChangedDate] DESC'
        )
        return AzureTaskProvider(client, additional_fields=AzureTaskProvider.DEFAULT_FIELDS,
                                 custom_expand_fields=[AzureTaskProvider.WORK_ITEM_UPDATES_CUSTOM_FIELD_NAME],
                                 query=(qb.build_query()), thread_pool_executor=thread_pool)

    # given
    task_provider = create_task_provider(wit_client)

    # when
    tasks = task_provider.get_tasks()

    # then
    print(len(tasks))


if __name__ == '__main__':
    ORGANIZATION_URL = ''
    PERSONAL_ACCESS_TOKEN = ''

    credentials = BasicAuthentication('', PERSONAL_ACCESS_TOKEN)
    connection = Connection(base_url=ORGANIZATION_URL, creds=credentials)
    azure_client = connection.clients.get_work_item_tracking_client()

    azure_search_more_than_limit_example(azure_client)
