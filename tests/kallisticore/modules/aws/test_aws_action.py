from unittest import TestCase, mock
from unittest.mock import Mock

from kallisticore.exceptions import CouldNotFindFunction, InvalidCredentialType
from kallisticore.lib.action import Action
from kallisticore.lib.credential import TokenCredential
from kallisticore.models.step import Step
from kallisticore.modules.aws import AwsAction
from kallisticore.modules.aws.aws_action import AwsFunctionLoader


class TestAwsAction(TestCase):
    module_map = {'aws': 'kallisticore.modules.aws'}

    def setUp(self):
        self.username = 'test_username'
        self.password = 'test_password'
        self.arguments = {}

    def test_initialize(self):
        arguments = {}
        action_name = 'Get policy'
        step = Step.build({'step': action_name,
                           'do': 'aws.iam.get_policy',
                           'where': arguments})
        action = AwsAction.build(step, self.module_map, {})

        self.assertIsInstance(action, AwsAction)
        self.assertIsInstance(action, Action)
        self.assertEqual(action_name, action.name)
        self.assertEqual(
            AwsFunctionLoader(self.module_map, 'aws')
            .get_function('iam.get_policy'),
            action.func)
        self.assertEqual(arguments, action.arguments)
        action.func = mock.Mock()
        action.execute()

    def test_aws_method_not_found(self):
        with self.assertRaises(CouldNotFindFunction) as exception:
            AwsFunctionLoader(self.module_map, 'aws')\
                .get_function('non-existing-method')
        self.assertEqual('aws.non-existing-method',
                         exception.exception.message)

    def test_invalid_credential_type(self):
        arguments = {'credentials': {}}
        mock_token_credential = Mock(spec=TokenCredential)
        with self.assertRaises(InvalidCredentialType) as error_context:
            AwsAction(module_func=mock.Mock(),
                      arguments=arguments, name='Test Aws',
                      credential=mock_token_credential)
        self.assertEqual('Invalid credential type: Environment variables '
                         'should be used for AWS client config.',
                         str(error_context.exception))
