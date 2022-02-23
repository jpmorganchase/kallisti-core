from collections import OrderedDict
from typing import List, Dict

from kallisticore.authentication import KallistiUser
from kallisticore.models import Trial
from kallisticore.models.experiment import Experiment
from kallisticore.models.notification import Notification
from kallisticore.models.step import Step
from kallisticore.models.trial_schedule import TrialSchedule, \
    validate_recurrence_pattern
from rest_framework import serializers


class ListOfDictsField(serializers.ListField):
    child = serializers.DictField()


def validate_step(value: List[Dict]):
    """
    :param value: List of step dict
    :return: None

    :raise ValidationError when invalid step structure is passed
    """
    Step.convert_to_steps(value)


def _get_kallisti_current_user_id(validated_data, key):
    user = validated_data.pop(key, None)
    if user is not None and isinstance(user, KallistiUser):
        return user.user_id
    return None


class ExperimentSerializer(serializers.ModelSerializer):
    description = serializers.CharField(required=False, allow_blank=True)
    parameters = serializers.DictField(required=False)
    metadata = serializers.DictField(required=False)
    pre_steps = ListOfDictsField(required=False, validators=[validate_step])
    steps = ListOfDictsField(validators=[validate_step])
    post_steps = ListOfDictsField(required=False, validators=[validate_step])
    creator = serializers.HiddenField(default=serializers.CurrentUserDefault())
    created_by = serializers.CharField(read_only=True)

    class Meta:
        model = Experiment
        fields = ('id', 'name', 'description', 'metadata', 'parameters',
                  'pre_steps', 'steps', 'post_steps', 'created_by', 'creator')

    def create(self, validated_data):
        validated_data['created_by'] = _get_kallisti_current_user_id(
            validated_data, 'creator')
        return super(ExperimentSerializer, self).create(validated_data)


class TrialSerializer(serializers.ModelSerializer):
    trial_record = serializers.SerializerMethodField()
    parameters = serializers.DictField(default={})
    metadata = serializers.DictField(default={}, required=False)
    ticket = serializers.DictField(default={})
    status = serializers.CharField(read_only=True)
    executed_at = serializers.DateTimeField(read_only=True)
    completed_at = serializers.DateTimeField(read_only=True)
    initiator = serializers.HiddenField(
        default=serializers.CurrentUserDefault())
    initiated_by = serializers.CharField(read_only=True)

    def get_trial_record(self, instance: Trial) -> OrderedDict:
        records = OrderedDict()
        pre_steps = instance.records.get('pre_steps', None)
        if pre_steps:
            records['pre_steps'] = pre_steps
        steps = instance.records.get('steps', None)
        if steps:
            records['steps'] = steps
        post_steps = instance.records.get('post_steps', None)
        if post_steps:
            records['post_steps'] = post_steps
        result = instance.records.get('result', None)
        if result:
            records['result'] = result
        return records

    def create(self, validated_data):
        validated_data['initiated_by'] = _get_kallisti_current_user_id(
            validated_data, 'initiator')
        return super(TrialSerializer, self).create(validated_data)

    class Meta:
        model = Trial
        fields = ('id', 'experiment', 'metadata', 'parameters', 'ticket',
                  'trial_record', 'status', 'executed_at', 'completed_at',
                  'initiated_by', 'initiator')


class TrialForReportSerializer(TrialSerializer):
    trial_record = serializers.SerializerMethodField()

    def get_trial_record(self, instance: Trial) -> dict:
        if not instance or not instance.records:
            return {}
        else:
            return instance.records

    class Meta:
        model = Trial
        exclude = ('experiment',)


class ReportSerializer(serializers.ModelSerializer):
    description = serializers.CharField(required=False)
    parameters = serializers.DictField(required=False)
    metadata = serializers.DictField(default={}, required=False)
    pre_steps = ListOfDictsField(validators=[validate_step])
    steps = ListOfDictsField(validators=[validate_step])
    post_steps = ListOfDictsField(required=False, validators=[validate_step])
    trials = serializers.SerializerMethodField()

    def get_trials(self, experiment):
        if self.context.get('trial_id'):
            trial = experiment.trials.get(id=self.context.get('trial_id'))
            return TrialForReportSerializer(many=True, instance=[trial]).data
        return TrialForReportSerializer(many=True,
                                        instance=experiment.trials).data

    class Meta:
        model = Experiment
        fields = ('id', 'name', 'description', 'metadata', 'parameters',
                  'pre_steps', 'steps', 'post_steps', 'trials')


class TrialStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trial
        fields = ('id', 'status', 'executed_at')


class TrialScheduleSerializer(serializers.ModelSerializer):
    parameters = serializers.DictField(default={})
    metadata = serializers.DictField(default={}, required=False)
    ticket = serializers.DictField(default={})
    recurrence_count = serializers.IntegerField(default=None, allow_null=True)
    recurrence_left = serializers.IntegerField(read_only=True)
    recurrence_pattern = serializers.CharField(required=True, validators=[
        validate_recurrence_pattern])
    creator = serializers.HiddenField(default=serializers.CurrentUserDefault())
    created_by = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    trials = serializers.SerializerMethodField()

    def create(self, validated_data):
        validated_data['created_by'] = _get_kallisti_current_user_id(
            validated_data, 'creator')
        assert Experiment.objects.get(
            id=self.context.get('experiment_id')).deleted_at is None
        validated_data['experiment_id'] = self.context.get('experiment_id')

        return super(TrialScheduleSerializer, self).create(validated_data)

    def get_trials(self, trial_schedule: TrialSchedule):
        sorted_trials = trial_schedule.trials.order_by('executed_at')
        return TrialStatusSerializer(sorted_trials, read_only=True,
                                     many=True).data

    class Meta:
        model = TrialSchedule
        fields = ('id', 'experiment_id', 'parameters', 'metadata', 'ticket',
                  'recurrence_pattern', 'recurrence_count', 'recurrence_left',
                  'creator', 'created_by', 'created_at', 'trials')


class NotificationSerializer(serializers.ModelSerializer):
    emails = serializers.ListField(required=True)

    class Meta:
        model = Notification
        fields = ('emails',)
