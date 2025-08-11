from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication

from calculators.velocity_calculator import VelocityTimeUnit, GeneralizedTeamVelocityCalculator
from data_providers.azure.issue_provider import AzureIssueProvider
from data_providers.azure.story_point_extractor import AzureStoryPointExtractor
from data_providers.azure.worklog_extractor import AzureIssueTotalSpentTimeExtractor


def team_velocity_integration_test(wit_client):
    def create_issue_provider(client):
        query = """
               SELECT [System.Id]
               FROM workitems
               WHERE
                   [System.TeamProject] = 'Empower'
                 AND [System.State] IN ('Closed'
                   , 'Done'
                   , 'Resolved')
                 AND [System.WorkItemType] IN ('User Story'
                   , 'Bug')
                 AND [System.AreaPath] UNDER 'Empower\\Flow'
                 AND [Microsoft.VSTS.Common.ClosedDate] >= '2025-08-01'
               ORDER BY [System.ChangedDate] DESC \
               """
        return AzureIssueProvider(client, query=query)

    def create_story_point_extractor():
        return AzureStoryPointExtractor(default_story_points_value=1)

    def create_time_extractor():
        return AzureIssueTotalSpentTimeExtractor()

    # given
    issue_provider = create_issue_provider(wit_client)
    story_point_extractor = create_story_point_extractor()
    time_extractor = create_time_extractor()

    # when
    velocity_calculator = GeneralizedTeamVelocityCalculator(issue_provider=issue_provider,
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
