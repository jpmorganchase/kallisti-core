import importlib
import inspect
from copy import deepcopy
from typing import Dict, Callable, Any, List, Optional

from kallisticore.exceptions import UnknownModuleName, CouldNotFindFunction
from kallisticore.lib.credential import Credential
from kallisticore.lib.expectation import Expectation
from kallisticore.models.step import Step
from kallisticore.utils.singleton import Singleton


class KallistiFunctionCache(metaclass=Singleton):
    def __init__(self):
        self.functions = {}

    def add(self, module_name: str, function_name: str,
            function_implementation: Callable) -> None:
        key = self._function_key(function_name, module_name)
        self.functions[key] = function_implementation

    def get(self, module_name, function_name) -> Callable:
        key = self._function_key(module_name, function_name)
        return self.functions.get(key, None)

    def _function_key(self, function_name: str, module_name: str):
        return module_name, function_name


class FunctionLoader:

    def __init__(self, module_map: dict, module_name: str):
        """
        :param module_map: map of action modules
        :param module_name: the name of the module to search
         e.g. "cf".
        """
        self._functions = KallistiFunctionCache()
        self._module_path = module_name
        self.module = FunctionLoader.get_module(module_map, self._module_path)

    def get_function(self, function_name: str) -> Callable:
        """ Get the function based on the type_name.

        Caches the results for previous findings, and search the cache
        before searching the modules.

        :param function_name: the name of the function to search
            e.g. "map_route_to_app".
        :returns the function found or raise exception if no function can be
            found.
        """
        function_implementation = self._functions.get(self._module_path,
                                                      function_name)
        if not function_implementation:
            function_implementation = self._find_function(function_name)
            self._functions.add(self._module_path, function_name,
                                function_implementation)

        return function_implementation

    def _find_function(self, function_name: str) -> Callable:
        modules_to_search = self._get_modules_to_search()

        for module in modules_to_search:
            if hasattr(module, "__all__"):
                declared_action_names = getattr(module, "__all__")
                if function_name in declared_action_names:
                    function_implementation = getattr(module, function_name)
                    return function_implementation

        raise CouldNotFindFunction(self._module_path + "." + function_name)

    def _get_modules_to_search(self) -> list:
        modules_to_search = [self.module]

        if hasattr(self.module, "__actions_modules__"):
            sub_modules = self._get_sub_modules_to_search()
            modules_to_search.extend(sub_modules)

        return modules_to_search

    def _get_sub_modules_to_search(self) -> list:
        sub_module_names = getattr(self.module, "__actions_modules__")
        return [importlib.import_module(module_name) for module_name in
                sub_module_names]

    @staticmethod
    def get_module(module_map: dict, namespace: str):
        module_name = module_map.get(namespace)
        if not module_name:
            raise UnknownModuleName(namespace)
        module = importlib.import_module(module_name)
        return module


class Action:
    func_loader_class = FunctionLoader

    @classmethod
    def build(cls, step: Step, action_module_map: dict,
              credential_class_map: dict):
        """
        :param step: Object of type Step
        :param action_module_map: Map of action modules
        :param credential_class_map: Map of credential classes
        """
        description = step.description
        arguments = deepcopy(step.where)

        module_name = step.get_namespace()
        function_name = step.get_function_name()
        func_loader = cls.func_loader_class(action_module_map, module_name)
        module_func = func_loader.get_function(function_name)

        credential = None
        if 'credentials' in arguments:
            cred_dict = arguments.pop('credentials')
            credential = Credential.build(credential_class_map, cred_dict)

        expectations = []
        for expect_spec in step.expect:
            expectations.append(Expectation.build(expect_spec))
        return cls(module_func, arguments, expectations, description,
                   credential)

    def __init__(self, module_func: Callable, arguments: Dict,
                 expectations: Optional[List[Expectation]] = None,
                 name: str = None, credential: Credential = None):
        """
        :param module_func: Action module function
        :param arguments: Arguments required by function to be executed
        :param expectations: Expectation of action's result
        :param name: Description for the action to be execute
        :param credential: Holds credential required for action to be executed
        :type credential: Credential
        """
        self.expectations = expectations if expectations else []
        self.name = name
        self.func = module_func
        if inspect.isclass(self.func):
            self.func = self.func(**arguments).execute
            self.arguments = {}
        else:
            self.arguments = arguments
        self.credential = credential

    def execute(self) -> Any:
        """ Execute the action, captures the exception if any.

        :return True if the action has been executed successfully:
        """
        result = self.func(**self.arguments)
        self.check_result_for_expectations(result)
        return result

    def check_result_for_expectations(self, result):
        for expect_spec in self.expectations:
            expect_spec.execute(result)


def make_action(step: Step, action_module_map: dict,
                credential_class_map: dict) -> Action:
    """ Create Action based on the action type specified in action_spec.
    :param step: the action specification in json
        eg.g. {"step":"", "do":"", "where":{}}
    :param action_module_map: Action module map
    :param credential_class_map: Credential class map
    :returns a Kallisti Action object.
    """
    namespace = step.get_namespace()
    module = FunctionLoader.get_module(action_module_map, namespace)
    action_class = getattr(module, '__action_class__', Action)
    return action_class.build(step, action_module_map, credential_class_map)
