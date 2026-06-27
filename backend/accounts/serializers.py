from rest_framework import serializers
from .models import User, PlayerProfile, ClubProfile
from django.utils import timezone

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'role', 'birth_date']

    def validate_role(self, value):
        if not value:
            raise serializers.ValidationError('Role is required.')
        return value

    def validate_birth_date(self, value):
        if not value:
            raise serializers.ValidationError('Birth date is required')

        today = timezone.now().date()
        age = (today.year - value.year
               - ((today.month, today.day) < (value.month, value.day)))

        if age < 18:
            raise serializers.ValidationError('Minimum age requirement: 18 years old.')
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()


class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)


class OTPResendSerializer(serializers.Serializer):
    email = serializers.EmailField()


class Toggle2FASerializer(serializers.Serializer):
    enabled = serializers.BooleanField()


class DetailResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()


class OTPLoginResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
    pending_otp = serializers.BooleanField()


class TokenPairSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


class LogoutRequestSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class PlayerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PlayerProfile
        fields = [
            'id', 'first_name', 'last_name', 'gender',
            'position', 'level', 'biography',
            'is_verified',
        ]
        read_only_fields = ['id', 'is_verified']


class ClubProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ClubProfile
        fields = [
            'id', 'club_name', 'president_name', 'foundation_date',
            'city', 'country', 'league', 'district',
            'social_link', 'is_verified',
        ]
        read_only_fields = ['id', 'is_verified']
