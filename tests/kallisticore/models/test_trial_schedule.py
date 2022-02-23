from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase

from kallisticore.models.experiment import Experiment
from kallisticore.models.trial_schedule import TrialSchedule, \
    validate_recurrence_pattern


class TestTrialSchedule(TestCase):
    def setUp(self):
        self._experiment = Experiment.create()
        self._recurrence_pattern = '* * * * *'
        self._recurrence_count = 5
        self._parameters = {'test-param': 'test-pram-value'}
        self._ticket = {'test-ticket': 'test-ticket-value'}
        self._trial_schedule = TrialSchedule.create(
            experiment=self._experiment,
            recurrence_pattern=self._recurrence_pattern,
            recurrence_count=self._recurrence_count,
            parameters=self._parameters, ticket=self._ticket)

    def test_validate_recurrence_pattern(self):
        with self.assertRaises(ValidationError):
            validate_recurrence_pattern('invalid-cron-expression')
        self.assertTrue(validate_recurrence_pattern('* * * * *'))

    def test_fetch_all(self):
        trial_schedules = TrialSchedule.objects.all()
        self.assertEqual(len(trial_schedules), 1)

        trial_schedule = trial_schedules[0]
        self.assertIsNotNone(trial_schedule.id)
        self._assert_same_trial_schedule(trial_schedule)

    def test_soft_delete_fetch_all(self):
        trial_schedules = TrialSchedule.objects.all()
        self.assertEqual(len(trial_schedules), 1)

        TrialSchedule.objects.get(id=self._trial_schedule.id).delete()
        trial_schedules = TrialSchedule.objects.all()
        self.assertEqual(len(trial_schedules), 0)

    def test_fetch(self):
        trial_schedule = TrialSchedule.objects.get(id=self._trial_schedule.id)
        self.assertIsNotNone(trial_schedule.id)
        self._assert_same_trial_schedule(trial_schedule)

    def test_soft_delete_fetch(self):
        trial_schedule = TrialSchedule.objects.get(id=self._trial_schedule.id)
        self.assertIsNotNone(trial_schedule.id)

        trial_schedule.delete()

        # objects.get should raise an DoesNotExist error
        with self.assertRaises(TrialSchedule.DoesNotExist):
            TrialSchedule.objects.get(id=trial_schedule.id)

        # objects.get_queryset_all().get() should return the deleted experiment
        trial_schedule = TrialSchedule.objects.get_queryset_all().get(
            id=trial_schedule.id)
        self.assertIsNotNone(trial_schedule.id)
        self._assert_same_trial_schedule(trial_schedule)

    def test_experience_delete(self):
        self.assertIsNone(self._trial_schedule.deleted_at)
        self._experiment.delete()
        self.assertIsNotNone(TrialSchedule.objects.get_queryset_all().get(
            id=self._trial_schedule.id).deleted_at)
        self.assertEqual(0, TrialSchedule.objects.count())

    def test_recurrence_left_on_create_and_update(self):
        self.assertEqual(self._recurrence_count,
                         self._trial_schedule.recurrence_count)
        self.assertEqual(self._recurrence_count,
                         self._trial_schedule.recurrence_left)
        self._trial_schedule.decrement_recurrence_left()
        self.assertEqual(self._recurrence_count,
                         self._trial_schedule.recurrence_count)
        self.assertEqual(self._recurrence_count - 1,
                         self._trial_schedule.recurrence_left)
        new_recurrence_count = self._recurrence_count + 10
        self._trial_schedule.recurrence_count = new_recurrence_count
        self._trial_schedule.save()
        self.assertEqual(new_recurrence_count,
                         self._trial_schedule.recurrence_count)
        self.assertEqual(new_recurrence_count,
                         self._trial_schedule.recurrence_left)

    def test_has_recurrence_count_set(self):
        self.assertTrue(self._trial_schedule.has_recurrence_count_set())

        trial_schedule = TrialSchedule.create(
            experiment=self._experiment,
            recurrence_pattern=self._recurrence_pattern)
        self.assertFalse(trial_schedule.has_recurrence_count_set())

        trial_schedule.recurrence_count = 0
        trial_schedule.save()
        self.assertTrue(self._trial_schedule.has_recurrence_count_set())

    def test_has_recurrence_left(self):
        self.assertTrue(self._trial_schedule.has_recurrence_left())

        trial_schedule = TrialSchedule.create(
            experiment=self._experiment,
            recurrence_pattern=self._recurrence_pattern)
        self.assertFalse(trial_schedule.has_recurrence_left())

        trial_schedule.recurrence_count = 0
        trial_schedule.save()
        self.assertFalse(trial_schedule.has_recurrence_left())

    def test_should_execute_at(self):
        # time logic
        at_datetime = datetime(2019, 1, 1, 0, 0, 0)
        self._trial_schedule.recurrence_pattern = '* * * * *'
        self._trial_schedule.save()
        self.assertFalse(
            self._trial_schedule.should_execute_at(at_datetime, 59))
        self.assertTrue(
            self._trial_schedule.should_execute_at(at_datetime, 60))

        after_60_seconds = at_datetime + timedelta(seconds=60)
        self.assertTrue(
            self._trial_schedule.should_execute_at(after_60_seconds, 60))

        self._trial_schedule.recurrence_pattern = '5 * * * *'
        self._trial_schedule.save()
        self.assertFalse(
            self._trial_schedule.should_execute_at(at_datetime, 60))
        after_4_minutes = at_datetime + timedelta(minutes=4)
        self.assertTrue(
            self._trial_schedule.should_execute_at(after_4_minutes, 60))

        # recurrence count logic
        self._trial_schedule.recurrence_pattern = '* * * * *'
        self._trial_schedule.recurrence_count = 0
        self._trial_schedule.save()
        self.assertFalse(
            self._trial_schedule.should_execute_at(at_datetime, 60))

        self._trial_schedule.recurrence_count = 1
        self._trial_schedule.save()
        self.assertTrue(
            self._trial_schedule.should_execute_at(at_datetime, 60))
        self._trial_schedule.decrement_recurrence_left()
        self.assertFalse(
            self._trial_schedule.should_execute_at(at_datetime, 60))

        self._trial_schedule.recurrence_count = None
        self._trial_schedule.save()
        self.assertTrue(
            self._trial_schedule.should_execute_at(at_datetime, 60))

    def test_decrement_recurrence_left(self):
        self._trial_schedule.decrement_recurrence_left()
        self.assertEqual(self._recurrence_count,
                         self._trial_schedule.recurrence_count)
        self.assertEqual(self._recurrence_count - 1,
                         self._trial_schedule.recurrence_left)

        self._trial_schedule.recurrence_count = None
        self._trial_schedule.save()
        self.assertIsNone(self._trial_schedule.recurrence_left)
        self._trial_schedule.decrement_recurrence_left()
        self.assertIsNone(self._trial_schedule.recurrence_left)

    def _assert_same_trial_schedule(self, trial_schedule: TrialSchedule):
        self.assertEqual(trial_schedule.recurrence_pattern,
                         self._recurrence_pattern)
        self.assertEqual(trial_schedule.experiment_id, self._experiment.id)
        self.assertEqual(trial_schedule.recurrence_count,
                         self._recurrence_count)
        self.assertEqual(trial_schedule.parameters, self._parameters)
        self.assertEqual(trial_schedule.ticket, self._ticket)

    def test_metadata_when_none_defined(self):
        experiment = Experiment.create()
        trial_schedule = TrialSchedule.create(experiment=experiment,
                                              parameters=self._parameters)
        self.assertEqual(trial_schedule.metadata, {})

    def test_metadata_when_experiment_metadata_is_defined(self):
        experiment_metadata = {"test_id": "123456"}
        experiment = Experiment.create(metadata=experiment_metadata)
        trial_schedule = TrialSchedule.create(experiment=experiment,
                                              parameters=self._parameters)
        self.assertEqual(trial_schedule.metadata, experiment_metadata)

    def test_metadata_when_trial_schedule_metadata_is_defined(self):
        trial_schedule_metadata = {"type": "inter_pool"}
        experiment = Experiment.create()
        trial_schedule = TrialSchedule.create(experiment=experiment,
                                              metadata=trial_schedule_metadata,
                                              parameters=self._parameters)
        self.assertEqual(trial_schedule.metadata, trial_schedule_metadata)

    def test_metadata_with_different_keys_defined(self):
        experiment_metadata = {"test_id": "123456"}
        trial_schedule_metadata = {"type": "inter_pool"}
        experiment = Experiment.create(metadata=experiment_metadata)
        trial_schedule = TrialSchedule.create(experiment=experiment,
                                              metadata=trial_schedule_metadata,
                                              parameters=self._parameters)
        self.assertEqual(trial_schedule.metadata,
                         {"test_id": "123456", "type": "inter_pool"})

    def test_metadata_with_same_key_defined(self):
        experiment_metadata = {"type": "high_availability"}
        trial_schedule_metadata = {"type": "inter_pool"}
        experiment = Experiment.create(metadata=experiment_metadata)
        trial_schedule = TrialSchedule.create(experiment=experiment,
                                              metadata=trial_schedule_metadata,
                                              parameters=self._parameters)
        self.assertEqual(trial_schedule.metadata, trial_schedule_metadata)
