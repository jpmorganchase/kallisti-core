import os
from unittest.mock import patch

import kallisticore.lib.action
import kallisticore.modules.common
import kallisticore.modules.examples.sample_module1 as sample_module
import kallisticore.modules.examples.sample_module2.increment_action as \
    sample_module2_increment
import kallisticore.modules.examples.sample_module2.subtract_action as \
    sample_module2_subtract
from django.conf import settings
from django.test import TestCase
from kallisticore.exceptions import CouldNotFindFunction, UnknownModuleName
from kallisticore.lib.action import FunctionLoader, Action
from kallisticore.lib.action import make_action
from kallisticore.lib.credential import EnvironmentUserNamePasswordCredential
from kallisticore.lib.expectation import OperatorExpectation
from kallisticore.models.step import Step
from kallisticore.modules.cloud_foundry.cloud_foundry_action import \
    CloudFoundryAction


class TestFunctionLoader(TestCase):
    MODULE_MAP = {'eg': 'kallisticore.modules.examples.sample_module1',
                  'eg2': 'kallisticore.modules.examples.sample_module2'}

    def test_single_module(self):
        # Action functions are defined in single module
        # with __all__ defined, and no __actions_modules__
        # Check we can load the correct function.

        action_function = FunctionLoader(self.MODULE_MAP, 'eg')\
            .get_function('increment')
        self.assertEqual(action_function, sample_module.increment)

    def test_single_module_no_export(self):
        # Action functions are defined in single module
        # and __all__ and __actions_modules__ are undefined.
        # Check raised exception.
        module_path = 'kallisticore.modules.examples.sample_module1.__all__'
        with patch(module_path, []), \
                self.assertRaises(CouldNotFindFunction) as cm:
            FunctionLoader(self.MODULE_MAP, 'eg').get_function('increment')
        self.assertEqual(cm.exception.args[0], 'eg.increment')

    def test_multiple_modules_with_actions_and_action_modules(self):
        # Action functions are defined in multiple modules
        # with __all__ and __actions_modules__ defined.

        func = FunctionLoader(self.MODULE_MAP, 'eg2').get_function('increment')
        self.assertEqual(func, sample_module2_increment.increment)
        func = FunctionLoader(self.MODULE_MAP, 'eg2').get_function('Add')
        self.assertEqual(func, sample_module2_increment.Add)
        func = FunctionLoader(self.MODULE_MAP, 'eg2').get_function('subtract')
        self.assertEqual(func, sample_module2_subtract.subtract)

    def test_multiple_modules_with_only_action_modules(self):
        # Action functions are defined in multiple modules
        # with __all__ undefined in module file,
        # and __actions_modules__ defined.
        module_path = 'kallisticore.modules.examples.sample_module2.' \
                      'increment_action.__all__'
        with patch(module_path, []):
            func_loader = FunctionLoader(self.MODULE_MAP, 'eg2')
            func = func_loader.get_function('subtract')
            self.assertEqual(func, sample_module2_subtract.subtract)
            with self.assertRaises(CouldNotFindFunction) as cm:
                func_loader.get_function('increment')
            self.assertEqual(cm.exception.args[0], 'eg2.increment')

    def test_no_module_error(self):
        # Kallisti module name defined in the experiment does not exist in
        # ACTION_NAMESPACE.
        with self.assertRaises(UnknownModuleName) as cm:
            func_loader = FunctionLoader(self.MODULE_MAP,
                                         'unknown_kallisti_module')
            func_loader.get_function('function_name')
        self.assertEqual(cm.exception.args[0], 'unknown_kallisti_module')

    def test_no_function_error(self):
        # One of the function name in the experiment does not exist.
        with self.assertRaises(CouldNotFindFunction) as cm:
            FunctionLoader(self.MODULE_MAP, 'eg').get_function('function_name')
        self.assertEqual(cm.exception.args[0], 'eg.function_name')


class TestAction(TestCase):
    MODULE_MAP = {'eg': 'kallisticore.modules.examples.sample_module1',
                  'eg2': 'kallisticore.modules.examples.sample_module2'}
    CRED_CLS_MAP = {'ENV_VAR_USERNAME_PASSWORD':
                    'kallisticore.lib.credential.'
                    'EnvironmentUserNamePasswordCredential'}

    def test_action_build(self):
        # Check for action implemented as function.
        action_arguments = {'a': 1}

        step = Step.build({'step': 'increment',
                           'do': 'eg.increment',
                           'where': action_arguments})
        action = Action.build(step, self.MODULE_MAP, {})

        self.assertIsInstance(action, Action)
        self.assertEqual('increment', action.name)
        self.assertEqual(
            getattr(kallisticore.modules.examples.sample_module1, 'increment'),
            action.func)
        self.assertEqual(action_arguments, action.arguments)
        self.assertEqual(None, action.credential)
        self.assertEqual([], action.expectations)

    def test_action_build_with_expectations(self):
        # Check for action implemented as function.
        action_arguments = {'a': 1}
        step = Step.build({'step': 'increment',
                           'do': 'eg.increment',
                           'where': action_arguments,
                           'expect': [{'operator': 'eq', 'value': 2}]})
        action = Action.build(step, self.MODULE_MAP, {})

        self.assertIsInstance(action, Action)
        self.assertEqual('increment', action.name)
        self.assertEqual(
            getattr(kallisticore.modules.examples.sample_module1, 'increment'),
            action.func)
        self.assertEqual(action_arguments, action.arguments)
        self.assertEqual(None, action.credential)
        self.assertEqual(1, len(action.expectations))
        self.assertIsInstance(action.expectations[0], OperatorExpectation)

    def test_action_build_with_credentials_initialized(self):
        username_key = 'TEST_USER'
        password_key = 'TEST_PASSWORD'
        os.environ[username_key] = 'my-username'
        os.environ[password_key] = 'my-secret'

        action_arguments = {
            'a': 1,
            'credentials': {'type': 'ENV_VAR_USERNAME_PASSWORD',
                            'username_key': username_key,
                            'password_key': password_key}}
        step = Step.build({'step': 'increment',
                           'do': 'eg.increment',
                           'where': action_arguments})
        action = Action.build(step, self.MODULE_MAP, self.CRED_CLS_MAP)

        self.assertIsInstance(action.credential,
                              EnvironmentUserNamePasswordCredential)
        self.assertEqual(username_key, action.credential.username_key)
        self.assertEqual(password_key, action.credential.password_key)

    def test_action_initialize_sets_up_the_attributes(self):
        action_arguments = {'a': 1}
        expect = {'operator': 'eq', 'value': 2}
        step = Step.build({'step': 'increment',
                           'do': 'eg.increment',
                           'where': action_arguments,
                           'expect': [expect]})
        action = Action.build(step, self.MODULE_MAP, {})

        self.assertIsInstance(action, Action)
        self.assertEqual('increment', action.name)
        self.assertEqual(
            getattr(kallisticore.modules.examples.sample_module1, 'increment'),
            action.func)
        self.assertEqual(action_arguments, action.arguments)
        self.assertEqual(None, action.credential)
        self.assertIsInstance(action.expectations[0], OperatorExpectation)

    def test_execute_function_action(self):
        # Check for action implemented as function.
        step = Step.build({'step': 'increment',
                           'do': 'eg.increment',
                           'where': {'a': 1}})
        action = Action.build(step, self.MODULE_MAP, {})

        self.assertEqual(2, action.execute())

    def test_execute_class_action(self):
        step = Step.build({'step': 'add',
                           'do': 'eg2.Add',
                           'where': {'a': 1, 'b': 2}})
        action = Action.build(step, self.MODULE_MAP, {})

        self.assertEqual(3, action.execute())


class TestMakeAction(TestCase):
    MODULE_MAP = {'eg': 'kallisticore.modules.examples.sample_module1',
                  'eg2': 'kallisticore.modules.examples.sample_module2'}

    def test_unknown_module_name(self):
        step = Step.build({'step': 'increment',
                           'do': 'unknown_module.increment',
                           'where': {'a': None}})
        with self.assertRaises(UnknownModuleName) as cm:
            make_action(step, self.MODULE_MAP, {})
        self.assertEqual(cm.exception.args[0], 'unknown_module')

    def test_with_factory_function_for_cloud_foundry(self):
        module_map = {'cf': 'kallisticore.modules.cloud_foundry'}
        step = Step.build({'step': 'get_app_stats',
                           'do': 'cf.get_app_stats',
                           'where': {'cf_api_url': 'https://cf-api.test',
                                     'a': 1, 'b': 2}})
        action = make_action(step, module_map, {})
        self.assertIsInstance(action, CloudFoundryAction)

    def test_default_action(self):
        step = Step.build({'step': 'increment',
                           'do': 'eg.increment',
                           'where': {'a': 1}})
        action = make_action(step, self.MODULE_MAP, {})
        self.assertIsInstance(action, Action)


class TestActionNamespace(TestCase):

    def test_action_namespace(self):
        action_namespace = {'cf': 'kallisticore.modules.cloud_foundry',
                            'cm': 'kallisticore.modules.common',
                            'k8s': 'kallisticore.modules.kubernetes',
                            'istio': 'kallisticore.modules.kubernetes',
                            'prom': 'kallisticore.modules.prometheus',
                            'aws': 'kallisticore.modules.aws'}
        default_module_map = getattr(settings, 'KALLISTI_MODULE_MAP', {})
        self.assertEqual(action_namespace, default_module_map)
