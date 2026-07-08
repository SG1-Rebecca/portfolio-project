# accounts/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Auth
    path('auth/register/', views.RegisterView.as_view()),
    path('auth/login/', views.LoginView.as_view()),
    path('auth/verify-otp/', views.VerifyOTPView.as_view()),
    path('auth/resend-otp/', views.ResendOTPView.as_view()),
    path('auth/toggle-2fa/', views.Toggle2FAView.as_view()),
    path('auth/logout/', views.LogoutView.as_view()),
    path('auth/token/refresh/', TokenRefreshView.as_view()),

    # Profiles
    path('profiles/player/', views.PlayerProfileView.as_view()),
    path('profiles/club/', views.ClubProfileView.as_view()),

    # Public clubs
    path('clubs/', views.ClubListView.as_view(), name='club_list',),
    path('clubs/<uuid:user_id>/', views.ClubPublicProfileView.as_view(), name='club-detail',),
]
