from unittest import TestCase, mock

from kallisticore.lib.action import Action, FunctionLoader
from kallisticore.models.step import Step
from kallisticore.modules.prometheus import PrometheusAction


class TestPrometheusAction(TestCase):
    module_map = {'prom': 'kallisticore.modules.prometheus'}

    def setUp(self):
        self.arguments = {
            'base_url': 'http://prometheus.test',
            'query': 'test-query',
            'when': '5 minutes ago'
        }
        self.action_spec = {"step": "Test Prometheus Action",
                            "do": "prom.query",
                            "where": self.arguments}
        self.step = Step.build(self.action_spec)

    def test_initialization(self):
        action = PrometheusAction.build(self.step, self.module_map, {})
        expected_func = FunctionLoader(self.module_map, 'prom') \
            .get_function('query')
        self.assertIsInstance(action, PrometheusAction)
        self.assertIsInstance(action, Action)
        self.assertEqual('Test Prometheus Action', action.name)
        self.assertEqual(expected_func, action.func)
        self.assertEqual(self.arguments['query'], action.arguments['query'])
        self.assertEqual(self.arguments['when'], action.arguments['when'])
        self.assertEqual({'prometheus_base_url': 'http://prometheus.test'},
                         action.arguments['configuration'])
        self.assertEqual(None, action.credential)

    def test_execute(self):
        with mock.patch('chaosprometheus.probes.query') as mock_prom_query:
            mock_query_return_value = 'test query return value'
            mock_prom_query.return_value = mock_query_return_value
            action = PrometheusAction.build(self.step, self.module_map, {})
            result = action.execute()

        self.assertEqual(mock_query_return_value, result)
        mock_prom_query.assert_called_once_with(
            query='test-query', when='5 minutes ago',
            configuration={'prometheus_base_url': 'http://prometheus.test'})
