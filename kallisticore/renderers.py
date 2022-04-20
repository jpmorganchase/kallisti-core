from __future__ import unicode_literals

from django.conf import settings
from django.template import loader
from django.utils import six
from django.utils.encoding import force_text
from django.utils.six import StringIO
from django.utils.xmlutils import SimplerXMLGenerator
from rest_framework.renderers import BaseRenderer


class XMLRenderer(BaseRenderer):
    """
    Renderer which serializes to XML.
    """
    media_type = 'application/xml'
    format = 'xml'
    charset = 'utf-8'
    ITEM_TAG_NAME = 'list-item'
    ROOT_TAG_NAME = 'root'
    TITLE_TAG_NAME = 'report-title'
    XML_HEADER = '<?xml version="1.0" encoding="utf-8"?>\n'
    XSL_HEADER = '<?xml-stylesheet type="text/xsl" href="#reportstyle"?>' \
                 '<!DOCTYPE report ' \
                 '[<!ATTLIST xsl:stylesheet id    ID  #REQUIRED>]>'
    XSL_TEMPLATE = loader.get_template(
        'kallisticore/xsl_template.xml').template

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Renders `data` into serialized XML.
        """
        if data is None:
            return ''

        stream = StringIO()
        xml = SimplerXMLGenerator(stream, self.charset)
        self._append_title(xml)
        self._append_data(xml, data)
        xml.endDocument()
        return self.XML_HEADER + self.XSL_HEADER + '<report>\n' \
            + self.XSL_TEMPLATE.source + stream.getvalue() + '</report>\n'

    def _append_title(self, xml):
        xml.startElement(self.TITLE_TAG_NAME, {})
        xml.characters(settings.KALLISTI_REPORT_HEADER_TITLE)
        xml.endElement(self.TITLE_TAG_NAME)

    def _append_data(self, xml, data):
        xml.startElement(self.ROOT_TAG_NAME, {})
        self._to_xml(xml, data)
        xml.endElement(self.ROOT_TAG_NAME)

    def _to_xml(self, xml, data):
        if isinstance(data, (list, tuple)):
            for item in data:
                xml.startElement(self.ITEM_TAG_NAME, {})
                self._to_xml(xml, item)
                xml.endElement(self.ITEM_TAG_NAME)

        elif isinstance(data, dict):
            for key, value in six.iteritems(data):
                xml.startElement(key, {})
                self._to_xml(xml, value)
                xml.endElement(key)

        elif data is None:
            # Don't output any value
            pass

        else:
            xml.characters(force_text(data))
