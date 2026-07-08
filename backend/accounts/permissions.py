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


class HasCompletedProfile(BasePermission):
    message = "You must complete your profile before accessing this resource."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if not user.role:
            return False

        if user.role == Role.PLAYER:
            return hasattr(user, 'playerprofile')
        elif user.role == Role.CLUB:
            return hasattr(user, 'clubprofile')

        return False


class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True

        return request.user.is_authenticated and obj.club.user == request.user
