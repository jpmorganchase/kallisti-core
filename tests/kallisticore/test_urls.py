from django.test import TestCase
from django.urls import reverse


class TestUrls(TestCase):

    def test_report(self):
        self.assertEqual("/api/v1/report", reverse("report"))
