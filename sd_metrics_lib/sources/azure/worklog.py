from datetime import datetime
from typing import Optional, List

from sd_metrics_lib.sources.abstract_worklog import AbstractStatusChangeWorklogExtractor
from sd_metrics_lib.sources.worklog import TaskTotalSpentTimeExtractor
from sd_metrics_lib.utils.worktime import WorkTimeExtractor, SimpleWorkTimeExtractor


class AzureStatusChangeWorklogExtractor(AbstractStatusChangeWorklogExtractor):

    def __init__(self,
                 transition_statuses: Optional[List[str]] = None,
                 user_filter: Optional[List[str]] = None,
                 time_format='%Y-%m-%dT%H:%M:%S.%f%z',
                 use_user_name: bool = True,
                 worktime_extractor: WorkTimeExtractor = SimpleWorkTimeExtractor()) -> None:
        super().__init__(transition_statuses=transition_statuses,
                         user_filter=user_filter,
                         worktime_extractor=worktime_extractor)
        self.time_format = time_format
        self.use_user_name = use_user_name

    def _extract_chronological_changes_sequence(self, task):
        fields = task.fields
        return fields.get('CustomExpand.WorkItemUpdate') or []

    def _is_user_change_entry(self, changelog_entry) -> bool:
        fields = changelog_entry.fields
        return fields and 'System.AssignedTo' in fields and fields['System.AssignedTo'].new_value is not None

    def _is_status_change_entry(self, changelog_entry) -> bool:
        fields = changelog_entry.fields
        return fields and 'System.State' in fields and fields['System.State'].new_value is not None

    def _extract_user_from_change(self, changelog_entry) -> str:
        return changelog_entry.fields['System.AssignedTo'].new_value['uniqueName']

    def _extract_change_time(self, changelog_entry):
        date_string = changelog_entry.fields['System.ChangedDate'].new_value
        try:
            return datetime.strptime(date_string, self.time_format)
        except ValueError:
            # Sometimes Azure API returns time without milliseconds
            return datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S%z')

    def _is_status_changed_into_required(self, changelog_entry) -> bool:
        if self.transition_statuses is None:
            return True
        return changelog_entry.fields['System.State'].new_value in self.transition_statuses

    def _is_status_changed_from_required(self, changelog_entry) -> bool:
        if self.transition_statuses is None:
            return True
        return changelog_entry.fields['System.State'].old_value in self.transition_statuses

    def _is_current_status_a_required_status(self, task) -> bool:
        if self.transition_statuses is None:
            return True
        fields = task.get('fields', {}) if isinstance(task, dict) else {}
        current = fields.get('System.State')
        return current in self.transition_statuses


class AzureTaskTotalSpentTimeExtractor(TaskTotalSpentTimeExtractor):

    def __init__(self, time_format='%Y-%m-%dT%H:%M:%S.%f%z') -> None:
        self.time_format = time_format

    def get_total_spent_time(self, task) -> int:
        resolution_date_str = task.fields['Microsoft.VSTS.Common.ClosedDate']
        if resolution_date_str is None:
            return 0

        resolution_date = self._convert_to_time(resolution_date_str)
        creation_date = self._convert_to_time(task.fields['System.CreatedDate'])
        spent_time = (resolution_date - creation_date)
        return int(spent_time.total_seconds())

    def _convert_to_time(self, date_string: str) -> datetime:
        try:
            return datetime.strptime(date_string, self.time_format)
        except ValueError:
            # Sometimes Azure API returns time without milliseconds
            return datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S%z')
