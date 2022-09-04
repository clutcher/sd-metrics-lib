from datetime import datetime, date, timedelta
from typing import Dict

from calculators.utils import time_utils
from data_providers import WorklogExtractor
from data_providers.worklog_extractor import IssueTotalSpentTimeExtractor

WEEKDAY_FRIDAY = 4  # date.weekday() starts with 0


class JiraWorklogExtractor(WorklogExtractor):

    def __init__(self, jira_client, user_filter: list[str] = None, include_subtask_worklog=False) -> None:
        self.jira_client = jira_client
        self.user_filter = user_filter
        self.include_subtask_worklog = include_subtask_worklog

    def get_work_time_per_user(self, issue):
        worklogs = self._get_worklog_for_issue_with_subtasks(issue)

        working_time_per_user = {}
        for worklog in worklogs:
            worklog_user = self._extract_user_from_worklog(worklog)
            if self._is_allowed_user(worklog_user):
                worklog_time_spent = self._extract_time_in_seconds_from_worklog(worklog)

                working_time_per_user[worklog_user] = working_time_per_user.get(worklog_user, 0) + worklog_time_spent

        return working_time_per_user

    def _get_worklog_for_issue_with_subtasks(self, issue):
        worklogs = []
        worklogs.extend(self._get_worklogs_from_jira(issue['key']))
        if self.include_subtask_worklog:
            try:
                sub_task_keys = [subtask["key"] for subtask in issue["fields"]["subtasks"]]
                for subtask in sub_task_keys:
                    worklogs.extend(self._get_worklogs_from_jira(subtask))
            except AttributeError:
                pass
        return worklogs

    def _get_worklogs_from_jira(self, issue_key: str):
        data = self.jira_client.issue_get_worklog(issue_key)
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


class JiraStatusChangeWorklogExtractor(WorklogExtractor):

    def __init__(self, transition_statuses: list[str],
                 user_filter: list[str] = None,
                 time_format='%Y-%m-%dT%H:%M:%S.%f%z',
                 use_user_name=False,
                 use_status_codes=False) -> None:

        self.transition_status_codes = transition_statuses
        self.use_status_codes = use_status_codes
        self.user_filter = user_filter

        self.time_format = time_format

        self.use_user_name = use_user_name
        self.interval_start_time = None
        self.interval_end_time = None

    def get_work_time_per_user(self, issue) -> Dict[str, int]:
        working_time_per_user = {}

        changelog_history = self._extract_issue_changelog_history(issue)
        if len(changelog_history) == 0:
            return working_time_per_user

        last_assigned_user = self._default_assigned_user()
        for changelog_entry in changelog_history:
            if self.__is_user_change_entry(changelog_entry):
                assignee = self._extract_user_from_changelog(changelog_entry)
                if self._is_allowed_user(assignee):
                    last_assigned_user = assignee

            if self._is_status_change_entry(changelog_entry):
                if self._is_status_changed_into_required(changelog_entry):
                    self.interval_start_time = datetime.strptime(changelog_entry['created'], self.time_format)

                if self._is_status_changed_from_required(changelog_entry):
                    self.interval_end_time = datetime.strptime(changelog_entry['created'], self.time_format)

                if self.__is_interval_found_for_status_change():
                    seconds_in_status = self._extract_working_time_from_period(self.interval_start_time,
                                                                               self.interval_end_time)
                    if seconds_in_status is not None:
                        working_time_per_user[last_assigned_user] = working_time_per_user.get(
                            last_assigned_user, 0) + seconds_in_status

                    self.__clean_interval_times()

        return working_time_per_user

    @staticmethod
    def _extract_issue_changelog_history(issue):
        """ Create a flat list of changelog history entries and add created time into each history entry """

        if 'changelog' not in issue or 'histories' not in issue['changelog']:
            return []

        changelog_history = []
        changelog = issue['changelog']['histories']
        for history_entry in changelog:
            if 'items' in history_entry:
                for history_entry_item in history_entry['items']:
                    history_entry_item['created'] = history_entry['created']
                    changelog_history.append(history_entry_item)

        # Jira API sends changelog in last entry first
        # so we want to reverse it to iterate for better iteration
        changelog_history.reverse()
        return changelog_history

    def _extract_working_time_from_period(self, start_time_period, end_time_period) -> int | None:
        # Use businesstimedelta lib for more precision calculation
        period_delta = end_time_period - start_time_period

        if period_delta.days > 0:
            work_days = self.__count_work_days(start_time_period, end_time_period)
            round_up_period_days = period_delta.days + 1
            return min(work_days, round_up_period_days) * time_utils.get_seconds_in_day()
        elif period_delta.total_seconds() < 15 * 60:
            return None
        elif period_delta.total_seconds() < time_utils.get_seconds_in_day():
            return period_delta.total_seconds()
        else:
            return time_utils.get_seconds_in_day()

    def _extract_user_from_changelog(self, changelog_entry):
        if self.use_user_name:
            return changelog_entry['toString']
        else:
            return changelog_entry['to']

    @staticmethod
    def __count_work_days(start_date: date, end_date: date):
        # if the start date is on a weekend, forward the date to next Monday
        if start_date.weekday() > WEEKDAY_FRIDAY:
            start_date = start_date + timedelta(days=7 - start_date.weekday())

        # if the end date is on a weekend, rewind the date to the previous Friday
        if end_date.weekday() > WEEKDAY_FRIDAY:
            end_date = end_date - timedelta(days=end_date.weekday() - WEEKDAY_FRIDAY)

        if start_date > end_date:
            return 0
        # that makes the difference easy, no remainders etc
        diff_days = (end_date - start_date).days + 1
        weeks = int(diff_days / 7)

        remainder = end_date.weekday() - start_date.weekday() + 1
        if remainder != 0 and end_date.weekday() < start_date.weekday():
            remainder = 5 + remainder

        return weeks * 5 + remainder

    def _is_allowed_user(self, last_assigned):
        if self.user_filter is None:
            return True
        if last_assigned in self.user_filter:
            return True
        return False

    @staticmethod
    def _is_status_change_entry(changelog_entry):
        return 'fieldId' in changelog_entry and changelog_entry['fieldId'] == 'status'

    @staticmethod
    def __is_user_change_entry(changelog_entry):
        return 'fieldId' in changelog_entry and changelog_entry['fieldId'] == 'assignee'

    @staticmethod
    def _default_assigned_user():
        return 'UNKNOWN'

    def _is_status_changed_into_required(self, changelog_entry):
        if self.transition_status_codes is None:
            return True
        if self.use_status_codes:
            return changelog_entry['to'] in self.transition_status_codes
        else:
            return changelog_entry['toString'] in self.transition_status_codes

    def _is_status_changed_from_required(self, changelog_entry):
        if self.transition_status_codes is None:
            return True
        if self.use_status_codes:
            return changelog_entry['from'] in self.transition_status_codes
        else:
            return changelog_entry['fromString'] in self.transition_status_codes

    def __is_interval_found_for_status_change(self):
        return self.interval_start_time is not None and self.interval_end_time is not None

    def __clean_interval_times(self):
        self.interval_start_time = None
        self.interval_end_time = None


class JiraResolutionTimeIssueTotalSpentTimeExtractor(IssueTotalSpentTimeExtractor):

    def __init__(self, time_format='%Y-%m-%dT%H:%M:%S.%f%z', ) -> None:
        self.time_format = time_format

    def get_total_spent_time(self, issue) -> int:
        resolution_date_str = issue['fields']['resolutiondate']
        if resolution_date_str is None:
            return 0

        resolution_date = datetime.strptime(resolution_date_str, self.time_format)
        creation_date = datetime.strptime(issue['fields']['created'], self.time_format)
        spent_time = (resolution_date - creation_date)
        return int(spent_time.total_seconds())
