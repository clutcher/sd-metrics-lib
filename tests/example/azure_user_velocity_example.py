import datetime
from concurrent.futures import ThreadPoolExecutor

from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication

from sd_metrics_lib.calculators.velocity import UserVelocityCalculator
from sd_metrics_lib.utils.time import TimeUnit
from sd_metrics_lib.sources.azure.query import AzureSearchQueryBuilder
from sd_metrics_lib.sources.azure.story_points import AzureStoryPointExtractor
from sd_metrics_lib.sources.azure.tasks import AzureTaskProvider
from sd_metrics_lib.sources.azure.worklog import AzureStatusChangeWorklogExtractor
from sd_metrics_lib.sources.worklog import ChainedWorklogExtractor

thread_pool = ThreadPoolExecutor(max_workers=20, thread_name_prefix="test-fetch")

def user_velocity_integration_test(wit_client):
    def create_task_provider(client):
        qb = AzureSearchQueryBuilder(
            projects=['Empower'],
            statuses=['Closed', 'Done', 'Resolved'],
            task_types=['User Story', 'Bug'],
            teams=['Empower\\Flow'],
            resolution_dates=(datetime.datetime(2025, 8, 1), None),
            order_by='[System.ChangedDate] DESC'
        )
        return AzureTaskProvider(client, query=(qb.build_query()), thread_pool_executor=thread_pool)

    def create_story_point_extractor():
        return AzureStoryPointExtractor(default_story_points_value=1)

    def create_worklog_extractor():
        status_extractor = AzureStatusChangeWorklogExtractor(transition_statuses=['In Progress'])
        return ChainedWorklogExtractor([status_extractor])

    # given
    task_provider = create_task_provider(wit_client)
    story_point_extractor = create_story_point_extractor()
    worklog_extractor = create_worklog_extractor()

    # when
    velocity_calculator = UserVelocityCalculator(task_provider=task_provider,
                                                 story_point_extractor=story_point_extractor,
                                                 worklog_extractor=worklog_extractor)

    velocity = velocity_calculator.calculate(velocity_time_unit=TimeUnit.DAY)

    # then
    print(velocity)


if __name__ == '__main__':
    ORGANIZATION_URL = ''
    PERSONAL_ACCESS_TOKEN = ''

    credentials = BasicAuthentication('', PERSONAL_ACCESS_TOKEN)
    connection = Connection(base_url=ORGANIZATION_URL, creds=credentials)
    azure_client = connection.clients.get_work_item_tracking_client()

    user_velocity_integration_test(azure_client)
