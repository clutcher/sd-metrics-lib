import datetime
from concurrent.futures import ThreadPoolExecutor

from atlassian import Jira

from sd_metrics_lib.calculators.velocity import UserVelocityCalculator
from sd_metrics_lib.utils.enums import VelocityTimeUnit
from sd_metrics_lib.sources.jira.query import JiraSearchQueryBuilder
from sd_metrics_lib.sources.jira.story_points import JiraTShirtStoryPointExtractor
from sd_metrics_lib.sources.jira.tasks import JiraTaskProvider
from sd_metrics_lib.sources.jira.worklog import JiraStatusChangeWorklogExtractor, JiraWorklogExtractor
from sd_metrics_lib.sources.tasks import CachingTaskProvider
from sd_metrics_lib.sources.worklog import ChainedWorklogExtractor

CACHE = {}

jira_fetch_executor = ThreadPoolExecutor(thread_name_prefix="jira-fetch")

def user_velocity_integration_test(client, additional_fields=None):
    def create_task_provider(jira):
        qb = JiraSearchQueryBuilder(
            projects=['TBC'],
            task_types=['Story', 'Bug', 'Tech Debt', 'Regression Defect'],
            resolution_dates=(datetime.datetime(2022, 6, 1), None)
        )
        jql = qb.build_query()
        provider = JiraTaskProvider(jira, jql, additional_fields=additional_fields,
                                    # thread_pool_executor=jira_fetch_executor
                                    )
        return CachingTaskProvider(provider, cache=CACHE)

    def create_story_point_extractor():
        tshirt_mapping = {
            'xs': 1,
            's': 3,
            'm': 6,
            'l': 12,
            'xl': 21
        }
        return JiraTShirtStoryPointExtractor('customfield_10010',
                                             tshirt_mapping,
                                             default_story_points_value=1)

    def create_worklog_extractor(jira_client):
        jira_worklog_extractor = JiraWorklogExtractor(jira_client)
        jira_status_worklog_extractor = JiraStatusChangeWorklogExtractor(['12207', '3'], use_user_name=True)
        return ChainedWorklogExtractor([jira_worklog_extractor, jira_status_worklog_extractor])

    # given
    task_provider = create_task_provider(client)
    t_shirt_story_point_extractor = create_story_point_extractor()
    chained_worklog_extractor = create_worklog_extractor(client)

    # when
    velocity_calculator = UserVelocityCalculator(task_provider=task_provider,
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

    user_velocity_integration_test(jira_client, ['changelog'])
