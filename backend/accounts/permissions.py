from rest_framework.permissions import BasePermission
from core.enums import Role


class IsPlayer(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == Role.PLAYER
        )


class IsClub(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == Role.CLUB
        )
