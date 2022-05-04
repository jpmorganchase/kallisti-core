import base64
import json
import time
from json import JSONDecodeError
from typing import Dict, Optional

import requests
from django.conf import settings

from kallisticore import exceptions
from kallisticore.lib.credential import Credential, TokenCredential, \
    UsernamePasswordCredential

__all__ = ["http_probe", "http_request", "wait"]


def wait(time_in_seconds: int):
    if type(time_in_seconds) is not int:
        raise exceptions.FailedAction(
            "Expected integer for argument 'time_in_seconds' "
            "(got %s)" % type(time_in_seconds).__name__)

    time.sleep(time_in_seconds)


def http_request(url: str, method: str = "GET",
                 request_body: Optional[Dict] = None,
                 headers: Optional[Dict] = None,
                 authentication: Optional[Dict] = None) -> Dict:
    headers = extract_authentication_headers(authentication, headers)

    method = method.upper()
    if method in ["GET", "DELETE"]:
        response = requests.request(method, url=url, headers=headers)
    elif method in ["POST", "PATCH", "PUT"]:
        response = requests.request(method, url=url,
                                    data=json.dumps(request_body),
                                    headers=headers)
    else:
        raise exceptions.InvalidHttpRequestMethod(
            "Invalid method: {}. Please specify a valid HTTP request "
            "method".format(method))
    duration = response.elapsed.total_seconds()
    return _append_parsed_json_response(
        {'status_code': response.status_code, 'response_text': response.text,
         'response_headers': response.headers,
         'response_time_in_seconds': duration})


def http_probe(url: str, method: str = "GET",
               request_body: Optional[Dict] = None,
               headers: Optional[Dict] = None,
               authentication: Optional[Dict] = None) -> Dict:
    headers = extract_authentication_headers(authentication, headers)

    method = method.upper()
    if method == "GET":
        response = requests.get(url=url, headers=headers)
    elif method == "POST":
        response = requests.post(url=url, data=json.dumps(request_body),
                                 headers=headers)
    else:
        raise exceptions.InvalidHttpProbeMethod(
            "Invalid method: {}. "
            "HTTP Probe allows only GET and POST methods".format(method))
    duration = response.elapsed.total_seconds()
    if response.status_code < 400:
        return _append_parsed_json_response(
            {'status_code': response.status_code,
             'response_text': response.text,
             'response_headers': response.headers,
             'response_time_in_seconds': duration})
    raise exceptions.FailedAction(
        "Http probe failed after {} seconds for url {} with status code {}. "
        "Details: {}".format(duration, url, response.status_code,
                             response.text))


def _append_parsed_json_response(result: dict) -> Dict:
    try:
        result['response'] = json.loads(result['response_text'])
        return result
    except (ValueError, KeyError, JSONDecodeError):
        return result


def _get_oauth_token_for_http_request_auth_header(config: Dict) -> str:
    response_token_key = 'access_token'
    if 'token_key' in config:
        response_token_key = config['token_key']

    cred_class_map = getattr(settings, 'KALLISTI_CREDENTIAL_CLASS_MAP', {})
    credential = Credential.build(cred_class_map, config['credentials'])
    credential.fetch()

    if isinstance(credential, TokenCredential):
        return _format_oauth_token(credential.token)

    if isinstance(credential, UsernamePasswordCredential):
        request_body = {
            'grant_type': 'password',
            'username': credential.username,
            'password': credential.password
        }
        if 'resource' in config:
            request_body['resource'] = config['resource']
        client_secret = config['client']['secret'] \
            if 'secret' in config['client'] else ''
        client_base64 = base64.b64encode('{}:{}'.format(
            config['client']['id'], client_secret).encode()).decode('utf-8')
        headers = {'Authorization': 'Basic {}'.format(client_base64)}

        response = requests.post(config['url'], request_body, headers=headers)
        if response.status_code >= 400:
            raise exceptions.FailedAction(
                "Authentication for http request failed with status code {}. "
                "Details: {}".format(response.status_code, response.text))

        response_body = response.json()
        return _format_oauth_token(response_body[response_token_key])

    raise exceptions.InvalidCredentialType(credential.__class__.__name__)


def _format_oauth_token(token: str) -> str:
    auth_token_prefix = 'Bearer'
    return '{} {}'.format(auth_token_prefix, token)


def extract_authentication_headers(authentication, headers):
    if authentication:
        if authentication['type'] == 'oauth2_token' and headers:
            headers['Authorization'] = \
                _get_oauth_token_for_http_request_auth_header(authentication)
        elif authentication['type'] == 'oauth2_token' and not headers:
            headers = {
                'Authorization': _get_oauth_token_for_http_request_auth_header(
                    authentication)}
    return headers
