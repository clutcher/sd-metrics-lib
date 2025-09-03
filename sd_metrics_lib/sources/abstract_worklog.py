from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Iterable, Optional

from sd_metrics_lib.sources.worklog import WorklogExtractor
from sd_metrics_lib.utils.time import Duration, TimeUnit
from sd_metrics_lib.utils.worktime import WorkTimeExtractor, SIMPLE_WORKTIME_EXTRACTOR


class AbstractStatusChangeWorklogExtractor(WorklogExtractor, ABC):

    def __init__(self,
                 transition_statuses: Optional[list[str]] = None,
                 user_filter: Optional[list[str]] = None,
                 worktime_extractor: WorkTimeExtractor = SIMPLE_WORKTIME_EXTRACTOR) -> None:
        self.transition_statuses = transition_statuses
        self.user_filter = user_filter
        self.worktime_extractor = worktime_extractor

        self.interval_start_time: Optional[datetime] = None
        self.interval_end_time: Optional[datetime] = None

    def get_work_time_per_user(self, task) -> Dict[str, Duration]:
        working_time_per_user: Dict[str, Duration] = {}

        changelog_history = list(self._extract_chronological_changes_sequence(task))
        if not changelog_history:
            return working_time_per_user

        last_assigned_user = self._default_assigned_user()
        for changelog_entry in changelog_history:
            is_user_change_entry = self._is_user_change_entry(changelog_entry)
            is_status_change_entry = self._is_status_change_entry(changelog_entry)

            if not is_user_change_entry and not is_status_change_entry:
                continue

            if is_user_change_entry and is_status_change_entry:
                # Combined change: close previous interval under previous assignee, then switch assignee
                previous_assigned_user = last_assigned_user

                last_assigned_user = self._get_current_assignee_from_changelog_when_last_assigned_is_unknown(
                    changelog_entry,
                    last_assigned_user
                )

                self._update_time_intervals_and_sum_worklog(changelog_entry, working_time_per_user,
                                                            previous_assigned_user)

                assignee = self._extract_user_from_change(changelog_entry)
                if self._is_allowed_user(assignee):
                    last_assigned_user = assignee

                if self._is_status_changed_into_required(changelog_entry):
                    if self.interval_start_time is None:
                        self.interval_start_time = self._extract_change_time(changelog_entry)
            elif is_user_change_entry:
                previous_assigned_user = last_assigned_user
                change_time = self._extract_change_time(changelog_entry)
                was_in_interval = self.interval_start_time is not None

                self._update_time_intervals_and_sum_worklog(changelog_entry, working_time_per_user,
                                                            previous_assigned_user)

                assignee = self._extract_user_from_change(changelog_entry)
                if self._is_allowed_user(assignee):
                    last_assigned_user = assignee

                if was_in_interval and not is_status_change_entry and self.interval_start_time is None:
                    self.interval_start_time = change_time
            elif is_status_change_entry:
                last_assigned_user = self._get_current_assignee_from_changelog_when_last_assigned_is_unknown(
                    changelog_entry,
                    last_assigned_user
                )
                self._update_time_intervals_and_sum_worklog(changelog_entry, working_time_per_user, last_assigned_user)

        if self._is_current_status_a_required_status(task):
            self.interval_end_time = self._now()
            self._sum_working_time(working_time_per_user, last_assigned_user)

        return working_time_per_user

    def _update_time_intervals_and_sum_worklog(self, changelog_entry, working_time_per_user, assigned_user):
        change_time = self._extract_change_time(changelog_entry)
        is_user_change = self._is_user_change_entry(changelog_entry)
        is_status_into_required = self._is_status_change_entry(changelog_entry) and self._is_status_changed_into_required(changelog_entry)
        is_status_from_required = self._is_status_change_entry(changelog_entry) and self._is_status_changed_from_required(changelog_entry)

        if is_user_change and self.interval_start_time is not None:
            self.interval_end_time = change_time
            self._sum_working_time(working_time_per_user, assigned_user)
            if is_status_into_required or (not is_status_from_required and self.interval_start_time is not None):
                self.interval_start_time = change_time
            else:
                self._clean_interval_times()
        else:
            # Handle status transitions - these are not mutually exclusive!
            if is_status_from_required and self.interval_start_time is not None:
                self.interval_end_time = change_time
                self._sum_working_time(working_time_per_user, assigned_user)

            if is_status_into_required:
                self.interval_start_time = change_time

    def _get_current_assignee_from_changelog_when_last_assigned_is_unknown(self, changelog_entry, last_assigned_user):
        if last_assigned_user == self._default_assigned_user():
            status_change_author = self._extract_author_from_changelog_entry(changelog_entry)
            if status_change_author and self._is_allowed_user(status_change_author):
                last_assigned_user = status_change_author
        return last_assigned_user

    @abstractmethod
    def _extract_chronological_changes_sequence(self, task) -> Iterable[dict]:
        pass

    @abstractmethod
    def _is_user_change_entry(self, changelog_entry) -> bool:
        pass

    @abstractmethod
    def _is_status_change_entry(self, changelog_entry) -> bool:
        pass

    @abstractmethod
    def _extract_user_from_change(self, changelog_entry) -> str:
        pass

    @abstractmethod
    def _extract_change_time(self, changelog_entry) -> datetime:
        pass

    @abstractmethod
    def _is_status_changed_into_required(self, changelog_entry) -> bool:
        pass

    @abstractmethod
    def _is_status_changed_from_required(self, changelog_entry) -> bool:
        pass

    @abstractmethod
    def _is_current_status_a_required_status(self, task) -> bool:
        pass

    @abstractmethod
    def _extract_author_from_changelog_entry(self, changelog_entry) -> Optional[str]:
        pass

    @staticmethod
    def _default_assigned_user() -> str:
        return 'UNKNOWN'

    def _is_allowed_user(self, user: Optional[str]) -> bool:
        if self.user_filter is None:
            return True
        if user is None:
            return False
        return user in self.user_filter

    @staticmethod
    def _now() -> datetime:
        try:
            return datetime.now().astimezone()
        except Exception:
            return datetime.now()

    def _sum_working_time(self, working_time_per_user: Dict[str, Duration], last_assigned_user: str):
        if self._is_interval_found_for_status_change():
            duration_in_status = self.worktime_extractor.extract_time_from_period(self.interval_start_time,
                                                                                  self.interval_end_time)
            if duration_in_status is not None:
                already_worked_time = working_time_per_user.get(last_assigned_user, Duration.zero())
                working_time_per_user[last_assigned_user] = already_worked_time.add(duration_in_status,
                                                                                    unit=TimeUnit.SECOND)
            self._clean_interval_times()

    def _is_interval_found_for_status_change(self):
        return self.interval_start_time is not None and self.interval_end_time is not None

    def _clean_interval_times(self):
        self.interval_start_time = None
        self.interval_end_time = None
