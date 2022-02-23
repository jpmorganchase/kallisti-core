import base64
import json
from unittest import mock

import requests_mock
from django.test import TestCase
from kallisticore.lib.authentication.jwt import JwtHandler, JwtException


class TestJwt(TestCase):
    """
    JwtHandler uses singleton, so PublicKeys won't be refreshed unless
    it's cleared explicitly throughout the test.
    """

    @mock.patch('kallisticore.lib.authentication.jwt.jwt.decode')
    @mock.patch('kallisticore.lib.authentication.jwt.jwk.construct')
    @requests_mock.mock()
    def test_decode(self, mock_jwk_construct, decode_mock, req_mock):
        mock_jwk_construct.return_value = mock.Mock()
        mock_claim = {'test-claim-key': 'test-claim-value'}
        decode_mock.return_value = mock_claim
        mock_jwks = {'keys': [
            {
                'kty': 'RSA',
                'use': 'sig',
                'alg': 'RS256',
                'kid': 'test-kid'
            }
        ]}
        mock_jwk_url = 'https://test-iss'
        req_mock.get(mock_jwk_url, text=json.dumps(mock_jwks))
        token_header = base64.b64encode(
            json.dumps({'kid': 'test-kid'}).encode()).decode('utf-8')
        token_body = base64.b64encode(
            json.dumps({'iss': 'https://test-iss'}).encode()).decode('utf-8')
        token_sig = 'test-sig'
        res = JwtHandler(mock_jwk_url, '').decode(
            '.'.join([token_header, token_body, token_sig]))
        self.assertEqual(mock_claim, res)

    @mock.patch('kallisticore.lib.authentication.jwt.jwk.construct')
    @requests_mock.mock()
    def test_no_kid_match(self, mock_jwk_construct, req_mock):
        mock_jwk_construct.return_value = mock.Mock()
        mock_jwks = {'keys': [
            {
                'kty': 'RSA',
                'use': 'sig',
                'alg': 'RS256',
                'kid': 'non-matching-kid'
            }
        ]}
        req_mock.get('https://test-iss', text=json.dumps(mock_jwks))
        token_header = base64.b64encode(
            json.dumps({'kid': 'test-kid-2'}).encode()).decode('utf-8')
        token_body = base64.b64encode(
            json.dumps({'iss': 'https://test-iss'}).encode()).decode('utf-8')
        token_sig = 'test-sig'
        with self.assertRaises(JwtException) as exc_context:
            JwtHandler('https://test-iss', '').decode(
                '.'.join([token_header, token_body, token_sig]))
        self.assertEqual('jwk for this token was not found',
                         str(exc_context.exception))
