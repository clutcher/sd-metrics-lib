from datetime import datetime
from typing import Optional

from sd_metrics_lib.sources.worklog import WorklogExtractor
from sd_metrics_lib.sources.abstract_worklog import AbstractStatusChangeWorklogExtractor
from sd_metrics_lib.sources.worklog import TaskTotalSpentTimeExtractor
from sd_metrics_lib.utils.worktime import SimpleWorkTimeExtractor, WorkTimeExtractor
from sd_metrics_lib.utils.time import Duration, TimeUnit


class JiraWorklogExtractor(WorklogExtractor):

    def __init__(self, jira_client, user_filter: list[str] = None, include_subtask_worklog=False) -> None:
        self.jira_client = jira_client
        self.user_filter = user_filter
        self.include_subtask_worklog = include_subtask_worklog

    def get_work_time_per_user(self, task):
        worklogs = self._get_worklog_for_task_with_subtasks(task)

        working_time_per_user = {}
        for worklog in worklogs:
            worklog_user = self._extract_user_from_worklog(worklog)
            if self._is_allowed_user(worklog_user):
                worklog_time_spent = self._extract_time_in_seconds_from_worklog(worklog)

                spent_time_from_worklog = Duration.of(worklog_time_spent, TimeUnit.SECOND)
                already_spent_time = working_time_per_user.get(worklog_user, Duration.zero())
                working_time_per_user[worklog_user] = already_spent_time.add(spent_time_from_worklog, unit=TimeUnit.SECOND)

        return working_time_per_user

    def _get_worklog_for_task_with_subtasks(self, task):
        worklogs = []
        worklogs.extend(self._get_worklogs_from_jira(task['key']))
        if self.include_subtask_worklog:
            try:
                sub_task_keys = [subtask["key"] for subtask in task["fields"]["subtasks"]]
                for subtask in sub_task_keys:
                    worklogs.extend(self._get_worklogs_from_jira(subtask))
            except AttributeError:
                pass
        return worklogs

    def _get_worklogs_from_jira(self, task_key: str):
        data = self.jira_client.issue_get_worklog(task_key)
        if 'worklogs' in data:
            return data['worklogs']
        return data

    def _is_allowed_user(self, worklog_user):
        if self.user_filter is None:
            return True
        if worklog_user in self.user_filter:
            return True
        return False

    @staticmethod
    def _extract_time_in_seconds_from_worklog(worklog):
        return worklog["timeSpentSeconds"]

    @staticmethod
    def _extract_user_from_worklog(worklog):
        return worklog["author"]["accountId"]


SIMPLE_WORKTIME_EXTRACTOR = SimpleWorkTimeExtractor()

class JiraStatusChangeWorklogExtractor(AbstractStatusChangeWorklogExtractor):

    def __init__(self, transition_statuses: list[str],
                 user_filter: list[str] = None,
                 time_format='%Y-%m-%dT%H:%M:%S.%f%z',
                 use_user_name=False,
                 use_status_codes=False,
                 worktime_extractor: WorkTimeExtractor = SIMPLE_WORKTIME_EXTRACTOR) -> None:

        super().__init__(transition_statuses=transition_statuses,
                         user_filter=user_filter,
                         worktime_extractor=worktime_extractor)
        self.time_format = time_format
        self.use_user_name = use_user_name
        self.use_status_codes = use_status_codes

    def _extract_chronological_changes_sequence(self, task):
        if not isinstance(task, dict):
            return []
        if 'changelog' not in task or 'histories' not in task['changelog']:
            return []

        changelog_history = []
        changelog = task['changelog']['histories']
        for history_entry in changelog:
            if 'items' not in history_entry:
                continue
            for history_entry_item in history_entry['items']:
                if self._is_status_change_entry(history_entry_item) or self._is_user_change_entry(history_entry_item):
                    history_entry_item['created'] = history_entry['created']
                    history_entry_item['author'] = history_entry.get('author', {})
                    changelog_history.append(history_entry_item)

        changelog_history.reverse()  # Jira returns newest first; reverse to chronological
        return changelog_history

    def _is_user_change_entry(self, changelog_entry):
        return 'fieldId' in changelog_entry and changelog_entry['fieldId'] == 'assignee'

    def _is_status_change_entry(self, changelog_entry):
        return 'fieldId' in changelog_entry and changelog_entry['fieldId'] == 'status'

    def _extract_user_from_change(self, changelog_entry):
        if self.use_user_name:
            return changelog_entry['toString']
        else:
            return changelog_entry['to']

    def _extract_change_time(self, changelog_entry):
        return datetime.strptime(changelog_entry['created'], self.time_format)

    def _is_status_changed_into_required(self, changelog_entry):
        if self.transition_statuses is None:
            return True
        if self.use_status_codes:
            return changelog_entry['to'] in self.transition_statuses
        else:
            return changelog_entry['toString'] in self.transition_statuses

    def _is_status_changed_from_required(self, changelog_entry):
        if self.transition_statuses is None:
            return True
        if self.use_status_codes:
            return changelog_entry['from'] in self.transition_statuses
        else:
            return changelog_entry['fromString'] in self.transition_statuses

    def _is_current_status_a_required_status(self, task):
        if self.transition_statuses is None:
            return True
        if 'fields' not in task or 'status' not in task['fields']:
            return False
        if self.use_status_codes:
            return task['fields']['status']['id'] in self.transition_statuses
        else:
            return task['fields']['status']['name'] in self.transition_statuses

    def _extract_author_from_changelog_entry(self, changelog_entry) -> Optional[str]:
        author = changelog_entry.get('author', {})
        if not author:
            return None

        if self.use_user_name:
            return author.get('displayName')
        else:
            return author.get('accountId')


class JiraResolutionTimeTaskTotalSpentTimeExtractor(TaskTotalSpentTimeExtractor):

    def __init__(self, time_format='%Y-%m-%dT%H:%M:%S.%f%z') -> None:
        self.time_format = time_format

    def get_total_spent_time(self, task) -> Duration:
        resolution_date_str = task['fields']['resolutiondate']
        if resolution_date_str is None:
            return Duration.zero()

        resolution_date = datetime.strptime(resolution_date_str, self.time_format)
        creation_date = datetime.strptime(task['fields']['created'], self.time_format)
        return Duration.datetime_difference(creation_date, resolution_date, TimeUnit.SECOND)

