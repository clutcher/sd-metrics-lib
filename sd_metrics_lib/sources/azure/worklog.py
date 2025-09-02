from datetime import datetime
from typing import Optional

from sd_metrics_lib.sources.abstract_worklog import AbstractStatusChangeWorklogExtractor
from sd_metrics_lib.sources.worklog import TaskTotalSpentTimeExtractor
from sd_metrics_lib.utils.worktime import WorkTimeExtractor, SimpleWorkTimeExtractor
from sd_metrics_lib.utils.time import Duration, TimeUnit


class AzureStatusChangeWorklogExtractor(AbstractStatusChangeWorklogExtractor):

    def __init__(self,
                 transition_statuses: Optional[list[str]] = None,
                 user_filter: Optional[list[str]] = None,
                 time_format='%Y-%m-%dT%H:%M:%S.%f%z',
                 use_user_name: bool = False,
                 worktime_extractor: WorkTimeExtractor = SimpleWorkTimeExtractor()) -> None:
        super().__init__(transition_statuses=transition_statuses,
                         user_filter=user_filter,
                         worktime_extractor=worktime_extractor)
        self.time_format = time_format
        self.use_user_name = use_user_name

    def _extract_chronological_changes_sequence(self, task):
        fields = task.fields
        return fields.get('CustomExpand.WorkItemUpdate', [])

    def _is_user_change_entry(self, changelog_entry) -> bool:
        fields = changelog_entry.fields
        return fields and 'System.AssignedTo' in fields and fields['System.AssignedTo'].new_value is not None

    def _is_status_change_entry(self, changelog_entry) -> bool:
        fields = changelog_entry.fields
        return fields and 'System.State' in fields and fields['System.State'].new_value is not None

    def _extract_user_from_change(self, changelog_entry) -> str:
        assigned_to = changelog_entry.fields['System.AssignedTo'].new_value
        if self.use_user_name:
            return assigned_to.get(
                'displayName',
                assigned_to.get(
                    'uniqueName',
                    assigned_to.get(
                        'id',
                        self._default_assigned_user()
                    )
                )
            )
        else:
            return assigned_to.get('id', self._default_assigned_user())

    def _extract_change_time(self, changelog_entry):
        date_to_use = None

        fields = changelog_entry.fields
        if fields:
            state_change_field = fields.get('Microsoft.VSTS.Common.StateChangeDate')
            if state_change_field and state_change_field.new_value:
                date_to_use = state_change_field.new_value
            else:
                changed_date_field = fields.get('System.ChangedDate')
                if changed_date_field and changed_date_field.new_value:
                    date_to_use = changed_date_field.new_value

        if not date_to_use:
            # Revised date pretty often contains a placeholder value with date 9999-01-01
            date_to_use = changelog_entry.revised_date

        if isinstance(date_to_use, datetime):
            return date_to_use
        else:
            try:
                return datetime.strptime(date_to_use, self.time_format)
            except ValueError:
                # Sometimes Azure API returns time without milliseconds
                return datetime.strptime(date_to_use, '%Y-%m-%dT%H:%M:%S%z')

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
        current_state = task.fields.get('System.State')
        return current_state in self.transition_statuses

    def _extract_author_from_changelog_entry(self, changelog_entry) -> Optional[str]:
        changed_by = changelog_entry.fields['System.ChangedBy'].new_value
        if changed_by:
            if self.use_user_name:
                return changed_by.get(
                    'displayName',
                    changed_by.get(
                        'uniqueName',
                        changed_by.get(
                            'id',
                            self._default_assigned_user()
                        )
                    )
                )
            else:
                return changed_by.get('id')
        return None


class AzureTaskTotalSpentTimeExtractor(TaskTotalSpentTimeExtractor):

    def __init__(self, time_format='%Y-%m-%dT%H:%M:%S.%f%z') -> None:
        self.time_format = time_format

    def get_total_spent_time(self, task) -> Duration:
        resolution_date_str = task.fields['Microsoft.VSTS.Common.ClosedDate']
        if resolution_date_str is None:
            return Duration.zero()

        resolution_date = self._convert_to_time(resolution_date_str)
        creation_date = self._convert_to_time(task.fields['System.CreatedDate'])
        return Duration.datetime_difference(creation_date, resolution_date, TimeUnit.SECOND)

    def _convert_to_time(self, date_string: str) -> datetime:
        try:
            return datetime.strptime(date_string, self.time_format)
        except ValueError:
            # Sometimes Azure API returns time without milliseconds
            return datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S%z')
