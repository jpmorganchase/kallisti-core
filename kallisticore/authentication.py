from typing import Optional, Dict, Any

from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings

from kallisticore.lib.authentication.jwt import JwtHandler


class KallistiUser(dict):
    def __init__(self, user_id: str, domain: Optional[str] = None,
                 claims: Optional[Dict] = None, **kwargs: Any):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.domain = domain
        self.claims = claims

    def __getitem__(self, key):
        return self.__dict__.__getitem__(key)

    def __setitem__(self, key, val):
        self.__dict__.__setitem__(key, val)

    def __repr__(self):
        return '%s(%s)' % (type(self).__name__, (self.__dict__.__repr__()))

    def get_claim(self, claim_key):
        return self.claims.get(claim_key, None)


class DefaultAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        if getattr(settings, 'KALLISTI_AUTH_JWT_TOKEN_URL', None):
            return ExternalJWTAuthentication().authenticate(request)
        else:
            return KallistiUser('anonymous_user'), None


class ExternalJWTAuthentication(authentication.BaseAuthentication):
    CLAIM_USER_ID_KEY = getattr(settings, 'KALLISTI_CLAIM_USER_ID_KEY', 'sub')

    def __init__(self):
        self.user = None

    def authenticate(self, request):
        token = request.META.get('HTTP_AUTHORIZATION')
        if not token:
            raise AuthenticationFailed('No authorization token found.')
        token_parts = token.split(' ')
        if len(token_parts) != 2 or token_parts[0] != 'Bearer':
            raise AuthenticationFailed("Invalid user token.")
        access_token = token_parts[1]

        try:
            claims = JwtHandler(settings.KALLISTI_AUTH_JWKS_URL,
                                settings.KALLISTI_AUTH_JWT_AUDIENCE)\
                .decode(access_token)
        except Exception as e:
            raise AuthenticationFailed(str(e))
        if claims:
            user_id = claims.get(self.CLAIM_USER_ID_KEY, None)
            self.user = KallistiUser(user_id=user_id, claims=claims)
            return self.user, None
        raise AuthenticationFailed('Cannot check user token.')
