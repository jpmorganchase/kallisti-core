from django.conf import settings
from rest_framework import viewsets
from rest_framework.decorators import authentication_classes
from rest_framework.response import Response

from kallisticore.models.notification import Notification
from kallisticore.serializers import NotificationSerializer


@authentication_classes((settings.KALLISTI_API_AUTH_CLASS,))
class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.filter(pk=1)
    serializer_class = NotificationSerializer
    permission_classes = (settings.KALLISTI_API_PERMISSION_CLASS,)
    http_method_names = ['get', 'put']

    def get_object(self):
        return self.queryset[0]

    def list(self, request, *args, **kwargs):
        serializer = NotificationSerializer(self.queryset[0])
        return Response(serializer.data)
