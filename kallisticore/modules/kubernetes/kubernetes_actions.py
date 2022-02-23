import base64
import os
import re
from pathlib import Path
from typing import Dict, Callable

import boto3
import yaml
from botocore.signers import RequestSigner
from kallisticore.exceptions import FailedAction
from kallisticore.lib.action import Action
from kallisticore.lib.credential import Credential, UsernamePasswordCredential
from kallisticore.lib.credential import KubernetesServiceAccountTokenCredential


class KubernetesAction(Action):
    DEFAULT_CREDENTIAL_TOKEN_PREFIX = 'Bearer'
    PLATFORM_K8S = 'k8s'
    PLATFORM_EKS = 'eks'
    STS_URL_FORMAT = 'https://sts.{}.amazonaws.com/' \
                     '?Action=GetCallerIdentity&Version=2011-06-15'
    STS_TOKEN_EXPIRES_IN = 60

    def __init__(self, module_func: Callable, arguments: Dict,
                 expectations: [], description: str = None,
                 credential: Credential = None):
        super(KubernetesAction, self).__init__(
            module_func=module_func, arguments=arguments,
            expectations=expectations, name=description, credential=credential)

        self.platform = self.arguments.pop('platform',
                                           self.PLATFORM_K8S).lower()

        if self.platform == self.PLATFORM_EKS:
            self.arguments['secrets'] = {
                'KUBERNETES_CONTEXT': self._make_eks_context()}
        elif self.platform == self.PLATFORM_K8S:
            if credential is None:
                credential = self._get_default_credential()
            credential.fetch()
            if isinstance(credential, UsernamePasswordCredential):
                self.arguments['secrets'] = {
                    'KUBERNETES_HOST': self.arguments.pop('k8s_api_host', ''),
                    'KUBERNETES_USERNAME': credential.username,
                    'KUBERNETES_PASSWORD': credential.password
                }
            else:
                self.arguments['secrets'] = {
                    'KUBERNETES_HOST': self.arguments.pop('k8s_api_host', ''),
                    'KUBERNETES_API_KEY': credential.token,
                    'KUBERNETES_API_KEY_PREFIX':
                        self.DEFAULT_CREDENTIAL_TOKEN_PREFIX,
                }
        else:
            raise FailedAction('K8s on the platform: {} is not supported.'
                               .format(self.platform))

    def _get_default_credential(self):
        return KubernetesServiceAccountTokenCredential()

    def _make_eks_context(self) -> str:
        eks_cluster_name = self.arguments.pop('cluster_name')
        region = self.arguments.pop('region', '')
        session = self._create_aws_session(region)
        cluster_info = self._get_eks_cluster_info(session, eks_cluster_name)
        token = self._retrieve_eks_token(session, region, eks_cluster_name)
        self._create_eks_k8s_config(cluster_info, token)
        return cluster_info['cluster']['arn']

    def _create_aws_session(self, region: str = ''):
        aws_session_params = {'region_name': region} if region else {}
        if boto3.DEFAULT_SESSION is None:
            boto3.setup_default_session(**aws_session_params)
        return boto3.session.Session()

    def _get_eks_cluster_info(self, session: boto3.Session, cluster_name):
        eks_client = session.client('eks')
        return eks_client.describe_cluster(name=cluster_name)

    def _retrieve_eks_token(self, session: boto3.Session, region: str,
                            cluster_name: str):
        sts_client = session.client('sts', region_name=region)
        service_id = sts_client.meta.service_model.service_id
        signer = RequestSigner(service_id, region, 'sts', 'v4',
                               session.get_credentials(), session.events)
        params = {
            'method': 'GET',
            'url': self.STS_URL_FORMAT.format(region),
            'body': {},
            'headers': {
                'x-k8s-aws-id': cluster_name
            },
            'context': {}
        }
        signed_url = signer.generate_presigned_url(
            params, region_name=region, expires_in=self.STS_TOKEN_EXPIRES_IN,
            operation_name='')
        base64_url = base64.urlsafe_b64encode(
            signed_url.encode('utf-8')).decode('utf-8')
        return 'k8s-aws-v1.' + re.sub(r'=*', '', base64_url)

    def _create_eks_k8s_config(self, cluster_info: dict, token: str):
        cluster_cert = cluster_info['cluster']['certificateAuthority']['data']
        cluster_endpoint = cluster_info['cluster']['endpoint']
        cluster_arn = cluster_info['cluster']['arn']
        k8s_config = {
            'apiVersion': 'v1',
            'clusters': [
                {
                    'cluster': {
                        'server': cluster_endpoint,
                        'certificate-authority-data': cluster_cert
                    },
                    'name': cluster_arn
                }
            ],
            'contexts': [
                {
                    'context': {
                        'cluster': cluster_arn,
                        'user': cluster_arn
                    },
                    'name': cluster_arn
                }
            ],
            'current-context': cluster_arn,
            'users': [
                {
                    'name': cluster_arn,
                    'user': {
                        'token': token
                    }
                }
            ]
        }
        config_text = yaml.dump(k8s_config, default_flow_style=False)
        k8s_config_dir = os.path.join(str(Path.home()), '.kube')
        Path(k8s_config_dir).mkdir(parents=True, exist_ok=True)
        k8s_config_file = os.path.join(k8s_config_dir, 'config')
        open(k8s_config_file, "w+").write(config_text)
