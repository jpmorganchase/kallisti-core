from datetime import datetime
from unittest import mock

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from kallisticore import signals
from kallisticore.models import Experiment, Trial
from kallisticore.models.step import Step
from kallisticore.models.trial import TrialStatus, validate_trial_status, \
    validate_trial_ticket
from kallisticore.signals import execute_plan_for_trial


class TestTrialStatus(TestCase):
    def test_trial_status_values(self):
        self.assertEqual("Failed", TrialStatus.FAILED.value)
        self.assertEqual("Succeeded", TrialStatus.SUCCEEDED.value)
        self.assertEqual("Scheduled", TrialStatus.SCHEDULED.value)
        self.assertEqual("In Progress", TrialStatus.IN_PROGRESS.value)
        self.assertEqual("Invalid", TrialStatus.INVALID.value)
        self.assertEqual("Aborted", TrialStatus.ABORTED.value)


class TestTrialWithoutInterpolation(TestCase):
    def setUp(self):
        self.pre_steps = [{"step": "name",
                           "do": "cm.http_probe",
                           "where": {"url": "https://app.test"}}]
        self.steps = [{"step": "name",
                       "do": "cf.stop_app",
                       "where": {"app_name": "hello-world",
                                 "cf_api_url": "https://cf-api.test"}}]
        self.post_steps = [{"step": "name",
                            "do": "cf.start_app",
                            "where": {"app_name": "hello-world",
                                      "cf_api_url": "https://cf-api.test"}}]
        self._experiment = Experiment.create(
            name='one-action',
            description='one action description',
            pre_steps=Step.convert_to_steps(self.pre_steps),
            steps=Step.convert_to_steps(self.steps),
            post_steps=Step.convert_to_steps(self.post_steps),
        )

        signals.post_save.disconnect(execute_plan_for_trial, sender=Trial)
        self._trial = Trial.create(experiment=self._experiment)

    def tearDown(self):
        signals.post_save.connect(execute_plan_for_trial, sender=Trial)

    def test_get_steps(self):
        actual = self._trial.get_steps()
        expected = [{"step": "name",
                     "do": "cf.stop_app",
                     "where": {"app_name": "hello-world",
                               "cf_api_url": "https://cf-api.test"}}]
        self.assertEqual(1, len(actual))
        self.assertEqual(Step.build(expected[0]).to_dict(),
                         actual[0].to_dict())

    def test_get_post_steps(self):
        actual = self._trial.get_post_steps()
        expected = [{"step": "name",
                     "do": "cf.start_app",
                     "where": {"app_name": "hello-world",
                               "cf_api_url": "https://cf-api.test"}}]
        self.assertEqual(1, len(actual))
        self.assertEqual(Step.build(expected[0]).to_dict(),
                         actual[0].to_dict())

    def test_get_pre_steps(self):
        actual = self._trial.get_pre_steps()
        expected = [{"step": "name",
                     "do": "cm.http_probe",
                     "where": {"url": "https://app.test"}}]
        self.assertEqual(1, len(actual))
        self.assertEqual(Step.build(expected[0]).to_dict(),
                         actual[0].to_dict())


class TestTrialWithInterpolation(TestCase):
    def setUp(self):
        self.parameters = {"app_name": "hello-world",
                           "url": "https://app.test",
                           "cf_api_url": "https://cf-api.test"}
        self.pre_steps = [{"step": "name",
                           "do": "cm.http_probe",
                           "where": {"url": "{{url}}"}}]
        self.steps = [{"step": "name",
                       "do": "cf.stop_app",
                       "where": {"app_name": "{{app_name}}",
                                 "cf_api_url": "{{cf_api_url}}"}}]
        self.post_steps = [{"step": "name",
                            "do": "cf.start_app",
                            "where": {"app_name": "{{app_name}}",
                                      "cf_api_url": "{{cf_api_url}}"}}]
        self._experiment = Experiment.create(
            name='one-action',
            description='one action description',
            pre_steps=Step.convert_to_steps(self.pre_steps),
            steps=Step.convert_to_steps(self.steps),
            post_steps=Step.convert_to_steps(self.post_steps),
        )
        signals.post_save.disconnect(execute_plan_for_trial, sender=Trial)
        self._trial = Trial.create(experiment=self._experiment,
                                   parameters=self.parameters)

    def tearDown(self):
        signals.post_save.connect(execute_plan_for_trial, sender=Trial)

    def test_trial_is_created(self):
        self.assertEqual(self._experiment, self._trial.experiment)
        self.assertEqual(TrialStatus.SCHEDULED.value, self._trial.status)

    def test_trial_fetch_all(self):
        go_web_trials = Trial.objects.all()
        self.assertEqual(len(go_web_trials), 1)

        go_web_trial = go_web_trials[0]
        self.assertEqual(self._experiment, go_web_trial.experiment)
        self.assertEqual(TrialStatus.SCHEDULED.value, go_web_trial.status)

    def test_trial_soft_delete_experiment_fetch_all(self):
        go_web_trials = Trial.objects.all()
        self.assertEqual(len(go_web_trials), 1)

        Experiment.objects.get(id=go_web_trials[0].experiment.id).delete()

        go_web_trials = Trial.objects.all()
        self.assertEqual(len(go_web_trials), 0)

    def test_trial_fetch(self):
        go_web_trial = Trial.objects.get(id=self._trial.id)
        self.assertEqual(go_web_trial, self._trial)

    def test_trial_soft_delete_experiment_fetch(self):
        Experiment.objects.get(id=self._experiment.id).delete()

        # objects.get should raise an DoesNotExist error
        with self.assertRaises(Trial.DoesNotExist):
            Trial.objects.get(id=self._trial.id)

        # objects.get_queryset_all().get() should return the trial
        # from deleted experiment
        go_web_trial = Trial.objects.get_queryset_all().get(id=self._trial.id)
        self.assertEqual(go_web_trial, self._trial)

    def test_trial_state_allows_valid_status_to_be_saved(self):
        for trial_status in TrialStatus:
            self._trial.status = trial_status.value

            self.assertEqual(None, self._trial.save())
            self.assertEqual(trial_status.value, self._trial.status)

    def test_trial_state_does_not_allow_invalid_status_to_be_saved(self):
        with self.assertRaises(ValidationError) as error:
            Trial.create(experiment=self._experiment, status="INVALID_STATE")

        self.assertEqual(['INVALID_STATE is not a valid trial status'],
                         error.exception.messages)

    def test_trial_update_status_saves_trial_status_to_given_value(self):
        self._trial.update_status(TrialStatus.SUCCEEDED)
        self.assertEqual(self._trial.status, TrialStatus.SUCCEEDED.value)

    def test_trial_completed_at_is_set_to_None(self):
        self.assertIsNone(self._trial.completed_at)

    def test_trial_update_status_succeeded_update_completed_at(self):
        self._trial.update_status(TrialStatus.SUCCEEDED)
        self.assertEqual(self._trial.status, TrialStatus.SUCCEEDED.value)
        self.assertIsInstance(self._trial.completed_at, timezone.datetime)

    def test_trial_update_status_failed_update_completed_at(self):
        self._trial.update_status(TrialStatus.FAILED)
        self.assertEqual(self._trial.status, TrialStatus.FAILED.value)
        self.assertIsInstance(self._trial.completed_at, timezone.datetime)

    def test_trial_update_status_aborted_update_completed_at(self):
        self._trial.update_status(TrialStatus.ABORTED)
        self.assertEqual(self._trial.status, TrialStatus.ABORTED.value)
        self.assertIsInstance(self._trial.completed_at, timezone.datetime)

    def test_trial_update_status_created_doesnt_update_completed_at(self):
        self._trial.update_status(TrialStatus.SCHEDULED)
        self.assertEqual(self._trial.status, TrialStatus.SCHEDULED.value)
        self.assertEqual(self._trial.completed_at, None)

    def test_trial_update_status_in_progress_doesnt_update_completed_at(self):
        self._trial.update_status(TrialStatus.IN_PROGRESS)
        self.assertEqual(self._trial.status, TrialStatus.IN_PROGRESS.value)
        self.assertEqual(self._trial.completed_at, None)

    def test_trial_executed_at_is_set_to_None(self):
        self.assertIsNone(self._trial.executed_at)

    def test_trial_update_executed_at_sets_date_time_to_now(self):
        self._trial.update_executed_at()
        self.assertIsInstance(self._trial.executed_at, timezone.datetime)

    def test_trial_get_steps(self):
        actual = self._trial.get_steps()
        expected = [{"step": "name",
                     "do": "cf.stop_app",
                     "where": {"app_name": "hello-world",
                               "cf_api_url": "https://cf-api.test"}}]

        self.assertEqual(1, len(actual))
        self.assertEqual(Step.build(expected[0]).to_dict(),
                         actual[0].to_dict())

    def test_get_post_steps(self):
        actual = self._trial.get_post_steps()
        expected = [{"step": "name",
                     "do": "cf.start_app",
                     "where": {"app_name": "hello-world",
                               "cf_api_url": "https://cf-api.test"}}]
        self.assertEqual(1, len(actual))
        self.assertEqual(Step.build(expected[0]).to_dict(),
                         actual[0].to_dict())

    def test_get_pre_steps(self):
        actual = self._trial.get_pre_steps()
        expected = [{"step": "name",
                     "do": "cm.http_probe",
                     "where": {"url": "https://app.test"}}]

        self.assertEqual(1, len(actual))
        self.assertEqual(Step.build(expected[0]).to_dict(),
                         actual[0].to_dict())

    def test_trial_is_related_to_experiment(self):
        self.assertIn(self._trial.id,
                      self._experiment.trials.values_list('id', flat=True))
        self.assertIn(self._trial.status,
                      self._experiment.trials.values_list('status', flat=True))


class TestValidateTrialStatus(TestCase):
    def test_returns_true_when_passed_a_valid_trial_status(self):
        self.assertEqual(True, validate_trial_status(TrialStatus.FAILED.value))

    def test_validation_error_for_invalid_trial_status(self):
        with self.assertRaises(ValidationError) as error:
            validate_trial_status("NEVER-WILL-IT-BE-THIS-STATE")
        self.assertEqual(
            ['NEVER-WILL-IT-BE-THIS-STATE is not a valid trial status'],
            error.exception.messages)


class TestValidateTrialTicket(TestCase):
    def test_returns_true_when_passed_a_valid_trial_ticket(self):
        with mock.patch('kallisticore.models.trial.ALLOWED_TRIAL_TICKET_KEYS',
                        ['allowed-key']):
            self.assertEqual(True, validate_trial_ticket(
                {'type': 'allowed-key', 'number': 'ABC1234'}))

    def test_validation_error_for_invalid_ticket(self):
        with self.assertRaises(ValidationError) as error:
            validate_trial_ticket({'invalid': 'ticket'})
        self.assertEqual(["{'invalid': 'ticket'} is not a valid trial ticket"],
                         error.exception.messages)

    def test_validation_error_for_additional_field(self):
        with self.assertRaises(ValidationError) as error:
            validate_trial_ticket({'type': 'test-system', 'number': 'ABC123',
                                   'additional': 'field'})
        self.assertEqual(
            ["{'type': 'test-system', 'number': 'ABC123', "
             "'additional': 'field'} is not a valid trial ticket"],
            error.exception.messages)

    def test_validation_error_for_invalid_ticket_type(self):
        with self.assertRaises(ValidationError) as error:
            validate_trial_ticket({'type': 'invalid',
                                   'number': 'ABC123'})
        self.assertEqual(["{'type': 'invalid', 'number': 'ABC123'} is "
                          "not a valid trial ticket"],
                         error.exception.messages)


class TestTrialMetadata(TestCase):
    def setUp(self):
        self.parameters = {"app_name": "hello-world",
                           "cf_api_url": "https://cf-api.test"}
        self.steps = [{"step": "name",
                       "do": "cf.stop_app",
                       "where": {"app_name": "{{app_name}}",
                                 "cf_api_url": "{{cf_api_url}}"}}]
        self.post_steps = [{"step": "name",
                            "do": "cf.start_app",
                            "where": {"app_name": "{{app_name}}",
                                      "cf_api_url": "{{cf_api_url}}"}}]

    def tearDown(self):
        signals.post_save.connect(execute_plan_for_trial, sender=Trial)

    def test_metadata_when_experiment_and_trial_metadata_are_not_defined(self):
        experiment = Experiment.create(
            name='one-action',
            description='one action description',
            steps=Step.convert_to_steps(self.steps),
            post_steps=Step.convert_to_steps(self.post_steps),
        )
        signals.post_save.disconnect(execute_plan_for_trial, sender=Trial)
        trial = Trial.create(experiment=experiment, parameters=self.parameters)
        self.assertEqual(trial.metadata, {})

    def test_metadata_when_experiment_metadata_is_defined(self):
        experiment_metadata = {"meta_data_example": "123456"}
        experiment = Experiment.create(
            name='one-action',
            description='one action description',
            metadata=experiment_metadata,
            steps=Step.convert_to_steps(self.steps),
            post_steps=Step.convert_to_steps(self.post_steps),
        )
        signals.post_save.disconnect(execute_plan_for_trial, sender=Trial)
        trial = Trial.create(experiment=experiment, parameters=self.parameters)
        self.assertEqual(trial.metadata, experiment_metadata)

    def test_metadata_when_trial_metadata_is_defined(self):
        trial_metadata = {"type": "inter_pool"}
        experiment = Experiment.create(
            name='one-action',
            description='one action description',
            steps=Step.convert_to_steps(self.steps),
            post_steps=Step.convert_to_steps(self.post_steps),
        )
        signals.post_save.disconnect(execute_plan_for_trial, sender=Trial)
        trial = Trial.create(experiment=experiment, metadata=trial_metadata,
                             parameters=self.parameters)
        self.assertEqual(trial.metadata, trial_metadata)

    def test_metadata_for_different_keys_defined(self):
        experiment_metadata = {"test_id": "123456"}
        trial_metadata = {"type": "inter_pool"}
        experiment = Experiment.create(
            name='one-action',
            description='one action description',
            metadata=experiment_metadata,
            steps=Step.convert_to_steps(self.steps),
            post_steps=Step.convert_to_steps(self.post_steps),
        )
        signals.post_save.disconnect(execute_plan_for_trial, sender=Trial)
        trial = Trial.create(experiment=experiment, metadata=trial_metadata,
                             parameters=self.parameters)
        self.assertEqual(trial.metadata,
                         {"test_id": "123456", "type": "inter_pool"})

    def test_metadata_for_same_key_defined(self):
        experiment_metadata = {"type": "high_availability"}
        trial_metadata = {"type": "inter_pool"}
        experiment = Experiment.create(
            name='one-action',
            description='one action description',
            metadata=experiment_metadata,
            steps=Step.convert_to_steps(self.steps),
            post_steps=Step.convert_to_steps(self.post_steps),
        )
        signals.post_save.disconnect(execute_plan_for_trial, sender=Trial)
        trial = Trial.create(experiment=experiment, metadata=trial_metadata,
                             parameters=self.parameters)
        self.assertEqual(trial.metadata, trial_metadata)


class TestTrialIsCompleted(TestCase):
    def setUp(self):
        self.steps = [{"step": "name",
                       "do": "cf.stop_app",
                       "where": {"app_name": "{{app_name}}",
                                 "cf_api_url": "{{cf_api_url}}"}}]
        self.experiment = Experiment.create(
            name='one-action',
            description='one action description',
            steps=Step.convert_to_steps(self.steps)
        )
        signals.post_save.disconnect(execute_plan_for_trial, sender=Trial)

    def tearDown(self):
        signals.post_save.connect(execute_plan_for_trial, sender=Trial)

    def test_completed_at_present(self):
        trial = Trial.create(experiment=self.experiment,
                             completed_at=datetime.now())
        self.assertTrue(trial.is_completed())

    def test_completed_at_not_present(self):
        trial = Trial.create(experiment=self.experiment, completed_at=None)
        self.assertFalse(trial.is_completed())
