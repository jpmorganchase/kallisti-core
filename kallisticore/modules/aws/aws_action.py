import importlib
from typing import Dict

from chaosaws import discover
from kallisticore.exceptions import CouldNotFindFunction
from kallisticore.exceptions import InvalidCredentialType
from kallisticore.lib.action import Action
from kallisticore.lib.action import FunctionLoader
from kallisticore.lib.credential import Credential,\
    UsernamePasswordCredential, TokenCredential
from kallisticore.lib.expectation import Expectation


class AwsFunctionLoader(FunctionLoader):
    def _find_function(self, function_name: str):
        method_name = function_name.split('.')[-1]
        for activity in discover(False)['activities']:
            if activity.get('name') == method_name:
                module = importlib.import_module(activity.get('mod'))
                return getattr(module, method_name)
        raise CouldNotFindFunction(
            self._module_path + "." + function_name)


class AwsAction(Action):
    func_loader_class = AwsFunctionLoader

    def __init__(self, module_func, arguments: Dict,
                 expectations: [Expectation] = None, name: str = None,
                 credential: Credential = None):
        super(AwsAction, self).__init__(
            module_func=module_func, arguments=arguments,
            expectations=expectations, name=name, credential=credential)
        if isinstance(self.credential, UsernamePasswordCredential) \
                or isinstance(self.credential, TokenCredential):
            raise InvalidCredentialType('Environment variables should be used '
                                        'for AWS client config.')
        if 'region' in arguments:
            self.arguments['configuration'] = {
                'aws_region': arguments.pop('region')}
