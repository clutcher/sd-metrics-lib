import datetime

from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication

from sd_metrics_lib.utils.enums import VelocityTimeUnit
from sd_metrics_lib.calculators.velocity import GeneralizedTeamVelocityCalculator
from sd_metrics_lib.sources.azure.query import AzureSearchQueryBuilder
from sd_metrics_lib.sources.azure.story_points import AzureStoryPointExtractor
from sd_metrics_lib.sources.azure.tasks import AzureTaskProvider
from sd_metrics_lib.sources.azure.worklog import AzureTaskTotalSpentTimeExtractor


def team_velocity_integration_test(wit_client):
    def create_task_provider(client):
        query_builder = AzureSearchQueryBuilder(
            projects=['Empower'],
            statuses=['Closed', 'Done', 'Resolved'],
            task_types=['User Story', 'Bug'],
            teams=['Empower\\Flow'],
            resolution_dates=(datetime.datetime(2025, 8, 1), None),
            order_by='[System.ChangedDate] DESC'
        )
        return AzureTaskProvider(client, query=(query_builder.build_query()))

    def create_story_point_extractor():
        return AzureStoryPointExtractor(default_story_points_value=1)

    def create_time_extractor():
        return AzureTaskTotalSpentTimeExtractor()

    # given
    task_provider = create_task_provider(wit_client)
    story_point_extractor = create_story_point_extractor()
    time_extractor = create_time_extractor()

    # when
    velocity_calculator = GeneralizedTeamVelocityCalculator(task_provider=task_provider,
                                                            story_point_extractor=story_point_extractor,
                                                            time_extractor=time_extractor)

    velocity = velocity_calculator.calculate(velocity_time_unit=VelocityTimeUnit.DAY)

    # then
    print(velocity)


if __name__ == '__main__':
    ORGANIZATION_URL = ''
    PERSONAL_ACCESS_TOKEN = ''

    credentials = BasicAuthentication('', PERSONAL_ACCESS_TOKEN)
    connection = Connection(base_url=ORGANIZATION_URL, creds=credentials)
    wit_client = connection.clients.get_work_item_tracking_client()

    team_velocity_integration_test(wit_client)
