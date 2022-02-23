import json
from collections import OrderedDict
from logging import Formatter, makeLogRecord, getLogger

from kallisticore.models.trial import Trial
from kallisticore.utils.sanitizer import Sanitizer

LOGGING_FORMATTER = Formatter('[%(asctime)s - %(levelname)3s] %(message)s',
                              '%Y-%m-%dT%H:%M:%SZ')


class TrialLogRecord:
    def __init__(self, trial_stage: str):
        self.logs = []
        self.trial_stage = trial_stage

    def append(self, level: str, msg: str):
        log_record = makeLogRecord({
            "levelname": level,
            "msg": msg,
        })
        self.logs.append(LOGGING_FORMATTER.format(log_record))

    def make(self) -> OrderedDict:
        data = OrderedDict()
        data['logs'] = self.logs
        return data


class TrialStepLogRecord(TrialLogRecord):
    def __init__(self, trial_stage: str, step_name: str,
                 step_parameters: dict):
        self.step_name = step_name
        self.step_parameters = Sanitizer.clean_sensitive_data(step_parameters)
        super(TrialStepLogRecord, self).__init__(trial_stage)

    def make(self) -> OrderedDict:
        data = OrderedDict()
        data['step_name'] = self.step_name
        data['step_parameters'] = self.step_parameters
        data.update(super(TrialStepLogRecord, self).make())
        return data


class TrialLogRecorder:
    logger = getLogger(__name__)

    def __init__(self, trial_id: str):
        self.trial_id = trial_id
        self.trial_record = {}

    def commit(self, trial_log_record: TrialLogRecord):
        self.trial_record.setdefault(trial_log_record.trial_stage, [])\
            .append(trial_log_record.make())

        try:
            Trial.objects.filter(pk=self.trial_id).update(
                records=json.dumps(self.trial_record))
        except Exception as e:
            self.logger.warning(
                "Failed to update 'records' column for trial {}, {}"
                .format(self.trial_id, e))
