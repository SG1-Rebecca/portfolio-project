from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRFValidationError
from .models import RecruitmentPost, Application
from core.enums import ApplicationStatus


class RecruitmentPostSerializer(serializers.ModelSerializer):
    club_name = serializers.CharField(source='club.club_name', read_only=True)

    class Meta:
        model  = RecruitmentPost
        fields = [
            'id', 'club_name', 'title', 'status', 'category',
            'position_needed', 'level_required', 'region',
            'description', 'application_deadline',
        ]
        read_only_fields = ['id', 'club_name']


class ApplicationSerializer(serializers.ModelSerializer):
    player_email = serializers.EmailField(source='player.user.email', read_only=True)
    # Contact revealed only when club accepts
    contact = serializers.SerializerMethodField()

    class Meta:
        model  = Application
        fields = [
            'id', 'post', 'player_email', 'player_message',
            'status', 'contact_revealed', 'contact',
        ]
        read_only_fields = ['id', 'status', 'contact_revealed', 'contact']

    @extend_schema_field(OpenApiTypes.EMAIL)
    def get_contact(self, obj) -> str | None:
        if not obj.contact_revealed:
            return None
        return obj.player.user.email


    def create(self, validated_data):
        instance = Application(**validated_data)
        try:
            instance.full_clean()
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict)
        instance.save()
        return instance

class ApplicationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Application
        fields = ['status']
