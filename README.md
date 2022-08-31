# sd-metrics-lib

Python library for calculation of various metrics related to software development process. Provides user velocity
calculation based on data from Jira. Metrics calculation classes are using interfaces, so it could be easily extended
with another data providers, like Trello, Asana etc. from application code.

## Implementation notes

General architecture is simple and has 2 main parts:

+ _calculators_ package:
    + **UserVelocityCalculator** class calculates user velocity or developer performance in other words. Requires
      IssueProvider, StoryPointExtractor and WorklogExtractor for calculation.
+ _data_providers_ package:
    + **IssueProvider** interface designed to provide issues/tickets for calculators.
        + **JiraIssueProvider** implementation class, which fetches issues from Jira by JQL using jira client
          from [atlassian-python-api](https://pypi.org/project/atlassian-python-api/).
        + **ProxyIssueProvider** wrapper for issues fetched from another data providers.
    + **StoryPointExtractor** interface designed to extract "story points" from issue.
        + **JiraCustomFieldStoryPointExtractor** implementation class, which extract value of custom field from Jira.
        + **JiraTShirtStoryPointExtractor** implementation class, which extract value of custom field from Jira and maps
          string value into numbers.
    + **WorklogExtractor** interface designed to extract amount of time users spent on ticket.
        + **JiraWorklogExtractor** implementation class, which uses regular jira work log entries to define user spent
          time.
        + **JiraStatusChangeWorklogExtractor** implementation class, which uses issue status change history log to
          define user spent time on issue.
        + **ChainedWorklogExtractor** implementation class, which allows "chain" **WorklogExtractor** to execute them
          one by one.

## Code examples

### Calculate amount of tickets developer resolves per day based on Jira ticket status change history.

This code should work on any project and give at least some data for analysis.

```python
from atlassian import Jira

from calculators import UserVelocityCalculator
from calculators.velocity_calculator import VelocityTimeUnit
from data_providers.jira.issue_provider import JiraIssueProvider
from data_providers.jira.worklog_extractor import JiraStatusChangeWorklogExtractor
from data_providers.story_point_extractor import ConstantStoryPointExtractor

JIRA_SERVER = 'server_url'
JIRA_LOGIN = 'login'
JIRA_PASS = 'password'
jira_client = Jira(JIRA_SERVER, JIRA_LOGIN, JIRA_PASS, cloud=True)

jql = " project in ('TBC') AND resolutiondate >= 2022-08-01 "
jql_issue_provider = JiraIssueProvider(jira_client, jql, expand='changelog')

story_point_extractor = ConstantStoryPointExtractor()
jira_worklog_extractor = JiraStatusChangeWorklogExtractor(['In Progress', 'In Development'])

velocity_calculator = UserVelocityCalculator(issue_provider=jql_issue_provider,
                                             story_point_extractor=story_point_extractor,
                                             worklog_extractor=jira_worklog_extractor)
velocity = velocity_calculator.calculate(velocity_time_unit=VelocityTimeUnit.DAY)

print(velocity)
```

### Calculate amount of story points developer resolves per day based on Jira worklog.

This code will provide good enough dev performance metrics on projects, where worklog and story points are entered in
Jira.

```python
from atlassian import Jira

from calculators import UserVelocityCalculator
from calculators.velocity_calculator import VelocityTimeUnit
from data_providers.jira.issue_provider import JiraIssueProvider
from data_providers.jira.worklog_extractor import JiraWorklogExtractor
from data_providers.jira import JiraCustomFieldStoryPointExtractor

JIRA_SERVER = 'server_url'
JIRA_LOGIN = 'login'
JIRA_PASS = 'password'
jira_client = Jira(JIRA_SERVER, JIRA_LOGIN, JIRA_PASS, cloud=True)

jql = " project in ('TBC') AND resolutiondate >= 2022-08-01 "
jql_issue_provider = JiraIssueProvider(jira_client, jql)

story_point_extractor = JiraCustomFieldStoryPointExtractor('customfield_10010')
jira_worklog_extractor = JiraWorklogExtractor(jira_client)

velocity_calculator = UserVelocityCalculator(issue_provider=jql_issue_provider,
                                             story_point_extractor=story_point_extractor,
                                             worklog_extractor=jira_worklog_extractor)
velocity = velocity_calculator.calculate(velocity_time_unit=VelocityTimeUnit.DAY)

print(velocity)
```

## Version history

### 1.0.1

+ **(Bug Fix)** Fix package import exception after installing from pypi.

### 1.0

+ **(Feature)** Add user velocity calculator.