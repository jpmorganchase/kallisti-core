import logging
import sys
import traceback
from inspect import Traceback
from typing import Optional, Type, List
from django.conf import settings

from kallisticore.exceptions import MissingParameterValueError, \
    StepsExecutionError
from kallisticore.lib.action import make_action
from kallisticore.lib.observe.subject import Subject
from kallisticore.lib.trial_log_recorder import TrialLogRecord, \
    TrialStepLogRecord, TrialLogRecorder
from kallisticore.models import Trial
from kallisticore.models.step import Step
from kallisticore.models.trial import TrialStatus, TrialStepsType


class TrialExecutor(Subject):
    logger = logging.getLogger(__name__)
    trial_log_recorder = None

    def __init__(self, trial: Trial, action_module_map: dict,
                 credential_class_map: dict):
        super(TrialExecutor, self).__init__()
        self.trial = trial
        self.action_module_map = action_module_map
        self.credential_class_map = credential_class_map

    def __enter__(self):
        self._setup_trial_log_recorder()
        return self

    def __exit__(self, exc_type: Optional[Type[BaseException]],
                 exc_val: Optional[BaseException],
                 exc_tb: Optional[Traceback]) -> bool:
        if exc_val:
            if exc_type.__name__ == "MissingParameterValueError":
                status = TrialStatus.INVALID
            elif exc_type == StepsExecutionError and \
                    exc_val.is_pre_steps_exception():
                status = TrialStatus.ABORTED
            else:
                status = TrialStatus.FAILED
            self.trial.update_status(status)
            self._log_unsuccessful_trial(
                exc_type, exc_val, exc_tb, status.value)
        else:
            self.trial.update_status(TrialStatus.SUCCEEDED)
            self._log_successful_trial()
        self.notify(trial=self.trial)
        return True

    def run(self):
        self.trial.update_executed_at()
        self.trial.update_status(TrialStatus.IN_PROGRESS)
        self._raise_error_if_missing_parameters(
            self.trial.get_undefined_variables())
        self._log_trial_start_message()
        post_steps, pre_steps, steps = self._extract_trial_steps()
        self._execute_steps(pre_steps, TrialStepsType.PRE)
        try:
            self._execute_steps(steps, TrialStepsType.STEPS)
        finally:
            self._execute_steps(post_steps, TrialStepsType.POST)

    def _extract_trial_steps(self):
        try:
            pre_steps = self.trial.get_pre_steps()
            steps = self.trial.get_steps()
            post_steps = self.trial.get_post_steps()
        except Exception:
            exc_name, exc_message, exc_tb = self._handle_exception(
                *sys.exc_info())
            error_msg = "Error extracting experiment steps!"
            self._app_log_err("Trial Failed - {}.".format(error_msg), exc_name,
                              exc_message, exc_tb)
            raise Exception(error_msg)
        return post_steps, pre_steps, steps

    def _execute_steps(self, steps: List[Step], step_type: TrialStepsType):
        for step in steps:
            step_name = step.get_function_name().replace('_', ' ').capitalize()
            trial_steps_log = TrialStepLogRecord(step_type.value, step_name,
                                                 step.where)
            try:
                self._execute_action(step, trial_steps_log)
            except Exception as exception:
                raise StepsExecutionError(step_type) from exception

    def _execute_action(self, step: Step,
                        trial_step_log: TrialStepLogRecord) -> None:
        action = make_action(step, self.action_module_map,
                             self.credential_class_map)
        try:
            trial_step_log.append("INFO", "Starting command execution.")
            return_value = action.execute()
            if return_value is not None:
                trial_step_log.append("INFO",
                                      "Result: {}.".format(return_value))
                if action.expectations:
                    trial_step_log.append("INFO",
                                          "Succeeded. All expectations "
                                          "passed: {}.".format(step.expect))
            trial_step_log.append("INFO", "Completed.")
            self.trial_log_recorder.commit(trial_step_log)
        except Exception as exception:
            self._log_step_exception(action, trial_step_log)
            raise exception

    def _raise_error_if_missing_parameters(self, undefined_variables):
        if len(undefined_variables) > 0:
            log_msg = "Trial is invalid because of missing value in" \
                      " experiment parameters: {}." \
                .format(', '.join('\'{0}\''
                                  .format(w) for w in undefined_variables))
            self._app_log(logging.INFO, log_msg)
            raise MissingParameterValueError(log_msg)

    ##############################################
    # logging related methods
    ##############################################

    def _setup_trial_log_recorder(self):
        self.trial_log_recorder = TrialLogRecorder(self.trial.id)

    def _log_trial_start_message(self):
        parameters = self.trial.get_populated_parameters() or None
        self._app_log(logging.INFO,
                      "Starting with Parameters: {}.".format(parameters))

    def _log_step_exception(self, action, trial_step_log):
        exc_name, exc_message, exc_tb = self._handle_exception(*sys.exc_info())
        trial_step_log.append("ERROR",
                              "Step failed. Type: {}. Error: {}".format(
                                  exc_name, exc_message))
        self.trial_log_recorder.commit(trial_step_log)
        self._app_log_err("Action {} Failed.".format(action.name), exc_name,
                          exc_message, exc_tb)

    def _log_successful_trial(self):
        self._log_trial_results("INFO", "Trial Completed.")
        self._app_log(logging.INFO, "Completed.")

    def _log_unsuccessful_trial(self, exc_type: Type[BaseException],
                                exc_val: BaseException, exc_tb: Traceback,
                                status: str):
        exc_name, exc_message, exc_tb = self._handle_exception(exc_type,
                                                               exc_val, exc_tb)

        self._log_trial_results("ERROR",
                                "Trial {}. Type: {}. Error: {}"
                                .format(status, exc_name, exc_message))
        self._app_log_err("Trial {}".format(status), exc_name, exc_message,
                          exc_tb)

    def _log_trial_results(self, level, message):
        trial_log = TrialLogRecord('result')
        trial_log.append(level, message)
        self.trial_log_recorder.commit(trial_log)

    def _app_log_err(self, message: str, exc_name: str, exc_message: str,
                     traceback: str):
        self._app_log(
            level=logging.ERROR,
            message="{}. Type: {}. Error: {}, Stack trace: {}".format(
                message, exc_name, exc_message, traceback))

    def _app_log(self, level: int, message):
        self.logger.log(level=level,
                        msg="[Trial ID: {}] {}".format(self.trial.id, message))

    @staticmethod
    def _handle_exception(exc_type, exc_val, exc_tb):
        stack_trace = ''.join(traceback.format_tb(exc_tb))
        exc_name = exc_type.__name__
        exc_val_str = str(exc_val)
        return exc_name, exc_val_str, stack_trace


def execute_trial(instance):
    action_module_map = getattr(settings, 'KALLISTI_MODULE_MAP', {})
    cred_class_map = getattr(settings, 'KALLISTI_CREDENTIAL_CLASS_MAP', {})
    with TrialExecutor(
            instance, action_module_map, cred_class_map) as executor:
        for observer in getattr(settings, 'KALLISTI_TRIAL_OBSERVERS', []):
            executor.attach(observer())
        executor.run()
