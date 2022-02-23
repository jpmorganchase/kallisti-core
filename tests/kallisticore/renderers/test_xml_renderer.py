from unittest import mock

from django.test import TestCase
from kallisticore.renderers import XMLRenderer


class MockTemplateSource:
    source = '<?xsl_template?>'


class TestXMLRenderer(TestCase):

    @mock.patch('kallisticore.renderers.XMLRenderer.XML_HEADER',
                '<?xml_header?>')
    @mock.patch('kallisticore.renderers.XMLRenderer.XSL_HEADER',
                '<?xsl_header?>')
    @mock.patch('kallisticore.renderers.XMLRenderer.XSL_TEMPLATE',
                MockTemplateSource)
    def test_render_with_dict_data(self):
        xml_renderer = XMLRenderer()
        data = {'mock_key': 'mock_value'}
        xml_response = xml_renderer.render(data=data)
        self.assertEqual(xml_response,
                         '<?xml_header?><?xsl_header?><report>\n'
                         '<?xsl_template?><root>'
                         '<mock_key>mock_value</mock_key>'
                         '</root></report>\n')

    @mock.patch('kallisticore.renderers.XMLRenderer.XML_HEADER',
                '<?xml_header?>')
    @mock.patch('kallisticore.renderers.XMLRenderer.XSL_HEADER',
                '<?xsl_header?>')
    @mock.patch('kallisticore.renderers.XMLRenderer.XSL_TEMPLATE',
                MockTemplateSource)
    def test_render_with_list_data(self):
        xml_renderer = XMLRenderer()
        data = ['mock_item_1', 'mock_item_2']
        xml_response = xml_renderer.render(data=data)
        self.assertEqual(xml_response,
                         '<?xml_header?><?xsl_header?><report>\n'
                         '<?xsl_template?><root>'
                         '<list-item>mock_item_1</list-item>'
                         '<list-item>mock_item_2</list-item>'
                         '</root></report>\n')
