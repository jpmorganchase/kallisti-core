from django.test import TestCase

from kallisticore.models import Trial
from kallisticore.models.experiment import Experiment
from kallisticore.models.trial import TrialStatus
from kallisticore.models.trial_schedule import TrialSchedule
from kallisticore.serializers import TrialScheduleSerializer


class TestTrialScheduleSerializer(TestCase):
    def test_retrieval(self):
        recurrence_pattern = '* * * * *'
        recurrence_count = 5
        parameters = {'test-param': 'test-pram-value'}
        ticket = {'test-ticket': 'test-ticket-value'}
        metadata = {'test-id': '123456'}
        schedule_metadata = {'recurrence': 'weekly'}
        experiment = Experiment.create(metadata=metadata)
        trial_schedule = TrialSchedule.create(
            experiment=experiment, metadata=schedule_metadata,
            recurrence_pattern=recurrence_pattern,
            recurrence_count=recurrence_count, parameters=parameters,
            ticket=ticket)
        trial = Trial.create(experiment=experiment)
        trial_schedule.trials.add(trial)

        data = TrialScheduleSerializer(trial_schedule).data

        self.assertEqual(11, len(data))
        self.assertIsNotNone(data['id'])
        self.assertEqual(data['experiment_id'], experiment.id)
        self.assertEqual(data['metadata'], {'test-id': '123456',
                                            'recurrence': 'weekly'})
        self.assertEqual(data['parameters'], parameters)
        self.assertEqual(data['ticket'], ticket)
        self.assertEqual(data['recurrence_pattern'], recurrence_pattern)
        self.assertEqual(data['recurrence_count'], recurrence_count)
        self.assertEqual(data['recurrence_left'], recurrence_count)
        self.assertIsNotNone(data['created_at'])
        self.assertEqual(data['created_by'], 'unknown')
        self.assertEqual(data['trials'][0]['id'], str(trial.id))
        self.assertEqual(data['trials'][0]['status'],
                         TrialStatus.SCHEDULED.value)
        self.assertIsNone(data['trials'][0]['executed_at'])
