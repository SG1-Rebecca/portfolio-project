from rest_framework import generics, status
from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema

from .models import User, PlayerProfile, ClubProfile
from .serializers import (
    RegisterSerializer, LoginSerializer, OTPVerifySerializer,
    OTPResendSerializer, Toggle2FASerializer,
    PlayerProfileSerializer, ClubProfileSerializer,
    DetailResponseSerializer, OTPLoginResponseSerializer,
    TokenPairSerializer, LogoutRequestSerializer,
)
from .permissions import IsPlayer, IsClub
from .utils import generate_otp, verify_otp, send_otp_email


# Auth

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=LoginSerializer, responses={200: OTPLoginResponseSerializer})
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'detail': 'No account found with this email.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        otp = generate_otp(user)
        send_otp_email(user, otp)
        return Response({'detail': 'OTP sent.', 'pending_otp': True})


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=OTPVerifySerializer, responses={200: TokenPairSerializer})
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp   = serializer.validated_data['otp']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_400_BAD_REQUEST)

        if not verify_otp(user, otp):
            return Response({'detail': 'Invalid or expired OTP.'}, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = True
        user.save(update_fields=['is_active'])
        refresh = RefreshToken.for_user(user)
        return Response({
            'access' : str(refresh.access_token),
            'refresh': str(refresh),
        })


class ResendOTPView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=OTPResendSerializer, responses={200: DetailResponseSerializer})
    def post(self, request):
        serializer = OTPResendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'detail': 'No account found with this email.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        otp = generate_otp(user)
        send_otp_email(user, otp)
        return Response({'detail': 'OTP resent.'})


class Toggle2FAView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=Toggle2FASerializer, responses={200: DetailResponseSerializer})
    def post(self, request):
        serializer = Toggle2FASerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.is_2fa_enabled = serializer.validated_data['enabled']
        request.user.save(update_fields=['is_2fa_enabled'])
        state = 'enabled' if request.user.is_2fa_enabled else 'disabled'
        return Response({'detail': f'2FA {state}.'})


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=LogoutRequestSerializer, responses={204: None})
    def post(self, request):
        try:
            RefreshToken(request.data['refresh']).blacklist()
        except Exception:
            pass  # token already invalid or missing — silent
        return Response(status=status.HTTP_204_NO_CONTENT)


# Profiles

class PlayerProfileView(GenericAPIView):
    permission_classes = [IsPlayer]
    serializer_class = PlayerProfileSerializer

    def get(self, request):
        profile = PlayerProfile.objects.filter(user=request.user).first()
        if not profile:
            return Response({'detail': 'Profile not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(self.get_serializer(profile).data)

    def put(self, request):
        profile, _ = PlayerProfile.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ClubProfileView(GenericAPIView):
    permission_classes = [IsClub]
    serializer_class = ClubProfileSerializer

    def get(self, request):
        profile = ClubProfile.objects.filter(user=request.user).first()
        if not profile:
            return Response({'detail': 'Profile not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(self.get_serializer(profile).data)

    def put(self, request):
        profile, _ = ClubProfile.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
