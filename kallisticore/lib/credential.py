import abc
import importlib
import logging
import os
from abc import abstractmethod
from copy import deepcopy
from typing import Dict

from kallisticore.exceptions import InvalidCredentialType


class Credential(metaclass=abc.ABCMeta):
    logger = logging.getLogger(__name__)

    def __init__(self) -> None:
        self.source = self.__class__.__name__

    @classmethod
    def build(cls, class_map: Dict, cred_dict: Dict) -> 'Credential':
        if 'type' not in cred_dict or cred_dict['type'] not in \
                class_map.keys():
            raise InvalidCredentialType(cred_dict.get('type'))

        full_path = class_map[cred_dict['type']]
        classname = full_path.split('.')[-1]
        module_path = '.'.join(full_path.split('.')[:-1])
        module = importlib.import_module(module_path)
        klass = getattr(module, classname)

        args = deepcopy(cred_dict)
        args.pop('type')
        return klass(**args)

    @abstractmethod
    def fetch(self):
        raise NotImplementedError


class TokenCredential(Credential):
    _token = None

    @property
    def token(self):
        return self._token


class UsernamePasswordCredential(Credential):
    _username = None
    _password = None

    @property
    def username(self):
        return self._username

    @property
    def password(self):
        return self._password


class EnvironmentUserNamePasswordCredential(UsernamePasswordCredential):
    def __init__(self, username_key: str, password_key: str):
        super().__init__()
        self.logger.info(
            "Retrieving credentials for username_key: {}, "
            "password_key: {} ".format(username_key, password_key))

        self.username_key = username_key
        self.password_key = password_key

    def fetch(self):
        self._username = os.environ.get(self.username_key)
        self._password = os.environ.get(self.password_key)


class TokenFileCredential(TokenCredential):
    def __init__(self, token_path: str):
        super().__init__()
        self.token_path = token_path

    def fetch(self):
        with open(self.token_path) as token_fd:
            token = token_fd.read()
        self._token = token


class KubernetesServiceAccountTokenCredential(TokenFileCredential):
    def __init__(self):
        super().__init__('/var/run/secrets/kubernetes.io/serviceaccount/token')
