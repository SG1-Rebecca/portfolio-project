from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, PlayerProfile, ClubProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin interface for the User model
    """
    list_display = ('email', 'role', 'is_staff', 'is_active', 'created_at')
    list_filter = ('role', 'is_staff', 'is_active')

    search_fields = ('email',)
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )
    readonly_fields = ('created_at', 'updated_at')

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'birth_date', 'password1', 'password2'),
        }),
    )


@admin.register(PlayerProfile)
class PlayerProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for the PlayerProfile model
    """
    list_display = ('first_name', 'last_name', 'user', 'gender', 'position', 'level', 'is_verified')
    list_filter = ('gender', 'position', 'level', 'is_verified')
    search_fields = ('first_name', 'last_name', 'user__email')


@admin.register(ClubProfile)
class ClubProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for the ClubProfile model
    """
    list_display = ('club_name', 'city', 'country', 'league', 'is_verified')
    list_filter = ('city', 'country', 'league', 'is_verified')
    search_fields = ('club_name', 'user__email')