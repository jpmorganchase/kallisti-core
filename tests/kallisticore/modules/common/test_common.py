import base64
import json
from unittest import TestCase, mock
from unittest.mock import Mock, mock_open

import requests_mock
from kallisticore.exceptions import FailedAction, InvalidHttpProbeMethod, \
    InvalidCredentialType, InvalidHttpRequestMethod
from kallisticore.lib.credential import \
    EnvironmentUserNamePasswordCredential, \
    KubernetesServiceAccountTokenCredential
from kallisticore.modules import common
from kallisticore.modules.common import wait, http_probe, http_request


class TestCommonModule(TestCase):
    def test_exported_functions(self):
        self.assertListEqual(
            ['http_probe', 'http_request', 'wait'],
            common.__all__)


class TestHttpProbe(TestCase):
    test_uname = 'test-username'
    test_pw = 'test-password'

    def setUp(self):
        self._url = "http://go.test/-/status/health"
        self._headers = {"Content-type": "text/html"}

    def test_exception_for_invalid_method(self):
        method = "PUT"
        with self.assertRaises(InvalidHttpProbeMethod) as error:
            http_probe(url=self._url, method=method)
        self.assertEqual(
            "Invalid method: {}. HTTP Probe allows only GET and POST methods"
            .format(method),
            error.exception.message)

    @requests_mock.mock()
    def test_empty_response_without_request_headers(self, mock_request):
        data = {'status': 'UP'}
        response = json.dumps(data)
        mock_request.get(url=self._url, text=response)
        result = http_probe(url=self._url)

        self.assertEqual(response, result['response_text'])
        self.assertEqual(data, result['response'])
        self.assertEqual(200, result['status_code'])
        self.assertEqual({}, result['response_headers'])

    @requests_mock.mock()
    def test_non_json_response(self, mock_request):
        mock_request.get(self._url, text='non-json response')

        result = http_probe(url=self._url)
        self.assertNotIn('response', result)

    @requests_mock.mock()
    def test_response_headers_with_request_headers(self, mock_request):
        response = json.dumps({'status': 'UP'})
        mock_request.get(url=self._url, text=response, headers=self._headers)

        result = http_probe(url=self._url)
        self.assertEqual(self._headers, result['response_headers'])

    def test_exception_for_4xx_or_5xx_status_code_without_headers(self):
        text = 'Not Found'
        status_code = 404
        mock_duration = 1

        with self.assertRaises(FailedAction) as error:
            with mock.patch('requests.get') as mock_get:
                mock_get.return_value.status_code = status_code
                mock_get.return_value.text = text
                mock_get.return_value.elapsed.total_seconds.return_value = \
                    mock_duration
                http_probe(url=self._url)

        self.assertEqual(
            "Http probe failed after {} seconds for url {} with status "
            "code {}. Details: {}".format(mock_duration,
                                          self._url, status_code, text),
            error.exception.message)

    @requests_mock.mock()
    def test_response_with_headers(self, mock_request):
        response = json.dumps({'status': 'UP'})
        mock_request.get(url=self._url, text=response, headers=self._headers)

        result = http_probe(url=self._url, headers=self._headers)

        self.assertEqual(response, result['response_text'])
        self.assertEqual(200, result['status_code'])
        self.assertEqual(self._headers, result['response_headers'])

    @requests_mock.mock()
    def test_empty_response_headers_with_request_headers(self, mock_request):
        response = json.dumps({'status': 'UP'})
        mock_request.get(url=self._url, text=response)

        result = http_probe(url=self._url, headers=self._headers)
        self.assertEqual({}, result['response_headers'])

    def test_exception_for_4xx_or_5xx_with_headers(self):
        text = 'Not Found'
        status_code = 404
        mock_duration = 1

        with self.assertRaises(FailedAction) as error:
            with mock.patch('requests.get') as mock_get:
                mock_get.return_value.status_code = status_code
                mock_get.return_value.elapsed.total_seconds.return_value = \
                    mock_duration
                mock_get.return_value.text = text
                http_probe(url=self._url, headers=self._headers)

        self.assertEqual("Http probe failed after {} seconds for url {} with "
                         "status code {}. Details: {}"
                         .format(mock_duration, self._url, status_code, text),
                         error.exception.message)

    @requests_mock.mock()
    def test_post_empty_response_headers(self, mock_request):
        method = "POST"
        response = json.dumps({'status': 'UP'})
        mock_request.post(url=self._url, text=response)

        result = http_probe(url=self._url, method=method)
        self.assertEqual(response, result['response_text'])
        self.assertEqual(200, result['status_code'])
        self.assertEqual({}, result['response_headers'])

    @requests_mock.mock()
    def test_post_request_body_with_response_headers(self, mock_request):
        method = "POST"
        text = json.dumps({'key': 'value'})
        mock_request.post(url=self._url, text=json.dumps(text),
                          headers=self._headers)

        result = http_probe(url=self._url, request_body=text, method=method)
        self.assertEqual(self._headers, result['response_headers'])

    def test_post_exception_for_4xx_or_5xx_(self):
        text = 'Not Found'
        method = "POST"
        status_code = 404
        mock_duration = 1

        with self.assertRaises(FailedAction) as error:
            with mock.patch('requests.post') as mock_post:
                mock_post.return_value.status_code = status_code
                mock_post.return_value.elapsed.total_seconds.return_value = \
                    mock_duration
                mock_post.return_value.text = text
                http_probe(url=self._url, method=method)

        self.assertEqual("Http probe failed after {} seconds for url {} "
                         "with status code {}. Details: {}"
                         .format(mock_duration, self._url, status_code, text),
                         error.exception.message)

    @requests_mock.mock()
    def test_post_with_headers(self, mock_request):
        method = "POST"
        response = json.dumps({'status': 'UP'})
        mock_request.post(url=self._url, text=response, headers=self._headers)

        result = http_probe(url=self._url, method=method,
                            headers=self._headers)

        self.assertEqual(response, result['response_text'])
        self.assertEqual(200, result['status_code'])
        self.assertEqual(self._headers, result['response_headers'])

    @requests_mock.mock()
    def test_post_empty_response_header(self, mock_request):
        method = "POST"
        response = json.dumps({'status': 'UP'})
        mock_request.post(url=self._url, text=response)

        result = http_probe(url=self._url, method=method,
                            headers=self._headers)
        self.assertEqual({}, result['response_headers'])

    def test_post_exception_for_4xx_or_5xx_with_headers(self):
        text = 'Not Found'
        method = "POST"
        status_code = 404
        mock_duration = 1

        with self.assertRaises(FailedAction) as error:
            with mock.patch('requests.post') as mock_post:
                mock_post.return_value.status_code = status_code
                mock_post.return_value.elapsed.total_seconds.return_value = \
                    mock_duration
                mock_post.return_value.text = text
                http_probe(url=self._url, method=method, headers=self._headers)

        self.assertEqual("Http probe failed after {} seconds for url {} "
                         "with status code {}. Details: {}"
                         .format(mock_duration, self._url, status_code, text),
                         error.exception.message)

    @requests_mock.mock()
    def test_k8s_auth_with_header(self, mock_request):
        with mock.patch('kallisticore.modules.common.Credential') \
                as mock_credential_module, \
                mock.patch('builtins.open', mock_open(read_data='test-token')):
            mock_k8s_creds = KubernetesServiceAccountTokenCredential()
            mock_credential_module.build.return_value = mock_k8s_creds
            auth_config = {
                'type': 'oauth2_token',
                'credentials': {}
            }
            expected_headers = {'Authorization': 'test-token', **self._headers}
            response = json.dumps({'status': 'UP'})
            mock_request.get(url=self._url, text=response,
                             headers=expected_headers)

            result = http_probe(url=self._url, headers=self._headers,
                                authentication=auth_config)
            self.assertEqual(response, result['response_text'])
            self.assertEqual(200, result['status_code'])

    @requests_mock.mock()
    def test_env_pw_auth_without_header(self, mock_request):
        with mock.patch('kallisticore.modules.common.Credential') \
                as mock_credential_module:
            mock_credential = Mock(spec=EnvironmentUserNamePasswordCredential)
            mock_credential.username.return_value = TestHttpProbe.test_uname
            mock_credential.password.return_value = TestHttpProbe.test_pw
            mock_credential.fetch.side_effects = None
            mock_credential_module.build.return_value = mock_credential
            test_auth_url = 'https://test-auth.com'
            auth_config = {
                'type': 'oauth2_token',
                'url': test_auth_url,
                'credentials': {},
                'client': {
                    'id': 'test-client-id',
                    'secret': 'test-client-secret'
                }
            }
            expected_base64 = base64.b64encode(
                (auth_config['client']['id'] + ':' +
                 auth_config['client']['secret']).encode()).decode('utf-8')
            auth_expected_headers = {
                'Authorization': 'Basic %s' % expected_base64}
            auth_mock_response = json.dumps({'access_token': 'test-token'})
            mock_request.post(url=test_auth_url, text=auth_mock_response,
                              headers=auth_expected_headers)

            probe_expected_headers = {'Authorization': 'test-token'}
            response = json.dumps({'status': 'UP'})
            mock_request.get(url=self._url, text=response,
                             headers=probe_expected_headers)

            result = http_probe(url=self._url, authentication=auth_config)
            self.assertEqual(response, result['response_text'])
            self.assertEqual(200, result['status_code'])

    @requests_mock.mock()
    def test_env_pw_auth_with_resource(self, mock_request):
        with mock.patch('kallisticore.modules.common.Credential') \
                as mock_credential_module:
            mock_credential = Mock(spec=EnvironmentUserNamePasswordCredential)
            mock_credential.username.return_value = TestHttpProbe.test_uname
            mock_credential.password.return_value = TestHttpProbe.test_pw
            mock_credential.fetch.side_effects = None
            mock_credential_module.build.return_value = mock_credential
            test_auth_url = 'https://test-auth.com'
            auth_config = {
                'type': 'oauth2_token',
                'url': test_auth_url,
                'credentials': {},
                'client': {
                    'id': 'test-client-id',
                    'secret': 'test-client-secret'
                },
                'resource': 'test-resource-value',
                'token_key': 'different_token_key'
            }
            expected_base64 = base64.b64encode(
                (auth_config['client']['id'] + ':' +
                 auth_config['client']['secret']).encode()).decode('utf-8')
            auth_expected_headers = {
                'Authorization': 'Basic %s' % expected_base64}
            auth_mock_response = json.dumps(
                {'access_token': 'test-token',
                 'different_token_key': 'different-token'})
            mock_auth_post = mock_request.post(url=test_auth_url,
                                               text=auth_mock_response,
                                               headers=auth_expected_headers)

            probe_expected_headers = {'Authorization': 'different-token'}
            response = json.dumps({'status': 'UP'})
            mock_request.get(url=self._url, text=response,
                             headers=probe_expected_headers)

            result = http_probe(url=self._url, authentication=auth_config)
            self.assertEqual(response, result['response_text'])
            self.assertEqual(200, result['status_code'])
            self.assertTrue('resource=test-resource-value' in
                            mock_auth_post.last_request.body)

    def test_env_pw_authentication_fail(self):
        with mock.patch('kallisticore.modules.common.Credential') \
                as mock_credential_module:
            mock_credential = Mock(spec=EnvironmentUserNamePasswordCredential)
            mock_credential.username.return_value = TestHttpProbe.test_uname
            mock_credential.password.return_value = TestHttpProbe.test_pw
            mock_credential.fetch.side_effects = None
            mock_credential_module.build.return_value = mock_credential
            test_auth_url = 'https://test-auth.com'
            auth_config = {
                'type': 'oauth2_token',
                'url': test_auth_url,
                'credentials': {},
                'client': {
                    'id': 'test-client-id',
                    'secret': 'test-client-secret'
                }
            }

            mock_response_status_code = 404
            mock_response_text = 'test-error-message'

            with self.assertRaises(FailedAction) as error:
                with mock.patch('requests.post') as mock_post:
                    mock_post.return_value.status_code = \
                        mock_response_status_code
                    mock_post.return_value.text = mock_response_text
                    http_probe(url=self._url, authentication=auth_config)

            self.assertEqual(
                'Authentication for http request failed with status code {}. '
                'Details: {}'.format(mock_response_status_code,
                                     mock_response_text),
                error.exception.message)

    def test_authentication_unknown_credential(self):
        with mock.patch('kallisticore.modules.common.Credential') \
                as mock_credential_module:
            mock_credential = Mock()
            mock_credential_module.build.return_value = mock_credential
            auth_config = {
                'type': 'oauth2_token',
                'credentials': {}
            }

            with self.assertRaises(InvalidCredentialType) as error:
                http_probe(url=self._url, authentication=auth_config)

            self.assertEqual('Invalid credential type: %s' %
                             mock_credential.__class__.__name__,
                             error.exception.message)


class TestHttpRequest(TestCase):
    def setUp(self):
        self._url = "http://test.com/-/status/health"
        self._headers = {"Content-type": "text/html"}

    def test_exception_when_invalid_method_is_provided(self):
        method = "INVALID_METHOD"
        with self.assertRaises(InvalidHttpRequestMethod) as error:
            http_request(url=self._url, method=method)
        self.assertEqual("Invalid method: {}. Please specify a valid HTTP "
                         "request method".format(method),
                         error.exception.message)

    @requests_mock.mock()
    def test_not_raise_exception_for_4xx_or_5xx_(self, mock_request):
        text = 'Not Found'
        status_code = 404
        mock_request.get(url=self._url, text=text, status_code=status_code)

        response = json.dumps({'status': 'UP'})
        mock_request.get(url=self._url, text=response, headers=self._headers)

        result = http_request(url=self._url, headers=self._headers)

        self.assertEqual(response, result['response_text'])
        self.assertEqual(200, result['status_code'])
        self.assertEqual(self._headers, result['response_headers'])

    @requests_mock.mock()
    def test_non_json_response(self, mock_request):
        mock_request.get(self._url, text='non-json response')

        result = http_request(url=self._url)
        self.assertNotIn('response', result)

    @requests_mock.mock()
    def test_get_response(self, mock_request):
        data = {'status': 'UP'}
        response = json.dumps(data)
        mock_request.get(url=self._url, text=response, headers=self._headers)

        result = http_request(url=self._url, headers=self._headers)

        self.assertEqual(response, result['response_text'])
        self.assertEqual(data, result['response'])
        self.assertEqual(200, result['status_code'])
        self.assertEqual(self._headers, result['response_headers'])

    @requests_mock.mock()
    def test_get_empty_response_headers(self, mock_request):
        data = {'status': 'UP'}
        response = json.dumps(data)
        mock_request.get(url=self._url, text=response)
        result = http_request(url=self._url)

        self.assertEqual(response, result['response_text'])
        self.assertEqual(data, result['response'])
        self.assertEqual(200, result['status_code'])
        self.assertEqual({}, result['response_headers'])

    @requests_mock.mock()
    def test_post_empty_response_headers(self, mock_request):
        method = "POST"
        response = json.dumps({'status': 'UP'})
        mock_request.post(url=self._url, text=response)

        result = http_request(url=self._url, method=method)
        self.assertEqual(response, result['response_text'])
        self.assertEqual(200, result['status_code'])
        self.assertEqual({}, result['response_headers'])

    @requests_mock.mock()
    def test_post_request_body_without_request_header(self, mock_request):
        method = "POST"
        text = json.dumps({'key': 'data'})
        mock_request.post(url=self._url, text=text, headers=self._headers)

        result = http_request(url=self._url, method=method, request_body=text)
        self.assertEqual(self._headers, result['response_headers'])

    @requests_mock.mock()
    def test_post_request_with_request_headers(self, mock_request):
        method = "POST"
        response = json.dumps({'status': 'UP'})
        mock_request.post(url=self._url, text=response, headers=self._headers)

        result = http_request(url=self._url, method=method,
                              headers=self._headers)

        self.assertEqual(response, result['response_text'])
        self.assertEqual(200, result['status_code'])
        self.assertEqual(self._headers, result['response_headers'])

    @requests_mock.mock()
    def test_put_with_request_headers(self, mock_request):
        method = "PUT"
        response = json.dumps({'status': 'UP'})
        mock_request.put(url=self._url, text=response)

        result = http_request(url=self._url, method=method,
                              headers=self._headers)
        self.assertEqual(response, result['response_text'])
        self.assertEqual(200, result['status_code'])
        self.assertEqual({}, result['response_headers'])

    @requests_mock.mock()
    def test_put_request_body_with_response_headers(self, mock_request):
        method = "PUT"
        text = json.dumps({'key': 'value'})
        mock_request.put(url=self._url, text=text, headers=self._headers)

        result = http_request(url=self._url, method=method, request_body=text)
        self.assertEqual(text, result['response_text'])
        self.assertEqual(200, result['status_code'])
        self.assertEqual(self._headers, result['response_headers'])

    @requests_mock.mock()
    def test_patch_without_headers(self, mock_request):
        method = "PATCH"
        response = json.dumps({'status': 'UP'})
        mock_request.patch(url=self._url, text=response)

        result = http_request(url=self._url, method=method)
        self.assertEqual(response, result['response_text'])
        self.assertEqual(200, result['status_code'])
        self.assertEqual({}, result['response_headers'])

    @requests_mock.mock()
    def test_patch_request_body_with_headers(self, mock_request):
        method = "PATCH"
        text = json.dumps({'key': 'value'})
        mock_request.patch(url=self._url, text=text, headers=self._headers)

        result = http_request(url=self._url, method=method, request_body=text)
        self.assertEqual(text, result['response_text'])
        self.assertEqual(200, result['status_code'])
        self.assertEqual(self._headers, result['response_headers'])

    @requests_mock.mock()
    def test_delete_with_empty_response_headers(self, mock_request):
        method = "DELETE"
        response = json.dumps({'status': 'UP'})
        mock_request.delete(url=self._url, text=response)
        mock_request.delete(url=self._url, text=response, status_code=204)

        result = http_request(url=self._url, method=method)
        self.assertEqual(response, result['response_text'])
        self.assertEqual(204, result['status_code'])
        self.assertEqual({}, result['response_headers'])

    @requests_mock.mock()
    def test_delete_request_body_with_headers(self, mock_request):
        method = "DELETE"
        response = json.dumps({'status': 'UP'})
        mock_request.delete(url=self._url, text=response, status_code=204,
                            headers=self._headers)

        result = http_request(url=self._url, method=method)
        self.assertEqual(response, result['response_text'])
        self.assertEqual(204, result['status_code'])
        self.assertEqual(self._headers, result['response_headers'])

    @requests_mock.mock()
    def test_authentication_k8s_with_header(self, mock_request):
        with mock.patch('kallisticore.modules.common.Credential') \
                as mock_credential_module, \
                mock.patch('builtins.open', mock_open(read_data='test-token')):
            mock_k8s_creds = KubernetesServiceAccountTokenCredential()
            mock_credential_module.build.return_value = mock_k8s_creds
            auth_config = {
                'type': 'oauth2_token',
                'credentials': {}
            }
            expected_headers = {'Authorization': 'test-token', **self._headers}
            response = json.dumps({'status': 'UP'})
            mock_request.get(url=self._url, text=response,
                             headers=expected_headers)

            result = http_request(url=self._url, headers=self._headers,
                                  authentication=auth_config)
            self.assertEqual(response, result['response_text'])
            self.assertEqual(200, result['status_code'])

    @requests_mock.mock()
    def test_env_pw_auth_without_header(self, mock_request):
        with mock.patch('kallisticore.modules.common.Credential') \
                as mock_credential_module:
            mock_credential = Mock(spec=EnvironmentUserNamePasswordCredential)
            mock_credential.username.return_value = TestHttpProbe.test_uname
            mock_credential.password.return_value = TestHttpProbe.test_pw
            mock_credential.fetch.side_effects = None
            mock_credential_module.build.return_value = mock_credential
            test_auth_url = 'https://test-auth.com'
            auth_config = {
                'type': 'oauth2_token',
                'url': test_auth_url,
                'credentials': {},
                'client': {
                    'id': 'test-client-id',
                    'secret': 'test-client-secret'
                }
            }
            expected_base64 = base64.b64encode(
                (auth_config['client']['id'] + ':' +
                 auth_config['client']['secret']).encode()).decode('utf-8')
            auth_expected_headers = {
                'Authorization': 'Basic %s' % expected_base64}
            auth_mock_response = json.dumps({'access_token': 'test-token'})
            mock_request.post(url=test_auth_url, text=auth_mock_response,
                              headers=auth_expected_headers)

            request_expected_headers = {'Authorization': 'test-token'}
            response = json.dumps({'status': 'UP'})
            mock_request.get(url=self._url, text=response,
                             headers=request_expected_headers)

            result = http_request(url=self._url, authentication=auth_config)
            self.assertEqual(response, result['response_text'])
            self.assertEqual(200, result['status_code'])

    def test_env_pw_auth_failure(self):
        with mock.patch('kallisticore.modules.common.Credential') \
                as mock_credential_module:
            mock_credential = Mock(spec=EnvironmentUserNamePasswordCredential)
            mock_credential.username.return_value = TestHttpProbe.test_uname
            mock_credential.password.return_value = TestHttpProbe.test_pw
            mock_credential.fetch.side_effects = None
            mock_credential_module.build.return_value = mock_credential
            test_auth_url = 'https://test-auth.com'
            auth_config = {
                'type': 'oauth2_token',
                'url': test_auth_url,
                'credentials': {},
                'client': {
                    'id': 'test-client-id',
                    'secret': 'test-client-secret'
                }
            }

            mock_response_status_code = 404
            mock_response_text = 'test-error-message'

            with self.assertRaises(FailedAction) as error:
                with mock.patch('requests.post') as mock_post:
                    mock_post.return_value.status_code = \
                        mock_response_status_code
                    mock_post.return_value.text = mock_response_text
                    http_request(url=self._url, authentication=auth_config)

            self.assertEqual(
                'Authentication for http request failed with status code {}. '
                'Details: {}'.format(mock_response_status_code,
                                     mock_response_text),
                error.exception.message)

    def test_authentication_should_fail_with_unknown_credential(self):
        with mock.patch('kallisticore.modules.common.Credential') \
                as mock_credential_module:
            mock_credential = Mock()
            mock_credential_module.build.return_value = mock_credential
            auth_config = {
                'type': 'oauth2_token',
                'credentials': {}
            }

            with self.assertRaises(InvalidCredentialType) as error:
                http_request(url=self._url, authentication=auth_config)

            self.assertEqual('Invalid credential type: %s' %
                             mock_credential.__class__.__name__,
                             error.exception.message)


class TestWait(TestCase):
    @mock.patch('time.sleep')
    def test_wait_for_15_seconds(self, mock_sleep):
        wait(time_in_seconds=15)
        mock_sleep.assert_called_once_with(15)

    def test_exception_for_invalid_input(self):
        with self.assertRaises(FailedAction) as error:
            wait(time_in_seconds=None)

        self.assertEqual(
            "Expected integer for argument 'time_in_seconds' (got NoneType)",
            error.exception.message)
