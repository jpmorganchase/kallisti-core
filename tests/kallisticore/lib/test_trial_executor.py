import uuid
from unittest import mock
from unittest.mock import Mock, ANY, call

from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from kallisticore import signals
from kallisticore.lib.observe.observer import Observer
from kallisticore.lib.trial_executor import TrialExecutor, execute_trial
from kallisticore.models import Experiment
from kallisticore.models.step import Step
from kallisticore.models.trial import Trial, TrialStatus
from kallisticore.signals import execute_plan_for_trial


def create_experiment_and_trial(parameters, steps, pre_steps=None,
                                post_steps=None, runtime_parameters=None):
    experiment_name = 'some-experiment-' + str(uuid.uuid4())
    signals.post_save.disconnect(execute_plan_for_trial, sender=Trial)
    experiment = Experiment.create(
        name=experiment_name, parameters=parameters,
        pre_steps=Step.convert_to_steps(pre_steps or []),
        steps=Step.convert_to_steps(steps),
        post_steps=Step.convert_to_steps(post_steps or []))
    trial = Trial.create(experiment=experiment,
                         parameters=(runtime_parameters or {}))
    signals.post_save.connect(execute_plan_for_trial, sender=Trial)
    return trial


class TestTrialExecutor(TestCase):
    module_map = {'cf': 'kallisticore.modules.cloud_foundry'}
    LOG_REC = 'kallisticore.lib.trial_executor.TrialLogRecord'
    STEP_REC = 'kallisticore.lib.trial_executor.TrialStepLogRecord'
    COMMIT = 'kallisticore.lib.trial_executor.TrialLogRecorder.commit'
    CF_GET_APP = 'chaoscf.api.get_app_by_name'
    CF_GET_ORG = 'chaoscf.api.get_org_by_name'
    CF_STOP_APP = 'chaoscf.actions.stop_app'
    CF_START_APP = 'chaoscf.actions.start_app'
    CF_EXEC = 'kallisticore.modules.cloud_foundry.cloud_foundry_action.'\
              'CloudFoundryAction.execute'

    def setUp(self):
        self.app_name = 'hello-world'
        self.org = 'MY-ORG'
        self.cf_api_url = 'https://cf-api.test'
        self.health_endpoint = 'https://health-check.test/health'
        self.parameters = {'cf_org': self.org,
                           'app_name': self.app_name,
                           'cf_api_url': self.cf_api_url}
        self.pre_step_health_check = {
            'step': 'HTTP pre health check',
            'do': 'cm.http_probe',
            'where': {
                'url': '{{ health_endpoint }}'
            }}
        self.step_get_app_by_name = {
            'step': 'Get CF App by Name',
            'do': 'cf.get_app_by_name',
            'where': {
                'cf_api_url': '{{ cf_api_url }}',
                'app_name': '{{ app_name }}',
            }}
        self.step_get_org_by_name = {
            'step': 'Get CF Org by Name',
            'do': 'cf.get_org_by_name',
            'where': {
                'cf_api_url': '{{ cf_api_url }}',
                'org_name': '{{ cf_org }}',
            }}
        self.post_step_health_check = {
            'step': 'HTTP health check',
            'do': 'cm.http_probe',
            'where': {
                'url': '{{health_endpoint}}'
            }}
        self.steps = [self.step_get_app_by_name,
                      self.step_get_org_by_name]
        self.pre_steps = [self.pre_step_health_check]
        self.post_steps = [self.post_step_health_check]
        self.populated_step_get_app_by_name = {
            'step': 'Get CF App by Name',
            'do': 'cf.get_app_by_name',
            'where': {
                'cf_api_url': self.cf_api_url,
                'app_name': self.app_name,
            }}
        self.populated_step_get_org_by_name = {
            'step': 'Get CF Org by Name',
            'do': 'cf.get_org_by_name',
            'where': {
                'cf_api_url': self.cf_api_url,
                'org_name': self.org,
            }}
        self.populated_pre_step_health_check = {
            'step': 'HTTP pre health check',
            'do': 'cm.http_probe',
            'where': {
                'url': self.health_endpoint
            }}
        self.populated_post_step_health_check = {
            'step': 'HTTP health check',
            'do': 'cm.http_probe',
            'where': {
                'url': self.health_endpoint
            }}
        self._populated_steps = [self.populated_step_get_app_by_name,
                                 self.populated_step_get_org_by_name]
        self._populated_pre_steps = [self.populated_pre_step_health_check]
        self._populated_post_steps = [self.populated_post_step_health_check]

        signals.post_save.disconnect(execute_plan_for_trial, sender=Trial)
        self._trial = create_experiment_and_trial(self.parameters, self.steps)

    def tearDown(self):
        signals.post_save.connect(execute_plan_for_trial, sender=Trial)


class TestTrialLogRecorderSetup(TestTrialExecutor):

    def test_context_enter_sets_up_trial_log_recorder(self):
        log_rec_path = 'kallisticore.lib.trial_executor.TrialLogRecorder'
        with mock.patch(log_rec_path) as mock_log_recorder_cls:
            executor = TrialExecutor(self._trial, {}, {})
            executor.__enter__()
            mock_log_recorder_cls.assert_called_once_with(self._trial.id)


class TestTrialRunScenarioStepsSucceeded(TestTrialExecutor):
    def test_execute_all_commands(self):
        with mock.patch(self.CF_GET_APP) as app_action, \
             mock.patch(self.CF_GET_ORG) as org_action, \
             TrialExecutor(self._trial, self.module_map, {}) as trial_executor:
            trial_executor.run()

        app_action.assert_called_once_with(app_name="hello-world",
                                           configuration=ANY, secrets=ANY)
        org_action.assert_called_once_with(org_name="MY-ORG",
                                           configuration=ANY, secrets=ANY)

    def test_set_status_to_in_progress_at_run(self):
        executor = TrialExecutor(self._trial, self.module_map, {})
        with mock.patch(self.CF_GET_APP), mock.patch(self.CF_GET_ORG):
            executor.__enter__()
            executor.run()
        self.assertEqual(self._trial.status, TrialStatus.IN_PROGRESS.value)

    def test_set_status_to_successful(self):
        with mock.patch(self.CF_GET_APP), mock.patch(self.CF_GET_ORG), \
             TrialExecutor(self._trial, self.module_map, {}) as trial_executor:
            trial_executor.run()
        self.assertEqual(self._trial.status, TrialStatus.SUCCEEDED.value)

    def test_update_executed_at_to_date_time_object(self):
        with mock.patch(self.CF_GET_APP), mock.patch(self.CF_GET_ORG), \
             TrialExecutor(self._trial, self.module_map, {}) as trial_executor:
            trial_executor.run()
        self.assertIsInstance(self._trial.executed_at, timezone.datetime)

    def test_log_trial_with_parameter_interpolation(self):
        with mock.patch(self.LOG_REC) as mock_log_rec_cls, \
             mock.patch(self.STEP_REC) as mock_step_rec_cls, \
             mock.patch(self.COMMIT) as mock_rec_commit, \
             mock.patch(self.CF_GET_APP) as app_cmd_mock, \
             mock.patch(self.CF_GET_ORG) as org_cmd_mock, \
             TrialExecutor(self._trial, self.module_map, {}) as trial_executor:

            mock_trial_log = mock.Mock()
            mock_trial_log.append = mock.Mock()
            mock_log_rec_cls.return_value = mock_trial_log
            mock_trial_step_log = mock.Mock()
            mock_trial_step_log.append = mock.Mock()
            mock_step_rec_cls.return_value = mock_trial_step_log
            trial_executor.run()

        mock_step_rec_cls.assert_has_calls([
            call('steps', 'Get app by name',
                 self.populated_step_get_app_by_name['where']),
            call().append('INFO', 'Starting command execution.'),
            call().append('INFO',
                          "Result: {}.".format(app_cmd_mock.return_value)),
            call().append('INFO', 'Completed.'),
            call('steps', 'Get org by name',
                 self.populated_step_get_org_by_name['where']),
            call().append('INFO', 'Starting command execution.'),
            call().append('INFO',
                          "Result: {}.".format(org_cmd_mock.return_value)),
            call().append('INFO', 'Completed.'),
        ])
        mock_log_rec_cls.assert_has_calls([
            call('result'),
            call().append('INFO', 'Trial Completed.')
        ])
        mock_rec_commit.assert_has_calls([
            call(mock_trial_step_log),
            call(mock_trial_step_log),
            call(mock_trial_log)
        ])
        self.assertEqual(self._trial.status, TrialStatus.SUCCEEDED.value)

    def test_log_trial_without_param_interpolation(self):
        step_get_app_by_name = {'step': 'Get CF App by Name',
                                'do': 'cf.get_app_by_name',
                                'where': {
                                    'cf_api_url': self.cf_api_url,
                                    'app_name': self.app_name}}
        step_get_org_by_name = {'step': 'Get CF Org by Name',
                                'do': 'cf.get_org_by_name',
                                'where': {
                                    'cf_api_url': self.cf_api_url,
                                    'org_name': self.org}}
        steps = [step_get_app_by_name, step_get_org_by_name]

        trial = create_experiment_and_trial({}, steps)

        with mock.patch(self.LOG_REC) as mock_log_rec_cls, \
            mock.patch(self.STEP_REC) as mock_step_rec_cls, \
            mock.patch(self.COMMIT) as mock_rec_commit, \
            mock.patch(self.CF_GET_APP) as app_cmd_mock, \
            mock.patch(self.CF_GET_ORG) as org_cmd_mock,\
                TrialExecutor(trial, self.module_map, {}) as trial_executor:

            mock_trial_log = mock.Mock()
            mock_trial_log.append = mock.Mock()
            mock_log_rec_cls.return_value = mock_trial_log
            mock_trial_step_log = mock.Mock()
            mock_trial_step_log.append = mock.Mock()
            mock_step_rec_cls.return_value = mock_trial_step_log
            trial_executor.run()

        mock_step_rec_cls.assert_has_calls([
            call('steps', 'Get app by name', step_get_app_by_name['where']),
            call().append('INFO', 'Starting command execution.'),
            call().append('INFO',
                          "Result: {}.".format(app_cmd_mock.return_value)),
            call().append('INFO', 'Completed.'),
            call('steps', 'Get org by name', step_get_org_by_name['where']),
            call().append('INFO', 'Starting command execution.'),
            call().append('INFO',
                          "Result: {}.".format(org_cmd_mock.return_value)),
            call().append('INFO', 'Completed.'),
        ])
        mock_log_rec_cls.assert_has_calls([
            call('result'),
            call().append('INFO', 'Trial Completed.')
        ])
        mock_rec_commit.assert_has_calls([
            call(mock_trial_step_log),
            call(mock_trial_step_log),
            call(mock_trial_log)
        ])
        self.assertEqual(trial.status, TrialStatus.SUCCEEDED.value)

    def test_interpolation_from_trial_definition(self):
        parameters = {}
        trial = create_experiment_and_trial(
            parameters, self.steps, runtime_parameters=self.parameters)

        with mock.patch(self.LOG_REC) as mock_log_rec_cls, \
            mock.patch(self.STEP_REC) as mock_step_rec_cls, \
            mock.patch(self.COMMIT) as mock_rec_commit, \
            mock.patch(self.CF_GET_APP) as app_cmd_mock, \
            mock.patch(self.CF_GET_ORG) as org_cmd_mock, \
                TrialExecutor(trial, self.module_map, {}) as trial_executor:
            mock_trial_log = mock.Mock()
            mock_trial_log.append = mock.Mock()
            mock_log_rec_cls.return_value = mock_trial_log
            mock_trial_step_log = mock.Mock()
            mock_trial_step_log.append = mock.Mock()
            mock_step_rec_cls.return_value = mock_trial_step_log
            trial_executor.run()

        mock_step_rec_cls.assert_has_calls([
            call('steps', 'Get app by name',
                 self.populated_step_get_app_by_name['where']),
            call().append('INFO', 'Starting command execution.'),
            call().append('INFO',
                          "Result: {}.".format(app_cmd_mock.return_value)),
            call().append('INFO', 'Completed.'),
            call('steps', 'Get org by name',
                 self.populated_step_get_org_by_name['where']),
            call().append('INFO', 'Starting command execution.'),
            call().append('INFO',
                          "Result: {}.".format(org_cmd_mock.return_value)),
            call().append('INFO', 'Completed.')])
        mock_log_rec_cls.assert_has_calls([
            call('result'),
            call().append('INFO', 'Trial Completed.')])
        mock_rec_commit.assert_has_calls([
            call(mock_trial_step_log),
            call(mock_trial_step_log),
            call(mock_trial_log)])
        self.assertEqual(trial.status, TrialStatus.SUCCEEDED.value)

    def test_log_return_value_when_present(self):
        with mock.patch(self.LOG_REC) as mock_log_rec_cls, \
            mock.patch(self.STEP_REC) as mock_step_rec_cls, \
            mock.patch(self.COMMIT) as mock_rec_commit, \
            mock.patch(self.CF_GET_APP) as app_cmd_mock, \
            mock.patch(self.CF_GET_ORG) as org_cmd_mock, \
                TrialExecutor(self._trial, self.module_map, {}) \
                as trial_executor:

            mock_trial_log = mock.Mock()
            mock_trial_log.append = mock.Mock()
            mock_log_rec_cls.return_value = mock_trial_log
            mock_trial_step_log = mock.Mock()
            mock_trial_step_log.append = mock.Mock()
            mock_step_rec_cls.return_value = mock_trial_step_log
            app_cmd_mock.return_value = 'Hello World'
            org_cmd_mock.return_value = 'MY-ORG'
            trial_executor.run()

        mock_step_rec_cls.assert_has_calls([
            call('steps', 'Get app by name',
                 self.populated_step_get_app_by_name['where']),
            call().append('INFO', 'Starting command execution.'),
            call().append('INFO',
                          "Result: {}.".format(app_cmd_mock.return_value)),
            call().append('INFO', 'Completed.'),
            call('steps', 'Get org by name',
                 self.populated_step_get_org_by_name['where']),
            call().append('INFO', 'Starting command execution.'),
            call().append('INFO',
                          "Result: {}.".format(org_cmd_mock.return_value)),
            call().append('INFO', 'Completed.'),
        ])
        mock_log_rec_cls.assert_has_calls([
            call('result'),
            call().append('INFO', 'Trial Completed.')
        ])
        mock_rec_commit.assert_has_calls([
            call(mock_trial_step_log),
            call(mock_trial_step_log),
            call(mock_trial_log)
        ])
        self.assertEqual(self._trial.status, TrialStatus.SUCCEEDED.value)

    def test_should_update_parameters(self):
        with mock.patch(self.CF_GET_APP), mock.patch(self.CF_GET_ORG), \
             TrialExecutor(self._trial, self.module_map, {}) as trial_executor:
            trial_executor.run()
            self.assertEqual(self._trial.parameters, self.parameters)

    def test_log_success_if_expect_passes(self):
        step_description = 'Get CF App by Name'
        expect_spec = [{'operator': 'eq', 'app_name': self.app_name}]
        steps = [{'step': step_description,
                  'do': 'cf.get_app_by_name',
                  'where': {'app_name': self.app_name,
                            'cf_api_url': self.cf_api_url},
                  'expect': expect_spec}]
        trial = create_experiment_and_trial({}, steps)

        with mock.patch(self.LOG_REC) as mock_log_rec_cls, \
            mock.patch(self.STEP_REC) as mock_step_rec_cls, \
            mock.patch(self.COMMIT) as mock_rec_commit, \
            mock.patch(self.CF_GET_APP) as app_cmd_mock, \
                TrialExecutor(trial, self.module_map, {}) as trial_executor:
            mock_trial_log = mock.Mock()
            mock_trial_log.append = mock.Mock()
            mock_log_rec_cls.return_value = mock_trial_log
            mock_trial_step_log = mock.Mock()
            mock_trial_step_log.append = mock.Mock()
            mock_step_rec_cls.return_value = mock_trial_step_log
            app_cmd_mock.return_value = {'app_name': self.app_name}
            trial_executor.run()

        mock_step_rec_cls.assert_has_calls([
            call('steps', 'Get app by name',
                 {'app_name': self.app_name, 'cf_api_url': self.cf_api_url}),
            call().append('INFO', 'Starting command execution.'),
            call().append('INFO',
                          "Result: {}.".format(app_cmd_mock.return_value)),
            call().append('INFO',
                          "Succeeded. All expectations passed: {}.".format(
                              expect_spec)),
            call().append('INFO', 'Completed.'),
        ])
        mock_log_rec_cls.assert_has_calls([
            call('result'),
            call().append('INFO', 'Trial Completed.')
        ])
        mock_rec_commit.assert_has_calls([
            call(mock_trial_step_log),
            call(mock_trial_log)
        ])
        self.assertEqual(trial.status, TrialStatus.SUCCEEDED.value)


class TestTrialRunScenarioStepsFailed(TestTrialExecutor):
    def test_missing_param_in_steps(self):
        parameters = {}
        runtime_parameters = {'cf_api_url': self.cf_api_url,
                              'app_name': self.app_name}
        trial = create_experiment_and_trial(
            parameters, self.steps, runtime_parameters=runtime_parameters)

        with mock.patch(self.LOG_REC) as mock_log_rec_cls, \
            mock.patch(self.COMMIT) as mock_rec_commit, \
                TrialExecutor(trial, self.module_map, {}) as trial_executor:
            mock_trial_log = mock.Mock()
            mock_trial_log.append = mock.Mock()
            mock_log_rec_cls.return_value = mock_trial_log
            trial_executor.run()

        mock_log_rec_cls.assert_has_calls([
            call('result'),
            call().append('ERROR',
                          "Trial Invalid. Type: MissingParameterValueError. "
                          "Error: Trial is invalid because of missing value "
                          "in experiment parameters: 'cf_org'.")])
        mock_rec_commit.assert_has_calls([call(mock_trial_log)])
        self.assertEqual(trial.status, TrialStatus.INVALID.value)

    def test_missing_param_in_post_steps(self):
        parameters = {
            'cf_api_url': self.cf_api_url,
            'app_name': self.app_name}
        trial = create_experiment_and_trial(
            parameters, self.steps, post_steps=self.post_steps,
            runtime_parameters=self.parameters)

        with mock.patch(self.LOG_REC) as mock_log_rec_cls, \
            mock.patch(self.COMMIT) as mock_rec_commit, \
                TrialExecutor(trial, self.module_map, {}) as trial_executor:
            mock_trial_log = mock.Mock()
            mock_trial_log.append = mock.Mock()
            mock_log_rec_cls.return_value = mock_trial_log
            trial_executor.run()

        mock_log_rec_cls.assert_has_calls([
            call('result'),
            call().append('ERROR',
                          "Trial Invalid. Type: MissingParameterValueError. "
                          "Error: Trial is invalid because of missing value "
                          "in experiment parameters: 'health_endpoint'.")])
        mock_rec_commit.assert_has_calls([
            call(mock_trial_log)])
        self.assertEqual(trial.status, TrialStatus.INVALID.value)

    def test_abort_with_execution_failure(self):
        with mock.patch(self.CF_EXEC) as action_mock, \
                TrialExecutor(self._trial, self.module_map, {}) \
                as trial_executor:
            action_mock.side_effect = Exception("api function error.")
            trial_executor.run()
        action_mock.assert_called_once_with()
        self.assertEqual(self._trial.status, TrialStatus.FAILED.value)

    def test_update_executed_at(self):
        with mock.patch(self.CF_EXEC) as action_mock, \
                TrialExecutor(self._trial, self.module_map, {})\
                as trial_executor:
            action_mock.side_effect = Exception("api function error.")
            trial_executor.run()
        self.assertIsInstance(self._trial.executed_at, timezone.datetime)

    def test_log_steps_with_param_interpolation(self):
        error_msg = "api function error."

        with mock.patch(self.LOG_REC) as mock_log_rec_cls, \
            mock.patch(self.STEP_REC) as mock_step_rec_cls, \
            mock.patch(self.COMMIT) as mock_rec_commit, \
            mock.patch(self.CF_EXEC) as action_mock, \
                TrialExecutor(self._trial, self.module_map, {})\
                as trial_executor:
            mock_trial_log = mock.Mock()
            mock_trial_log.append = mock.Mock()
            mock_log_rec_cls.return_value = mock_trial_log
            mock_trial_step_log = mock.Mock()
            mock_trial_step_log.append = mock.Mock()
            mock_step_rec_cls.return_value = mock_trial_step_log
            action_mock.side_effect = Exception(error_msg)
            trial_executor.run()

        mock_step_rec_cls.assert_has_calls([
            call('steps', 'Get app by name',
                 {'app_name': self.app_name, 'cf_api_url': self.cf_api_url}),
            call().append('INFO', 'Starting command execution.'),
            call().append('ERROR',
                          "Step failed. Type: Exception. "
                          "Error: api function error.")])
        mock_log_rec_cls.assert_has_calls([
            call('result'),
            call().append('ERROR',
                          'Trial Failed. Type: StepsExecutionError. '
                          'Error: [in: steps, reason: api function error.]')])
        mock_rec_commit.assert_has_calls([
            call(mock_trial_step_log),
            call(mock_trial_log)])
        self.assertEqual(self._trial.status, TrialStatus.FAILED.value)

    def test_log_steps_without_param_interpolation_on_exec_fail(self):
        steps = [{'step': 'Get CF App by Name',
                  'do': 'cf.get_app_by_name',
                  'where': {
                      'cf_api_url': self.cf_api_url,
                      'app_name': self.app_name}},
                 {'step': 'Get CF Org by Name',
                  'do': 'cf.get_org_by_name',
                  'where': {
                      'cf_api_url': self.cf_api_url,
                      'org_name': self.org}}]

        trial = create_experiment_and_trial({}, steps)
        error_msg = "api function error."

        with mock.patch(self.LOG_REC) as mock_log_rec_cls, \
            mock.patch(self.STEP_REC) as mock_step_rec_cls, \
            mock.patch(self.COMMIT) as mock_rec_commit, \
            mock.patch(self.CF_EXEC) as action_mock, \
                TrialExecutor(trial, self.module_map, {}) as trial_executor:
            mock_trial_log = mock.Mock()
            mock_trial_log.append = mock.Mock()
            mock_log_rec_cls.return_value = mock_trial_log
            mock_trial_step_log = mock.Mock()
            mock_trial_step_log.append = mock.Mock()
            mock_step_rec_cls.return_value = mock_trial_step_log
            action_mock.side_effect = Exception(error_msg)
            trial_executor.run()

        mock_step_rec_cls.assert_has_calls([
            call('steps', 'Get app by name',
                 {'app_name': self.app_name, 'cf_api_url': self.cf_api_url}),
            call().append('INFO', 'Starting command execution.'),
            call().append('ERROR',
                          "Step failed. Type: Exception. "
                          "Error: api function error.")])
        mock_log_rec_cls.assert_has_calls([
            call('result'),
            call().append('ERROR',
                          'Trial Failed. Type: StepsExecutionError. '
                          'Error: [in: steps, reason: api function error.]')])
        mock_rec_commit.assert_has_calls([
            call(mock_trial_step_log),
            call(mock_trial_log)])
        self.assertEqual(trial.status, TrialStatus.FAILED.value)

    def test_log_with_invalid_param(self):
        steps = [{'step': 'Get CF App by Name',
                  'do': 'cf.get_app_by_name',
                  'where': {
                      'app_name': '{{ app_name}',
                      'env': '{{my_environment }}',
                      'pool': '{{ my_pool }}'}}]

        trial = create_experiment_and_trial(
            self.parameters, steps)

        with mock.patch(self.LOG_REC) as mock_log_rec_cls, \
            mock.patch(self.COMMIT) as mock_rec_commit, \
                TrialExecutor(trial, self.module_map, {}) as trial_executor:
            mock_trial_log = mock.Mock()
            mock_trial_log.append = mock.Mock()
            mock_log_rec_cls.return_value = mock_trial_log
            trial_executor.run()

        mock_log_rec_cls.assert_has_calls([
            call('result'),
            call().append('ERROR',
                          'Trial Failed. Type: TemplateSyntaxError. '
                          'Error: unexpected \'}\'')])
        mock_rec_commit.assert_has_calls([
            call(mock_trial_log)])
        self.assertEqual(trial.status, TrialStatus.FAILED.value)

    def test_log_error_message_if_expect_fails(self):
        steps = [{'step': 'Get CF App by Name',
                  'do': 'cf.get_app_by_name',
                  'where': {
                      'cf_api_url': self.cf_api_url,
                      'app_name': self.app_name},
                  'expect': [
                      {'operator': 'eq', 'app_name': 'unexpected-app-name'}]}]
        trial = create_experiment_and_trial({}, steps)

        with mock.patch(self.LOG_REC) as mock_log_rec_cls, \
            mock.patch(self.STEP_REC) as mock_step_rec_cls, \
            mock.patch(self.COMMIT) as mock_rec_commit, \
            mock.patch(self.CF_GET_APP) as app_mock, \
                TrialExecutor(trial, self.module_map, {}) as trial_executor:
            mock_trial_log = mock.Mock()
            mock_trial_log.append = mock.Mock()
            mock_log_rec_cls.return_value = mock_trial_log
            mock_trial_step_log = mock.Mock()
            mock_trial_step_log.append = mock.Mock()
            mock_step_rec_cls.return_value = mock_trial_step_log
            app_mock.return_value = {"app_name": "Hello World"}
            trial_executor.run()

        mock_step_rec_cls.assert_has_calls([
            call('steps', 'Get app by name',
                 {'app_name': self.app_name, 'cf_api_url': self.cf_api_url}),
            call().append('INFO', 'Starting command execution.'),
            call().append('ERROR',
                          "Step failed. Type: FailedExpectation. "
                          "Error: Expectation failed"
                          "(Hello World == unexpected-app-name)")])
        mock_log_rec_cls.assert_has_calls([
            call('result'),
            call().append('ERROR',
                          'Trial Failed. Type: StepsExecutionError. '
                          'Error: [in: steps, reason: Expectation failed'
                          '(Hello World == unexpected-app-name)]')])
        mock_rec_commit.assert_has_calls([
            call(mock_trial_step_log),
            call(mock_trial_log)])
        self.assertEqual(trial.status, TrialStatus.FAILED.value)


class TestTrialRunScenarioPostStepsSucceeded(TestTrialExecutor):
    def setUp(self):
        super(TestTrialRunScenarioPostStepsSucceeded, self).setUp()
        self.steps = [{'step': 'Stop App',
                       'do': 'cf.stop_app',
                       'where': {
                           'cf_api_url': self.cf_api_url,
                           'app_name': self.app_name}}]
        self.post_steps = [{'step': 'Start App',
                            'do': 'cf.start_app',
                            'where': {
                                'cf_api_url': self.cf_api_url,
                                'app_name': self.app_name}}]
        self.trial = create_experiment_and_trial(
            {}, self.steps, post_steps=self.post_steps)

    def test_post_steps_succeed(self):
        with mock.patch(self.LOG_REC) as mock_log_rec_cls, \
            mock.patch(self.STEP_REC) as mock_step_rec_cls, \
            mock.patch(self.COMMIT) as mock_rec_commit, \
            mock.patch(self.CF_STOP_APP) as stop_app_action, \
            mock.patch(self.CF_START_APP) as start_app_action, \
                TrialExecutor(self.trial, self.module_map, {})\
                as trial_executor:
            mock_trial_log = mock.Mock()
            mock_trial_log.append = mock.Mock()
            mock_log_rec_cls.return_value = mock_trial_log
            mock_log_record = mock.Mock()
            mock_log_record.append = mock.Mock()
            mock_step_rec_cls.return_value = mock_log_record
            start_app_action.return_value = 'start_app'
            stop_app_action.return_value = 'stop_app'
            trial_executor.run()

        mock_step_rec_cls.assert_has_calls([
            call('steps', 'Stop app',
                 {'cf_api_url': self.cf_api_url, 'app_name': self.app_name}),
            call().append('INFO', 'Starting command execution.'),
            call().append('INFO',
                          'Result: {}.'.format(stop_app_action.return_value)),
            call().append('INFO', 'Completed.'),
            call('post_steps', 'Start app',
                 {'cf_api_url': self.cf_api_url, 'app_name': 'hello-world'}),
            call().append('INFO', 'Starting command execution.'),
            call().append('INFO',
                          'Result: {}.'.format(start_app_action.return_value)),
            call().append('INFO', 'Completed.')])
        mock_log_rec_cls.assert_has_calls([
            call('result'),
            call().append('INFO', 'Trial Completed.')])
        mock_rec_commit.assert_has_calls([call(mock_trial_log)])
        self.assertEqual(self.trial.status, TrialStatus.SUCCEEDED.value)


class TestTrialRunScenarioPostStepsFailed(TestTrialExecutor):
    def setUp(self):
        super(TestTrialRunScenarioPostStepsFailed, self).setUp()
        self.steps = [{'step': 'Stop App',
                       'do': 'cf.stop_app',
                       'where': {
                           'cf_api_url': self.cf_api_url,
                           'app_name': self.app_name}}]
        self.post_steps = [{'step': 'Start App',
                            'do': 'cf.start_app',
                            'where': {
                                'cf_api_url': self.cf_api_url,
                                'app_name': self.app_name}}]
        self.trial = create_experiment_and_trial(
            {}, self.steps, post_steps=self.post_steps)

    def test_post_steps_fail(self):
        with mock.patch(self.LOG_REC) as mock_log_rec_cls, \
            mock.patch(self.COMMIT) as mock_rec_commit, \
            mock.patch(self.CF_STOP_APP), \
            mock.patch(self.CF_START_APP) as start_app_action, \
                TrialExecutor(self.trial, self.module_map, {}) \
                as trial_executor:
            start_app_action.side_effect = Exception("Api error message")
            mock_trial_log = mock.Mock()
            mock_trial_log.append = mock.Mock()
            mock_log_rec_cls.return_value = mock_trial_log
            trial_executor.run()

        mock_log_rec_cls.assert_called_with('result')
        mock_trial_log.append.assert_called_with(
            'ERROR', 'Trial Failed. Type: StepsExecutionError. '
                     'Error: [in: post_steps, reason: Api error message]')
        mock_rec_commit.assert_has_calls([call(mock_trial_log)])
        self.assertEqual(self.trial.status, TrialStatus.FAILED.value)


class TestTrialRunScenarioPreStepsSucceeded(TestTrialExecutor):
    def setUp(self):
        super(TestTrialRunScenarioPreStepsSucceeded, self).setUp()
        self.pre_steps = [{'step': 'Stop App',
                           'do': 'cf.stop_app',
                           'where': {
                               'cf_api_url': self.cf_api_url,
                               'app_name': self.app_name}}]
        self.steps = [{'step': 'Start App',
                       'do': 'cf.start_app',
                       'where': {
                           'cf_api_url': self.cf_api_url,
                           'app_name': self.app_name}}]
        self.trial = create_experiment_and_trial(
            {}, self.steps, pre_steps=self.pre_steps)

    def test_pre_steps_and_steps_succeed(self):
        with mock.patch(self.LOG_REC) as mock_log_rec_cls, \
            mock.patch(self.STEP_REC) as mock_step_rec_cls, \
            mock.patch(self.COMMIT) as mock_rec_commit, \
            mock.patch(self.CF_STOP_APP) as stop_app_action, \
            mock.patch(self.CF_START_APP) as start_app_action, \
                TrialExecutor(self.trial, self.module_map, {}) \
                as trial_executor:
            mock_trial_log = mock.Mock()
            mock_trial_log.append = mock.Mock()
            mock_log_rec_cls.return_value = mock_trial_log
            mock_log_record = mock.Mock()
            mock_log_record.append = mock.Mock()
            mock_step_rec_cls.return_value = mock_log_record
            start_app_action.return_value = 'start_app'
            stop_app_action.return_value = 'stop_app'
            trial_executor.run()

        mock_step_rec_cls.assert_has_calls([
            call('pre_steps', 'Stop app',
                 {'cf_api_url': self.cf_api_url, 'app_name': self.app_name}),
            call().append('INFO', 'Starting command execution.'),
            call().append('INFO',
                          'Result: {}.'.format(stop_app_action.return_value)),
            call().append('INFO', 'Completed.'),
            call('steps', 'Start app',
                 {'cf_api_url': self.cf_api_url, 'app_name': self.app_name}),
            call().append('INFO', 'Starting command execution.'),
            call().append('INFO',
                          'Result: {}.'.format(start_app_action.return_value)),
            call().append('INFO', 'Completed.')])
        mock_log_rec_cls.assert_has_calls([
            call('result'),
            call().append('INFO', 'Trial Completed.')])
        mock_rec_commit.assert_has_calls([
            call(mock_trial_log)])
        self.assertEqual(self.trial.status, TrialStatus.SUCCEEDED.value)


class TestTrialRunScenarioPreStepsFailed(TestTrialExecutor):
    def setUp(self):
        super(TestTrialRunScenarioPreStepsFailed, self).setUp()
        self.pre_steps = [{'step': 'Stop App',
                           'do': 'cf.stop_app',
                           'where': {
                               'cf_api_url': self.cf_api_url,
                               'app_name': self.app_name}}]
        self.steps = [{'step': 'Start App',
                       'do': 'cf.start_app',
                       'where': {
                           'cf_api_url': self.cf_api_url,
                           'app_name': self.app_name}}]
        self.trial = create_experiment_and_trial(
            {}, self.steps, pre_steps=self.pre_steps)

    def test_pre_steps_fail(self):
        with mock.patch(self.LOG_REC) as mock_log_rec_cls, \
            mock.patch(self.COMMIT) as mock_rec_commit, \
            mock.patch(self.CF_STOP_APP) as stop_app_action, \
            mock.patch(self.CF_START_APP), \
                TrialExecutor(self.trial, self.module_map, {}) \
                as trial_executor:
            stop_app_action.side_effect = Exception("Api error message")
            mock_trial_log = mock.Mock()
            mock_trial_log.append = mock.Mock()
            mock_log_rec_cls.return_value = mock_trial_log
            trial_executor.run()

        mock_log_rec_cls.assert_called_with('result')
        mock_trial_log.append.assert_called_with(
            'ERROR',
            "Trial Aborted. Type: StepsExecutionError. "
            "Error: [in: pre_steps, reason: Api error message]")
        mock_rec_commit.assert_has_calls([call(mock_trial_log)])
        self.assertEqual(self.trial.status, TrialStatus.ABORTED.value)


class TestTrialRunOnExit(TestTrialExecutor):
    def setUp(self):
        super(TestTrialRunOnExit, self).setUp()
        self.observer_mock = mock.Mock(spec=Observer)

    def test_notify_attached_observers_on_trial_success(self):
        with mock.patch(self.CF_GET_APP), mock.patch(self.CF_GET_ORG), \
             TrialExecutor(self._trial, self.module_map, {}) as trial_executor:
            trial_executor.attach(self.observer_mock)
            trial_executor.run()
        self.observer_mock.update.assert_called_once_with(trial=self._trial)

    def test_notify_attached_observers_on_trial_fail(self):
        with mock.patch(self.CF_GET_APP) as get_app_action, \
                mock.patch(self.CF_GET_ORG), \
                TrialExecutor(self._trial, self.module_map, {}) \
                as trial_executor:
            get_app_action.side_effect = Exception("Api error message")
            trial_executor.attach(self.observer_mock)
            trial_executor.run()
        self.observer_mock.update.assert_called_once_with(trial=self._trial)


class TestExecuteTrial(TestCase):

    @mock.patch("kallisticore.lib.trial_executor.TrialExecutor", autospec=True)
    def test_trial_executor_invoked(self, mock_trial_executor):
        mock_object = self.create_mock_trial_executor(mock_trial_executor)
        trial = {}

        execute_trial(trial)

        self.assert_executor_called(mock_object, mock_trial_executor, trial)

    def assert_executor_called(self, mock_object, mock_trial_executor, trial):
        module_map = getattr(settings, 'KALLISTI_MODULE_MAP', {})
        cred_cls_map = getattr(settings, 'KALLISTI_CREDENTIAL_CLASS_MAP', {})
        mock_trial_executor.assert_called_once_with(trial, module_map,
                                                    cred_cls_map)

        mock_object.__enter__.assert_called_once()
        mock_object.__enter__.assert_called_once()
        mock_object.run.assert_called_once()
        mock_object.__exit__.assert_called_once()

    def create_mock_trial_executor(self, mock_trial_executor):
        mock_object = Mock()
        mock_object.__enter__ = Mock(return_value=mock_object)
        mock_object.__exit__ = Mock()
        mock_trial_executor.return_value = mock_object
        return mock_object
