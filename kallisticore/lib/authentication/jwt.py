import base64
import json
from typing import Optional

import requests
from jose import jwk, jwt
from jose.backends.base import Key
from kallisticore.utils import singleton


class JwtException(Exception):
    def __init__(self, message: str, *args: object) -> None:
        super().__init__(message, *args)
        self.message = message


class PublicKeys(metaclass=singleton.Singleton):
    def __init__(self):
        self.keys = {}

    def add(self, kid: str, key: Key):
        self.keys[kid] = key

    def get(self, kid: str) -> Optional[Key]:
        return self.keys.get(kid, None)

    def kids(self) -> list:
        return list(self.keys)

    def is_empty(self) -> bool:
        return not bool(self.keys)


class JwtHandler:
    def __init__(self, jwk_url: str, audience: str):
        self.public_keys = PublicKeys()
        self.jwk_url = jwk_url
        self.audience = audience

    def decode(self, token: str) -> Optional[dict]:
        token_parts = token.split('.')
        token_header = json.loads(
            base64.b64decode(token_parts[0]).decode('utf-8'))
        kid = token_header.get('kid') or token_header.get('x5t')
        if not kid:
            raise JwtException('kid not found in token header')
        if self.public_keys.is_empty() or kid not in self.public_keys.kids():
            self._retrieve_public_keys()
        if kid not in self.public_keys.kids():
            raise JwtException('jwk for this token was not found')
        public_key = self.public_keys.get(kid)
        return jwt.decode(token, public_key, audience=self.audience,
                          algorithms=token_header.get('alg'))

    def _retrieve_public_keys(self):
        header = {'Accept': 'application/json'}
        response = requests.get(url=self.jwk_url, headers=header)
        if response.status_code == 200:
            key_data = response.json()['keys']
            self._create_public_keys(key_data)

    def _create_public_keys(self, key_data: list):
        for key in key_data:
            if key['kty'] == 'RSA':  # currently only supports RSA
                kid = key.get('kid') or key.get('x5t')
                public_key = jwk.construct(key)
                self.public_keys.add(kid, public_key)
