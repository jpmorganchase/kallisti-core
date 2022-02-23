from typing import Dict, Callable

from kallisticore.lib import credential as cred
from kallisticore.lib.action import Action
from kallisticore.lib.credential import Credential
from kallisticore.lib.expectation import Expectation


class CloudFoundryAction(Action):
    CF_DEFAULT_USERNAME_KEY = "CF_USERNAME"
    CF_DEFAULT_PASSWORD_KEY = "CF_PASSWORD"

    def __init__(self, module_func: Callable, arguments: Dict,
                 expectations: [Expectation] = None, name: str = None,
                 credential: Credential = None):
        super(CloudFoundryAction, self).__init__(
            module_func=module_func, arguments=arguments,
            expectations=expectations, name=name, credential=credential)

        pool_url = self.arguments.pop('cf_api_url')
        if credential is None:
            credential = self._get_default_credentials_for_environment()
        credential.fetch()
        assert isinstance(credential, cred.UsernamePasswordCredential)

        self.arguments['secrets'] = {
            'cf_client_id': self.arguments.pop('client_id', 'cf'),
            'cf_client_secret': self.arguments.pop('client_secret', ''),
            'cf_username': credential.username,
            'cf_password': credential.password}
        self.arguments['configuration'] = {'cf_verify_ssl': True,
                                           'cf_api_url': pool_url}

    def _get_default_credentials_for_environment(self) -> Credential:
        return cred.EnvironmentUserNamePasswordCredential(
            username_key=self.CF_DEFAULT_USERNAME_KEY,
            password_key=self.CF_DEFAULT_PASSWORD_KEY)
