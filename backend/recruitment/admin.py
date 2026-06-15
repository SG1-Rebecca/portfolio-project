from django.contrib import admin
from .models import RecruitmentPost, Application


# Register your models here.
@admin.register(RecruitmentPost)
class RecruitmentPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'club', 'position_needed', 'status', 'level_required', 'region', 'application_deadline')
    list_filter = ('status', 'level_required', 'region')
    search_fields = ('title', 'club__user__email', 'position_needed')

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('player', 'post', 'status', 'contact_revealed', 'created_at')
    list_filter = ('status', 'contact_revealed')
    search_fields = ('player__user__email', 'post__title')
    readonly_fields = ('created_at', 'updated_at')
