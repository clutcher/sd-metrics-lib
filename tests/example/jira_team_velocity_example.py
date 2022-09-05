from atlassian import Jira

from calculators.velocity_calculator import VelocityTimeUnit, GeneralizedTeamVelocityCalculator
from data_providers.jira.issue_provider import JiraIssueProvider
from data_providers.jira.story_point_extractor import JiraTShirtStoryPointExtractor
from data_providers.jira.worklog_extractor import JiraResolutionTimeIssueTotalSpentTimeExtractor


def team_velocity_integration_test(client):
    def create_issue_provider(jira):
        jql = " type in (Story, Bug, 'Tech Debt', 'Regression Defect') AND project in ('TBC') AND resolutiondate >= 2022-05-01 "
        jql_issue_provider = JiraIssueProvider(jira, jql, expand=['changelog'])
        return jql_issue_provider

    def create_story_point_extractor():
        tshirt_mapping = {
            'xs': 1,
            's': 3,
            'm': 6,
            'l': 12,
            'xl': 21
        }
        t_shirt_story_point_extractor = JiraTShirtStoryPointExtractor('customfield_10010',
                                                                      tshirt_mapping,
                                                                      default_story_points_value=1)
        return t_shirt_story_point_extractor

    def create_time_extractor():
        return JiraResolutionTimeIssueTotalSpentTimeExtractor()

    # given
    jql_issue_provider = create_issue_provider(client)
    t_shirt_story_point_extractor = create_story_point_extractor()
    time_extractor = create_time_extractor()

    # when
    velocity_calculator = GeneralizedTeamVelocityCalculator(issue_provider=jql_issue_provider,
                                                            story_point_extractor=t_shirt_story_point_extractor,
                                                            time_extractor=time_extractor)

    velocity = velocity_calculator.calculate(velocity_time_unit=VelocityTimeUnit.DAY)

    # then
    print(velocity)


if __name__ == '__main__':
    JIRA_PASS = ''
    JIRA_LOGIN = ''
    JIRA_SERVER = ''
    jira_client = Jira(JIRA_SERVER, JIRA_LOGIN, JIRA_PASS, cloud=True)

    team_velocity_integration_test(jira_client)
