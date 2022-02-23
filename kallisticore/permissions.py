from rest_framework.permissions import BasePermission


class DefaultUserPermission(BasePermission):
    def has_permission(self, request, view):
        return True
