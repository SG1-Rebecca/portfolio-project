from django.http import Http404
from rest_framework import generics, status
from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from drf_spectacular.utils import extend_schema

from core.enums import Role
from .models import User, PlayerProfile, ClubProfile
from .serializers import (
    RegisterSerializer, LoginSerializer, OTPVerifySerializer,
    OTPResendSerializer, Toggle2FASerializer,
    PlayerProfileSerializer, ClubProfileSerializer,
    DetailResponseSerializer, OTPLoginResponseSerializer,
    TokenPairSerializer, LogoutRequestSerializer, ClubPublicProfileSerializer
)
from .permissions import IsPlayer, IsClub, HasCompletedProfile
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
            'has_profile': user.get_profile() is not None
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
        refresh_token = request.data.get('refresh')
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except TokenError:
                pass
            except Exception:
                pass
        return Response(status=status.HTTP_204_NO_CONTENT)


# Profiles

class PlayerProfileView(GenericAPIView):
    permission_classes = [IsAuthenticated, IsPlayer]
    serializer_class = PlayerProfileSerializer

    def get(self, request):
        profile = PlayerProfile.objects.filter(user=request.user).first()
        if not profile:
            return Response({'detail': 'Profile not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(self.get_serializer(profile).data)

    def put(self, request):
        # Récupère le profil s'il existe, sinon renvoie une nouvelle instance vide liée à l'user
        profile, _ = PlayerProfile.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ClubProfileView(GenericAPIView):
    permission_classes = [IsAuthenticated, IsClub]
    serializer_class = ClubProfileSerializer

    def get_object(self):
        return ClubProfile.objects.get(user=self.request.user)

    def get(self, request):
        try:
            profile = self.get_object()
            return Response(self.get_serializer(profile).data)
        except ClubProfile.DoesNotExist:
            return Response({'detail': 'Profile not found.'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request):
        try:
            profile = ClubProfile.objects.get(user=request.user)
            created = False
        except ClubProfile.DoesNotExist:
            profile = None
            created = True

        if created:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            profile = serializer.save(user=request.user)
        else:
            serializer = self.get_serializer(profile, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

        return Response(serializer.data)


class ClubPublicProfileView(generics.RetrieveAPIView):
    serializer_class = ClubPublicProfileSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        try:
            return ClubProfile.objects.select_related('user').get(
                user__id=self.kwargs['user_id'],
                user__role=Role.CLUB
            )
        except ClubProfile.DoesNotExist:
            raise Http404("Club profile not found")

class ClubListView(generics.ListAPIView):
    queryset = ClubProfile.objects.select_related('user').all()
    serializer_class = ClubProfileSerializer
    permission_classes = [AllowAny]
