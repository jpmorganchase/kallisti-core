from typing import Dict, Callable

from kallisticore.lib.action import Action
from kallisticore.lib.credential import Credential
from kallisticore.lib.expectation import Expectation


class PrometheusAction(Action):
    def __init__(self, module_func: Callable, arguments: Dict,
                 expectations: [Expectation] = None,
                 name: str = None, credential: Credential = None):
        super(PrometheusAction, self).__init__(
            module_func=module_func, arguments=arguments,
            expectations=expectations, name=name, credential=credential)

        self.arguments['configuration'] = {
            'prometheus_base_url': arguments.pop('base_url')}


__action_class__ = PrometheusAction

__actions_modules__ = ['chaosprometheus.probes']
