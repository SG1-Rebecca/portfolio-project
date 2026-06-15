from django.contrib import admin
from .models import User, PlayerProfile, ClubProfile


# Register your models here.
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')

@admin.register(PlayerProfile)
class PlayerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'gender', 'level')
    list_filter = ('gender', 'level')
    search_fields = ('user__username', 'user__email')


@admin.register(ClubProfile)
class ClubProfileAdmin(admin.ModelAdmin):
    list_display = ('club_name', 'is_verified')
    list_filter = ('city', 'is_verified')
    search_fields = ('club_name', 'user__email')

