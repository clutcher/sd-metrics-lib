# sd-metrics-lib

Python library for calculating various metrics related to the software development process. Provides developer and team velocity
calculations based on data from Jira and Azure DevOps. Metrics calculation classes use interfaces, so the library can be easily extended
with other data providers (e.g., Trello, Asana) from application code.

## Architecture and API reference

### Overview

This library separates metric calculation from data sourcing. Calculators operate on abstract provider interfaces so you can plug in Jira, Azure DevOps, or your own sources. Below is a structured overview by package with links to the key classes you will use.

### Calculators

- Module: `sd_metrics_lib.calculators.metrics`
    - `MetricCalculator` (abstract): Base interface for all metric calculators (`calculate()`).
- Module: `sd_metrics_lib.calculators.velocity`
    - `AbstractMetricCalculator` (abstract): Adds lazy extraction and shared `calculate()` workflow.
    - `UserVelocityCalculator`: Per-user velocity (story points per time unit). Requires `TaskProvider`, `StoryPointExtractor`, `WorklogExtractor`.
    - `GeneralizedTeamVelocityCalculator`: Team velocity (total story points per time unit). Requires `TaskProvider`, `StoryPointExtractor`, `TaskTotalSpentTimeExtractor`.

### Sources (data providers)

- Module: `sd_metrics_lib.sources.tasks`
    - `TaskProvider` (abstract): Fetches a list of tasks/work items.
    - `ProxyTaskProvider`: Wraps a pre-fetched list of tasks (useful for tests/custom sources).
    - `CachingTaskProvider`: Caches results of any `TaskProvider`. Cache key is built from `provider.query` and `provider.additional_fields`; works with any dict-like cache (e.g., `cachetools.TTLCache`).
- Module: `sd_metrics_lib.sources.story_points`
    - `StoryPointExtractor` (abstract)
    - `ConstantStoryPointExtractor`: Returns a constant story point value (defaults to 1).
    - `FunctionStoryPointExtractor`: Wraps a callable to compute story points from a task.
    - `AttributePathStoryPointExtractor`: Reads story points via dotted attribute/dict path and converts to float with default fallback.
    - Vendor implementations below: `AzureStoryPointExtractor`, `JiraCustomFieldStoryPointExtractor`, `JiraTShirtStoryPointExtractor`.
- Module: `sd_metrics_lib.sources.worklog`
    - `WorklogExtractor` (abstract): Returns mapping `user -> seconds` for a task.
    - `TaskTotalSpentTimeExtractor` (abstract): Returns total time-in-seconds spent on a task.
    - `ChainedWorklogExtractor`: Tries extractors in order and returns the first non-empty result.
    - `FunctionWorklogExtractor`: Wraps a callable to produce per-user seconds dict; coerces keys to str and values to int.
    - `FunctionTotalSpentTimeExtractor`: Wraps a callable returning total seconds; coerces to int with safe defaults.
    - `AttributePathWorklogExtractor`: Reads a dict at a dotted attribute/dict path and normalizes keys/values.
    - `AttributePathTotalSpentTimeExtractor`: Reads a numeric value at a dotted path and converts to int with default fallback.
- Module: `sd_metrics_lib.sources.abstract_worklog`
    - `AbstractStatusChangeWorklogExtractor` (abstract): Derives work time from assignment/status change history; attributes time to assignee and respects optional user filters and `WorkTimeExtractor`.

#### Jira

- Module: `sd_metrics_lib.sources.jira.tasks`
    - `JiraTaskProvider`: Fetch tasks by `JQL` via `atlassian-python-api`; supports paging and optional `ThreadPoolExecutor`.
- Module: `sd_metrics_lib.sources.jira.query`
    - `JiraSearchQueryBuilder`: Builder for `JQL` (project, status, date range, type, team, custom raw filters, order by)
- Module: `sd_metrics_lib.sources.jira.story_points`
    - `JiraCustomFieldStoryPointExtractor`: Reads a numeric custom field; supports default value.
    - `JiraTShirtStoryPointExtractor`: Maps T-shirt sizes (e.g., `S`/`M`/`L`) to numbers from a custom field.
- Module: `sd_metrics_lib.sources.jira.worklog`
    - `JiraWorklogExtractor`: Aggregates time from native Jira worklogs (optionally includes subtasks); optional user filter.
    - `JiraStatusChangeWorklogExtractor`: Derives time from changelog (status/assignee changes); supports username vs `accountId` and status names vs codes; uses a `WorkTimeExtractor`.
    - `JiraResolutionTimeTaskTotalSpentTimeExtractor`: Total time from `created` to `resolutiondate`.

#### Azure DevOps

- Module: `sd_metrics_lib.sources.azure.tasks`
    - `AzureTaskProvider`: Executes `WIQL`; fetches work items in pages (sync or `ThreadPoolExecutor`); can expand updates for status-change-based calculations.
- Module: `sd_metrics_lib.sources.azure.query`
    - `AzureSearchQueryBuilder`: Builder for WIQL (project, status, date range, type, area path/team, custom raw filters, order by)
- Module: `sd_metrics_lib.sources.azure.story_points`
    - `AzureStoryPointExtractor`: Reads story points from a field (default `Microsoft.VSTS.Scheduling.StoryPoints`); robust parsing with default.
- Module: `sd_metrics_lib.sources.azure.worklog`
    - `AzureStatusChangeWorklogExtractor`: Derives per-user time from work item updates (assignment/state changes); supports status filters; uses `WorkTimeExtractor`.
    - `AzureTaskTotalSpentTimeExtractor`: Total time from `System.CreatedDate` to `Microsoft.VSTS.Common.ClosedDate`.

### Utilities

- Module: `sd_metrics_lib.utils.enums`
    - `VelocityTimeUnit` (Enum): values `HOUR`, `DAY`, `WEEK`, `MONTH`
    - `HealthStatus` (Enum): values `GREEN`, `YELLOW`, `ORANGE`, `RED`
    - `SeniorityLevel` (Enum): values `JUNIOR`, `MIDDLE`, `SENIOR`
- Module: `sd_metrics_lib.utils.storypoints`
    - `TShirtMapping`: Helper to convert between T-shirt sizes (`XS`/`S`/`M`/`L`/`XL`) and story points using default mapping `xs=1`, `s=5`, `m=8`, `l=13`, `xl=21`.
- Module: `sd_metrics_lib.utils.time`
    - Constants: `SECONDS_IN_HOUR`, `WORKING_HOURS_PER_DAY`, `WORKING_DAYS_PER_WEEK`, `WORKING_WEEKS_IN_MONTH`, `WEEKDAY_FRIDAY`
    - `get_seconds_in_day() -> int`
    - `convert_time(spent_time_in_seconds, VelocityTimeUnit) -> float`
- Module: `sd_metrics_lib.utils.worktime`
    - `WorkTimeExtractor` (abstract)
    - `SimpleWorkTimeExtractor`: Computes working seconds between two datetimes with business-day heuristics.
    - `BoundarySimpleWorkTimeExtractor`: Like `SimpleWorkTimeExtractor` but clamps to [start, end] boundaries.
- Module: `sd_metrics_lib.utils.cache`
    - `CacheProtocol` (Protocol), `DictProtocol` (Protocol)
    - `DictToCacheProtocolAdapter`: Adapts a dict-like to `CacheProtocol`.
    - `CacheKeyBuilder`: Helpers to build cache keys for data/meta entries.
    - `SupersetResolver`: Finds a superset fieldset for cached data reuse.
- Module: `sd_metrics_lib.utils.generators`
    - `TimeRangeGenerator`: Iterator producing date ranges for the requested `VelocityTimeUnit`

### Public API imports

Use the physical modules directly (no export shims):

- Calculators:
  - `from sd_metrics_lib.calculators.velocity import UserVelocityCalculator, GeneralizedTeamVelocityCalculator`
- Common utilities:
  - `from sd_metrics_lib.utils.enums import VelocityTimeUnit, HealthStatus, SeniorityLevel`
  - `from sd_metrics_lib.utils.storypoints import TShirtMapping`
  - `from sd_metrics_lib.utils.time import SECONDS_IN_HOUR, WORKING_HOURS_PER_DAY, WORKING_DAYS_PER_WEEK, WORKING_WEEKS_IN_MONTH, WEEKDAY_FRIDAY, get_seconds_in_day, convert_time`
  - `from sd_metrics_lib.utils.worktime import WorkTimeExtractor, SimpleWorkTimeExtractor, BoundarySimpleWorkTimeExtractor`
  - `from sd_metrics_lib.utils.generators import TimeRangeGenerator`
  - `from sd_metrics_lib.utils.cache import CacheKeyBuilder, CacheProtocol, DictToCacheProtocolAdapter, SupersetResolver, DictProtocol`
- Sources (providers):
  - `from sd_metrics_lib.sources.tasks import TaskProvider, ProxyTaskProvider, CachingTaskProvider`
  - `from sd_metrics_lib.sources.story_points import StoryPointExtractor, ConstantStoryPointExtractor, FunctionStoryPointExtractor, AttributePathStoryPointExtractor`
  - `from sd_metrics_lib.sources.worklog import WorklogExtractor, ChainedWorklogExtractor, TaskTotalSpentTimeExtractor, FunctionWorklogExtractor, FunctionTotalSpentTimeExtractor, AttributePathWorklogExtractor, AttributePathTotalSpentTimeExtractor`
- Jira:
  - `from sd_metrics_lib.sources.jira.query import JiraSearchQueryBuilder`
  - `from sd_metrics_lib.sources.jira.tasks import JiraTaskProvider`
  - `from sd_metrics_lib.sources.jira.story_points import JiraCustomFieldStoryPointExtractor, JiraTShirtStoryPointExtractor`
  - `from sd_metrics_lib.sources.jira.worklog import JiraWorklogExtractor, JiraStatusChangeWorklogExtractor, JiraResolutionTimeTaskTotalSpentTimeExtractor`
- Azure:
  - `from sd_metrics_lib.sources.azure.query import AzureSearchQueryBuilder`
  - `from sd_metrics_lib.sources.azure.tasks import AzureTaskProvider`
  - `from sd_metrics_lib.sources.azure.story_points import AzureStoryPointExtractor`
  - `from sd_metrics_lib.sources.azure.worklog import AzureStatusChangeWorklogExtractor, AzureTaskTotalSpentTimeExtractor`

## Installation

Install core library:

```bash
pip install sd-metrics-lib
```

Optional extras for providers:

```bash
pip install sd-metrics-lib[jira]
pip install sd-metrics-lib[azure]
```

## Code examples

### Calculate amount of tickets developer resolves per day based on Jira ticket status change history.

This code should work on any project and give at least some data for analysis.

```python
from atlassian import Jira

from sd_metrics_lib.calculators.velocity import UserVelocityCalculator
from sd_metrics_lib.utils.enums import VelocityTimeUnit
from sd_metrics_lib.sources.jira.tasks import JiraTaskProvider
from sd_metrics_lib.sources.jira.worklog import JiraStatusChangeWorklogExtractor
from sd_metrics_lib.sources.jira.story_points import JiraCustomFieldStoryPointExtractor

JIRA_SERVER = 'server_url'
JIRA_LOGIN = 'login'
JIRA_PASS = 'password'
jira_client = Jira(JIRA_SERVER, JIRA_LOGIN, JIRA_PASS, cloud=True)

jql = " project in ('TBC') AND resolutiondate >= 2022-08-01 "
task_provider = JiraTaskProvider(jira_client, jql, additional_fields=['changelog'])

story_point_extractor = JiraCustomFieldStoryPointExtractor('customfield_10010', default_story_points_value=1)
jira_worklog_extractor = JiraStatusChangeWorklogExtractor(['In Progress', 'In Development'])

velocity_calculator = UserVelocityCalculator(task_provider=task_provider,
                                             story_point_extractor=story_point_extractor,
                                             worklog_extractor=jira_worklog_extractor)
velocity = velocity_calculator.calculate(velocity_time_unit=VelocityTimeUnit.DAY)

print(velocity)
```

### Calculate amount of story points developer resolves per day based on Azure DevOps work items.

This example uses Azure DevOps WIQL to fetch closed items and derives time spent per user from status/assignment changes.
It also demonstrates enabling concurrency with a thread pool and caching results with a TTL cache.

```python
from cachetools import TTLCache
from concurrent.futures import ThreadPoolExecutor

from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication

from sd_metrics_lib.calculators.velocity import UserVelocityCalculator
from sd_metrics_lib.utils.enums import VelocityTimeUnit
from sd_metrics_lib.sources.azure.tasks import AzureTaskProvider
from sd_metrics_lib.sources.azure.story_points import AzureStoryPointExtractor
from sd_metrics_lib.sources.azure.worklog import AzureStatusChangeWorklogExtractor
from sd_metrics_lib.sources.tasks import CachingTaskProvider

# Caches and thread pools
JQL_CACHE = TTLCache(maxsize=100, ttl=600)
jira_fetch_executor = ThreadPoolExecutor(max_workers=100, thread_name_prefix="jira-fetch")

ORGANIZATION_URL = 'https://dev.azure.com/your_org'
PERSONAL_ACCESS_TOKEN = 'your_pat'

credentials = BasicAuthentication('', PERSONAL_ACCESS_TOKEN)
connection = Connection(base_url=ORGANIZATION_URL, creds=credentials)
wit_client = connection.clients.get_work_item_tracking_client()

wiql = """
       SELECT [System.Id]
       FROM workitems
       WHERE
           [System.TeamProject] = 'YourProject'
         AND [System.State] IN ('Closed', 'Done', 'Resolved')
         AND [System.WorkItemType] IN ('User Story', 'Bug')
         AND [Microsoft.VSTS.Common.ClosedDate] >= '2025-08-01'
       ORDER BY [System.ChangedDate] DESC \
       """

# Use thread pool and cache
task_provider = AzureTaskProvider(wit_client, query=wiql, thread_pool_executor=jira_fetch_executor)
task_provider = CachingTaskProvider(task_provider, cache=JQL_CACHE)

story_point_extractor = AzureStoryPointExtractor(default_story_points_value=1)
worklog_extractor = AzureStatusChangeWorklogExtractor(transition_statuses=['In Progress'])

velocity_calculator = UserVelocityCalculator(task_provider=task_provider,
                                             story_point_extractor=story_point_extractor,
                                             worklog_extractor=worklog_extractor)
velocity = velocity_calculator.calculate(velocity_time_unit=VelocityTimeUnit.DAY)

print(velocity)
```

## Version history

### 5.0.1

+ (Bug Fix) Fix bad import in utils module

### 5.0

+ (Breaking) Restructure packages and rename files for better import Developer Experience.

+ (Feature) Add proxy style classes for extractors
+ (Bug Fix) Fix tasks id adding in query builders
+ (Bug Fix) Fix not working custom expand field in AzureTaskProvider 

### 4.0

+ (Breaking) Fix circular module import issue

+ (Feature) Add filtering by task ids in Azure and Jira query builders

### 3.0

+ (Breaking) Rename all Issue* terms to Task* across API (IssueProvider -> TaskProvider, IssueTotalSpentTimeExtractor -> TaskTotalSpentTimeExtractor, etc.). Removed backward-compatibility aliases.
+ (Breaking) Change package and method names in JiraSearchQueryBuilder

+ (Feature) Introduce AzureSearchQueryBuilder
+ (Feature) AzureTaskProvider: make changelog history optional via additional fields
+ (Feature) Extend JiraSearchQueryBuilder: custom raw filters; filter by Team; open-ended resolution date
+ (Feature) Rewrite CachingTaskProvider to support Django caches
+ (Feature) Introduce AzureSearchQueryBuilder
+ (Bug Fix) Azure: fetch all tasks beyond 20k limit using stable pagination
+ (Bug Fix) Jira: do not fail on empty search results

### 2.0

+ (Feature) Add integration with Azure DevOps
+ (Breaking) Add a generic CachingIssueProvider to wrap any IssueProvider and remove CachingJiraIssueProvider

### 1.2.1

+ **(Improvement)** Add possibility to adjust init time
+ **(Bug Fix)** Fix bug with wrong cache data fetching
+ **(Bug Fix)** Fix bug in week time period end date resolving

### 1.2

+ **(Feature)** Added BoundarySimpleWorkTimeExtractor
+ **(Improvement)** Filter unneeded changelog items for better performance
+ **(Improvement)** Add T-Shirt to story points mapping util class
+ **(Improvement)** Add helper enums
+ **(Bug Fix)** Fix bug with story points returned instead of spent time
+ **(Bug Fix)** Fix bug with missing time for active status
+ **(Bug Fix)** Fix bug with passing class instances in extractor

### 1.1.4

+ **(Improvement)** Add multithreading support for JiraIssueProvider.

### 1.1.3

+ **(Feature)** Add CachingJiraIssueProvider.

### 1.1.2

+ **(Improvement)** Add story points getter for GeneralizedTeamVelocityCalculator.

### 1.1.1

+ **(Improvement)** Execute data fetching in Jira velocity calculators only once.
+ **(Improvement)** Add story points getter for Jira velocity calculators.

### 1.1

+ **(Feature)** Add team velocity calculator.
+ **(Improvement)** Add JQL filter for last modified data.
+ **(Bug Fix)** Fix wrong user resolving in JiraStatusChangeWorklogExtractor.
+ **(Bug Fix)** Fix resolving more time than spent period of time.
+ **(Bug Fix)** Fix Jira filter query joins without AND.

### 1.0.3

+ **(Improvement)** Add JiraIssueSearchQueryBuilder util class.
+ **(Improvement)** Add TimeRangeGenerator util class.
+ **(Bug Fix)** Fix filtering by status when no status list passed.

### 1.0.2

+ **(Bug Fix)** Fix package import exception after installing from pypi.

### 1.0

+ **(Feature)** Add user velocity calculator.