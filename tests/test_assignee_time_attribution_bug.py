
import unittest
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Dict, Any, Optional, Iterable

from sd_metrics_lib.sources.azure.worklog import AbstractStatusChangeWorklogExtractor
from sd_metrics_lib.utils.time import Duration, TimeUnit
from sd_metrics_lib.utils.worktime import WorkTimeExtractor


@dataclass
class MockField:
    old_value: Optional[str] = None
    new_value: Optional[str] = None


@dataclass
class MockChangelogEntry:
    fields: Dict[str, MockField]
    revised_date: datetime


@dataclass 
class MockTask:
    fields: Dict[str, Any]


class MockWorkTimeExtractor(WorkTimeExtractor):
    """Mock extractor that returns calendar time (not business time) for easier testing."""
    
    def extract_time_from_period(self, start_time_period, end_time_period) -> Duration:
        if end_time_period <= start_time_period:
            return None
        
        # Return actual calendar time difference in seconds
        delta_seconds = (end_time_period - start_time_period).total_seconds()
        
        # Ignore periods shorter than 15 minutes for realism
        if delta_seconds < 900:  # 15 minutes
            return None
            
        return Duration.of(delta_seconds, TimeUnit.SECOND)


class TestableAbstractStatusChangeWorklogExtractor(AbstractStatusChangeWorklogExtractor):
    """Concrete implementation of AbstractStatusChangeWorklogExtractor for testing."""
    
    def __init__(self, transition_statuses=None, user_filter=None, mock_now=None):
        super().__init__(
            transition_statuses=transition_statuses,
            user_filter=user_filter, 
            worktime_extractor=MockWorkTimeExtractor()
        )
        self.mock_now = mock_now

    def _extract_chronological_changes_sequence(self, task) -> Iterable:
        return task.fields.get('changelog_entries', [])

    def _is_user_change_entry(self, changelog_entry) -> bool:
        return 'assignee_change' in changelog_entry.fields

    def _is_status_change_entry(self, changelog_entry) -> bool:
        return 'status_change' in changelog_entry.fields

    def _extract_user_from_change(self, changelog_entry) -> str:
        return changelog_entry.fields['assignee_change'].new_value

    def _extract_change_time(self, changelog_entry) -> datetime:
        return changelog_entry.revised_date

    def _is_status_changed_into_required(self, changelog_entry) -> bool:
        if self.transition_statuses is None:
            return True
        status_field = changelog_entry.fields.get('status_change')
        return status_field and status_field.new_value in self.transition_statuses

    def _is_status_changed_from_required(self, changelog_entry) -> bool:
        if self.transition_statuses is None:
            return True
        status_field = changelog_entry.fields.get('status_change') 
        return status_field and status_field.old_value in self.transition_statuses

    def _is_current_status_a_required_status(self, task) -> bool:
        if self.transition_statuses is None:
            return True
        current_status = task.fields.get('current_status')
        return current_status in self.transition_statuses

    def _extract_author_from_changelog_entry(self, changelog_entry) -> Optional[str]:
        author_field = changelog_entry.fields.get('author')
        return author_field.new_value if author_field else None
    
    def _now(self) -> datetime:
        return self.mock_now if self.mock_now else super()._now()


class AssigneeTimeAttributionTestCase(unittest.TestCase):

    def setUp(self):
        self.igor = 'igor-id'
        self.otoniel = 'otoniel-id'
        self.alice = 'alice-id'

    def test_single_status_tracking_with_assignee_change(self):
        # given
        extractor = TestableAbstractStatusChangeWorklogExtractor(
            transition_statuses=['In Progress']
        )

        changelog_entries = [
            # Jun 25: New → In Progress (Igor)
            MockChangelogEntry(
                fields={
                    'status_change': MockField(old_value='New', new_value='In Progress'),
                    'author': MockField(new_value=self.igor)
                },
                revised_date=datetime(2024, 6, 25, 9, 0, tzinfo=timezone.utc)
            ),
            # Aug 20: In Progress → Pending Acceptance (Igor still assigned)
            MockChangelogEntry(
                fields={
                    'status_change': MockField(old_value='In Progress', new_value='Pending Acceptance'),
                    'author': MockField(new_value=self.igor)
                },
                revised_date=datetime(2024, 8, 20, 17, 30, tzinfo=timezone.utc)
            ),
            # Sep 2: Pending Acceptance → Closed (Otoniel assigned) ← Assignee change
            MockChangelogEntry(
                fields={
                    'status_change': MockField(old_value='Pending Acceptance', new_value='Closed'),
                    'assignee_change': MockField(old_value=self.igor, new_value=self.otoniel),
                    'author': MockField(new_value=self.otoniel)
                },
                revised_date=datetime(2024, 9, 2, 14, 0, tzinfo=timezone.utc)
            )
        ]
        
        task = MockTask(fields={
            'changelog_entries': changelog_entries,
            'current_status': 'Closed'  # Not tracked
        })
        
        result = extractor.get_work_time_per_user(task)

        # then
        expected_igor_seconds = (datetime(2024, 8, 20, 17, 30, tzinfo=timezone.utc) -
                                 datetime(2024, 6, 25, 9, 0, tzinfo=timezone.utc)).total_seconds()

        self.assertIn(self.igor, result)
        self.assertNotIn(self.otoniel, result)
        igor_seconds = result[self.igor].to_seconds()
        self.assertAlmostEqual(igor_seconds, expected_igor_seconds, delta=3600)
    
    def test_multiple_status_tracking_with_assignee_change(self):
        """
        Test Case 2: Multiple status tracking with assignee change.
        
        Timeline (same as above):
        - Jun 25: New → In Progress (Igor)
        - Aug 20: In Progress → Pending Acceptance (Igor) 
        - Sep 2: Pending Acceptance → Closed (Otoniel) ← Assignee change
        
        Expected (tracking 'In Progress', 'Pending Acceptance', 'Closed'):
        - Igor: Jun 25 → Sep 2 = ~69 days (worked In Progress + Pending Acceptance)
        - Otoniel: Sep 2 → now = ~1 day (working in Closed status)
        
        Bug: All time was attributed to Otoniel.
        """
        # given: mock current time to be 1 day after last change
        mock_now = datetime(2024, 9, 3, 14, 0, tzinfo=timezone.utc)

        extractor = TestableAbstractStatusChangeWorklogExtractor(
            transition_statuses=['In Progress', 'Pending Acceptance', 'Closed'],
            mock_now=mock_now
        )
        
        changelog_entries = [
            # Jun 25: New → In Progress (Igor)
            MockChangelogEntry(
                fields={
                    'status_change': MockField(old_value='New', new_value='In Progress'),
                    'author': MockField(new_value=self.igor)
                },
                revised_date=datetime(2024, 6, 25, 9, 0, tzinfo=timezone.utc)
            ),
            # Aug 20: In Progress → Pending Acceptance (Igor)
            MockChangelogEntry(
                fields={
                    'status_change': MockField(old_value='In Progress', new_value='Pending Acceptance'),
                    'author': MockField(new_value=self.igor)
                },
                revised_date=datetime(2024, 8, 20, 17, 30, tzinfo=timezone.utc)
            ),
            # Sep 2: Pending Acceptance → Closed (Otoniel) ← Both status and assignee change
            MockChangelogEntry(
                fields={
                    'status_change': MockField(old_value='Pending Acceptance', new_value='Closed'),
                    'assignee_change': MockField(old_value=self.igor, new_value=self.otoniel),
                    'author': MockField(new_value=self.otoniel)
                },
                revised_date=datetime(2024, 9, 2, 14, 0, tzinfo=timezone.utc)
            )
        ]
        
        task = MockTask(fields={
            'changelog_entries': changelog_entries,
            'current_status': 'Closed'  # Currently tracked
        })
        
        result = extractor.get_work_time_per_user(task)

        # then
        igor_expected_seconds = (datetime(2024, 9, 2, 14, 0, tzinfo=timezone.utc) -
                                 datetime(2024, 6, 25, 9, 0, tzinfo=timezone.utc)).total_seconds()
        otoniel_expected_seconds = (mock_now - datetime(2024, 9, 2, 14, 0, tzinfo=timezone.utc)).total_seconds()

        self.assertIn(self.igor, result)
        self.assertIn(self.otoniel, result)
        igor_seconds = result[self.igor].to_seconds()
        otoniel_seconds = result[self.otoniel].to_seconds()
        self.assertAlmostEqual(igor_seconds, igor_expected_seconds, delta=3600)
        self.assertAlmostEqual(otoniel_seconds, otoniel_expected_seconds, delta=3600)
    
    def test_complex_multiple_assignee_changes(self):
        """
        Test Case 3: Complex scenario with multiple assignee and status changes.
        
        Timeline:
        - Jan 1: New → In Progress (Igor)
        - Jan 15: Assignee change to Alice (still In Progress)
        - Feb 1: In Progress → Review (Alice)
        - Feb 10: Assignee change to Otoniel (still Review)
        - Feb 15: Review → Done (Otoniel)
        
        Expected (tracking 'In Progress', 'Review', 'Done'):
        - Igor: Jan 1 → Jan 15 = 14 days (In Progress)
        - Alice: Jan 15 → Feb 10 = 26 days (In Progress + Review) 
        - Otoniel: Feb 10 → Feb 15 = 5 days (Review + Done)
        """
        print("\n=== Test Case 3: Complex Multiple Changes ===")
        
        # Mock current time to be after all changes
        mock_now = datetime(2024, 2, 16, 12, 0, tzinfo=timezone.utc)
        
        extractor = TestableAbstractStatusChangeWorklogExtractor(
            transition_statuses=['In Progress', 'Review', 'Done'],
            mock_now=mock_now
        )
        
        changelog_entries = [
            # Jan 1: New → In Progress (Igor)
            MockChangelogEntry(
                fields={
                    'status_change': MockField(old_value='New', new_value='In Progress'),
                    'author': MockField(new_value=self.igor)
                },
                revised_date=datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc)
            ),
            # Jan 15: Assignee change to Alice (still In Progress)
            MockChangelogEntry(
                fields={
                    'assignee_change': MockField(old_value=self.igor, new_value=self.alice),
                    'author': MockField(new_value=self.alice)
                },
                revised_date=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)
            ),
            # Feb 1: In Progress → Review (Alice)
            MockChangelogEntry(
                fields={
                    'status_change': MockField(old_value='In Progress', new_value='Review'),
                    'author': MockField(new_value=self.alice)
                },
                revised_date=datetime(2024, 2, 1, 11, 0, tzinfo=timezone.utc)
            ),
            # Feb 10: Assignee change to Otoniel (still Review)
            MockChangelogEntry(
                fields={
                    'assignee_change': MockField(old_value=self.alice, new_value=self.otoniel),
                    'author': MockField(new_value=self.otoniel)
                },
                revised_date=datetime(2024, 2, 10, 14, 0, tzinfo=timezone.utc)
            ),
            # Feb 15: Review → Done (Otoniel)
            MockChangelogEntry(
                fields={
                    'status_change': MockField(old_value='Review', new_value='Done'),
                    'author': MockField(new_value=self.otoniel)
                },
                revised_date=datetime(2024, 2, 15, 16, 0, tzinfo=timezone.utc)
            )
        ]
        
        task = MockTask(fields={
            'changelog_entries': changelog_entries,
            'current_status': 'Done'  # Currently tracked
        })
        
        result = extractor.get_work_time_per_user(task)

        # then: verify all users and approximate durations
        self.assertIn(self.igor, result)
        self.assertIn(self.alice, result)
        self.assertIn(self.otoniel, result)

        igor_days = result[self.igor].to_seconds() / 86400
        alice_days = result[self.alice].to_seconds() / 86400
        otoniel_days = result[self.otoniel].to_seconds() / 86400

        self.assertAlmostEqual(igor_days, 14, delta=2)
        self.assertAlmostEqual(alice_days, 26, delta=2)
        self.assertAlmostEqual(otoniel_days, 6, delta=2)


if __name__ == '__main__':
    unittest.main()