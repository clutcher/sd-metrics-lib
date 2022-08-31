from atlassian import Jira

from calculators import UserVelocityCalculator
from calculators.velocity_calculator import VelocityTimeUnit
from data_providers.jira.issue_provider import JiraIssueProvider
from data_providers.jira.story_point_extractor import JiraTShirtStoryPointExtractor
from data_providers.jira.worklog_extractor import JiraStatusChangeWorklogExtractor, JiraWorklogExtractor
from data_providers.worklog_extractor import ChainedWorklogExtractor


def user_velocity_integration_test(client):
    def create_issue_provider(jira):
        jql = " type in (Story, Bug, 'Tech Debt', 'Regression Defect') AND project in ('TBC') AND resolutiondate >= 2022-08-01 "
        jql_issue_provider = JiraIssueProvider(jira, jql, expand='changelog')
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

    def create_worklog_extractor(client):
        jira_worklog_extractor = JiraWorklogExtractor(client)
        jira_status_worklog_extractor = JiraStatusChangeWorklogExtractor(['12207', '3'], use_user_name=True)
        return ChainedWorklogExtractor([jira_worklog_extractor, jira_status_worklog_extractor])

    # given
    jql_issue_provider = create_issue_provider(client)
    t_shirt_story_point_extractor = create_story_point_extractor()
    chained_worklog_extractor = create_worklog_extractor(client)

    # when
    velocity_calculator = UserVelocityCalculator(issue_provider=jql_issue_provider,
                                                 story_point_extractor=t_shirt_story_point_extractor,
                                                 worklog_extractor=chained_worklog_extractor)

    velocity = velocity_calculator.calculate(velocity_time_unit=VelocityTimeUnit.DAY)

    # then
    print(velocity)


if __name__ == '__main__':
    JIRA_PASS = ''
    JIRA_LOGIN = ''
    JIRA_SERVER = ''
    jira_client = Jira(JIRA_SERVER, JIRA_LOGIN, JIRA_PASS, cloud=True)

    user_velocity_integration_test(jira_client)
