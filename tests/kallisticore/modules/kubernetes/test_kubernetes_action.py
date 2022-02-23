import base64
import re
from unittest import TestCase, mock
from unittest.mock import mock_open

import yaml
from kallisticore.exceptions import FailedAction
from kallisticore.lib.action import Action, FunctionLoader
from kallisticore.lib.credential import UsernamePasswordCredential
from kallisticore.models.step import Step
from kallisticore.modules.kubernetes import KubernetesAction


class MockUsernameCredential(UsernamePasswordCredential):
    def fetch(self):
        self._username = 'test-user'
        self._password = 'test-password'


class TestKubernetesAction(TestCase):
    module_map = {'k8s': 'kallisticore.modules.kubernetes'}
    K8S_POD_PATH = 'chaosk8s.pod.actions.terminate_pods'

    def setUp(self):
        self.namespace = 'test-namespace'
        self.label_selector = 'test-label-selector'
        self.qty = 1
        self.k8s_api_host = 'https://test-k8s-api-host.com'
        self.k8s_api_token = 'test-k8s-api-token'
        self.arguments = {'ns': self.namespace,
                          'label_selector': self.label_selector,
                          'qty': self.qty,
                          'k8s_api_host': self.k8s_api_host}
        self.action_spec = {'step': 'Test Kubernetes Terminate Pods Action',
                            'do': 'k8s.terminate_pods',
                            'where': self.arguments}
        self.step = Step.build(self.action_spec)

    def test_initialization(self):
        expected_credential = {
            'KUBERNETES_HOST': self.k8s_api_host,
            'KUBERNETES_API_KEY': self.k8s_api_token,
            'KUBERNETES_API_KEY_PREFIX': 'Bearer'}
        with mock.patch('builtins.open',
                        mock_open(read_data=self.k8s_api_token)):
            action = KubernetesAction.build(self.step, self.module_map, {})
        self.assertIsInstance(action, KubernetesAction)
        self.assertIsInstance(action, Action)
        self.assertEqual('Test Kubernetes Terminate Pods Action', action.name)
        expected_func = FunctionLoader(self.module_map, 'k8s')\
            .get_function('terminate_pods')
        self.assertEqual(expected_func, action.func)
        self.assertEqual(self.arguments['ns'], action.arguments['ns'])
        self.assertEqual(self.arguments['label_selector'],
                         action.arguments['label_selector'])
        self.assertEqual(self.arguments['qty'], action.arguments['qty'])
        self.assertTrue('k8s_api_host' not in action.arguments)
        self.assertEqual(expected_credential, action.arguments['secrets'])

    def test_execute_with_service_account(self):
        with mock.patch(self.K8S_POD_PATH) as mock_terminate_pods, \
                mock.patch('builtins.open',
                           mock_open(read_data=self.k8s_api_token)):
            action = KubernetesAction.build(self.step, self.module_map, {})
            action.execute()

        expected_credential = {
            'KUBERNETES_HOST': self.k8s_api_host,
            'KUBERNETES_API_KEY': self.k8s_api_token,
            'KUBERNETES_API_KEY_PREFIX': 'Bearer'
        }
        mock_terminate_pods.assert_called_once_with(
            ns=self.namespace, label_selector=self.label_selector,
            qty=self.qty, secrets=expected_credential)

    def test_execute_with_username_password(self):
        cred_cls_map = {
            'MockUsername': 'tests.kallisticore.modules.kubernetes.'
                            'test_kubernetes_action.MockUsernameCredential'}

        with mock.patch(self.K8S_POD_PATH) as mock_terminate_pods:
            arguments = {'ns': self.namespace,
                         'label_selector': self.label_selector,
                         'qty': self.qty,
                         'k8s_api_host': self.k8s_api_host,
                         'credentials': {'type': 'MockUsername'}}
            action_spec = {'step': 'Test Kubernetes Action',
                           'do': 'k8s.terminate_pods',
                           'where': arguments}
            step = Step.build(action_spec)

            action = KubernetesAction.build(step, self.module_map,
                                            cred_cls_map)
            action.execute()

        expected_credential = {
            'KUBERNETES_USERNAME': 'test-user',
            'KUBERNETES_PASSWORD': 'test-password',
            'KUBERNETES_HOST': self.k8s_api_host}

        mock_terminate_pods.assert_called_once_with(
            ns=self.namespace, label_selector=self.label_selector,
            qty=self.qty, secrets=expected_credential)

    @mock.patch('kallisticore.modules.kubernetes.'
                'kubernetes_actions.RequestSigner')
    def test_execute_eks_under_cf(self, mock_signer_cls):
        mock_signer = mock.Mock()
        mock_signer.generate_presigned_url.return_value = 'test-token'
        mock_signer_cls.return_value = mock_signer
        mock_fd = mock.Mock()

        class MockServiceModel:
            service_id = 'test-service-id'

        class MockBoto3Session:
            events = 'test-session-events'

            def __init__(self, **kwargs):
                pass

            class MockEksClient:
                def describe_cluster(self, **kwargs):
                    return {'cluster': {
                        'certificateAuthority': {
                            'data': 'test-ca-data'},
                        'endpoint': 'test-cluster-endpoint',
                        'arn': 'test-cluster-arn'}}

            class MockStsClient:
                class Meta:
                    service_model = MockServiceModel

                meta = Meta

            def client(self, service, **kwargs):
                if service == 'eks':
                    return self.MockEksClient()
                elif service == 'sts':
                    return self.MockStsClient()

            def get_credentials(self):
                return 'test-credentials'

        class MockBoto3SessionModule:
            class SessionWrapper:
                Session = MockBoto3Session

            DEFAULT_SESSION = None
            session = SessionWrapper

            @staticmethod
            def setup_default_session(**kwargs):
                return True

        boto3_path = 'kallisticore.modules.kubernetes.kubernetes_actions.boto3'
        arguments = {'platform': 'EKS',
                     'cluster_name': 'test-cluster',
                     'region': 'test-region',
                     'ns': self.namespace,
                     'label_selector': self.label_selector,
                     'qty': self.qty}
        action_spec = {'step': 'Test Kubernetes Action',
                       'do': 'k8s.terminate_pods',
                       'where': arguments}
        step = Step.build(action_spec)
        with mock.patch(boto3_path, MockBoto3SessionModule), \
                mock.patch("builtins.open") as mock_open, \
                mock.patch('chaosk8s.pod.actions.terminate_pods') \
                as mock_terminate_pods:
            mock_open.return_value = mock_fd
            action = KubernetesAction.build(step, self.module_map, {})
            action.execute()
        mock_signer_cls.assert_called_with(
            'test-service-id', 'test-region', 'sts', 'v4', 'test-credentials',
            'test-session-events')
        expected_token = 'k8s-aws-v1.' + re.sub(
            r'=*', '', base64.urlsafe_b64encode(
                'test-token'.encode('utf-8')).decode('utf-8'))
        expected_k8s_context = yaml.dump({
            'apiVersion': 'v1',
            'clusters': [
                {'cluster': {'server': 'test-cluster-endpoint',
                             'certificate-authority-data': 'test-ca-data'},
                 'name': 'test-cluster-arn'}],
            'contexts': [{'context': {'cluster': 'test-cluster-arn',
                                      'user': 'test-cluster-arn'},
                          'name': 'test-cluster-arn'}],
            'current-context': 'test-cluster-arn',
            'users': [{'name': 'test-cluster-arn',
                       'user': {'token': expected_token}}]},
            default_flow_style=False)
        mock_fd.write.assert_called_with(expected_k8s_context)
        expected_credential = {'KUBERNETES_CONTEXT': 'test-cluster-arn'}
        mock_terminate_pods.assert_called_once_with(
            ns=self.namespace, label_selector=self.label_selector,
            qty=self.qty, secrets=expected_credential)

    def test_unsupported_platform(self):
        self.arguments['platform'] = 'UNSUPPORTED_PLATFORM'
        with self.assertRaises(FailedAction) as context:
            action = KubernetesAction(mock.Mock(), self.arguments, [])
            action.execute()
        self.assertEqual(
            'K8s on the platform: unsupported_platform is not supported.',
            str(context.exception))
