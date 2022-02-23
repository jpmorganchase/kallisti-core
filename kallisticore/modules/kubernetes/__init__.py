from kallisticore.modules.kubernetes.kubernetes_actions import KubernetesAction

__action_class__ = KubernetesAction

__actions_modules__ = ['chaosk8s.actions',
                       'chaosk8s.probes',
                       'chaosk8s.crd.actions',
                       'chaosk8s.crd.probes',
                       'chaosk8s.deployment.actions',
                       'chaosk8s.deployment.probes',
                       'chaosk8s.node.actions',
                       'chaosk8s.node.probes',
                       'chaosk8s.pod.actions',
                       'chaosk8s.pod.probes',
                       'chaosk8s.replicaset.actions',
                       'chaosk8s.service.actions',
                       'chaosk8s.service.probes',
                       'chaosk8s.statefulset.actions',
                       'chaosk8s.statefulset.probes',
                       'chaosistio.fault.actions',
                       'chaosistio.fault.probes']
