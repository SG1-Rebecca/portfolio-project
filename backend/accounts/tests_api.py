import uuid
from datetime import date
from unittest.mock import patch

from django.test import TestCase

from rest_framework_simplejwt.tokens import RefreshToken as RealRefreshToken
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from .models import User, PlayerProfile, ClubProfile
from .views import (
    RegisterView,
    LoginView,
    VerifyOTPView,
    ResendOTPView,
    Toggle2FAView,
    LogoutView,
    PlayerProfileView,
    ClubProfileView,
    ClubPublicProfileView,
    ClubListView,
)
from core.enums import Gender, SkillLevel, PlayerPosition, Role

# Helpers

factory = APIRequestFactory()


def make_email():
    return f"{uuid.uuid4().hex[:8]}@test.com"


def create_user(role=Role.PLAYER, is_active=True, **kwargs):
    defaults = {
        "email": make_email(),
        "birth_date": date(1995, 1, 1),
        "role": role,
        "is_active": is_active,
    }
    defaults.update(kwargs)
    user = User.objects.create_user(password="StrongPass123!", **defaults)
    return user


def create_player_profile(user=None, **kwargs):
    user = user or create_user(role=Role.PLAYER)
    defaults = {
        "user": user,
        "first_name": "Bob",
        "last_name": "Player",
        "gender": Gender.MALE,
        "level": SkillLevel.BEGINNER,
        "position": PlayerPosition.FORWARD,
    }
    defaults.update(kwargs)
    return PlayerProfile.objects.create(**defaults)


def create_club_profile(user=None, **kwargs):
    user = user or create_user(role=Role.CLUB)
    defaults = {
        "user": user,
        "club_name": "Test FC",
        "president_name": "Jane Doe",
        "foundation_date": date(2000, 1, 1),
        "city": "Lyon",
        "country": "France",
        "league": "National",
        "district": "Rhône",
    }
    defaults.update(kwargs)
    return ClubProfile.objects.create(**defaults)


# RegisterView

class RegisterViewTests(TestCase):

    def _post(self, data):
        request = factory.post("/auth/register/", data, format="json")
        return RegisterView.as_view()(request)

    def test_register_player(self):
        data = {
            "email": make_email(),
            "password": "StrongPass123!",
            "birth_date": "1995-06-15",
            "role": Role.PLAYER,
        }
        response = self._post(data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_register_club(self):
        data = {
            "email": make_email(),
            "password": "StrongPass123!",
            "birth_date": "1990-03-20",
            "role": Role.CLUB,
        }
        response = self._post(data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_register_duplicate_email(self):
        email = make_email()
        create_user(email=email)
        data = {
            "email": email,
            "birth_date": "1995-06-15",
            "role": Role.PLAYER,
        }
        response = self._post(data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_minor(self):
        data = {
            "email": make_email(),
            "birth_date": date.today().replace(year=date.today().year - 16).isoformat(),
            "role": Role.PLAYER,
        }
        response = self._post(data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_email(self):
        data = {
            "birth_date": "1995-06-15",
            "role": Role.PLAYER,
        }
        response = self._post(data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_new_user_is_inactive_by_default(self):
        """Un nouveau compte doit être inactif jusqu'à validation OTP."""
        email = make_email()
        self._post({
            "email": email,
            "birth_date": "1995-06-15",
            "role": Role.PLAYER,
        })
        user = User.objects.get(email=email)
        self.assertFalse(user.is_active)


# LoginView

class LoginViewTests(TestCase):

    def _post(self, data):
        request = factory.post("/auth/login/", data, format="json")
        return LoginView.as_view()(request)

    @patch("accounts.views.send_otp_email")
    @patch("accounts.views.generate_otp", return_value="123456")
    def test_login_existing_user_sends_otp(self, mock_otp, mock_email):
        user = create_user()
        response = self._post({"email": user.email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("pending_otp"))
        mock_otp.assert_called_once_with(user)
        mock_email.assert_called_once_with(user, "123456")

    def test_login_unknown_email_returns_404(self):
        response = self._post({"email": "nobody@test.com"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_login_missing_email_returns_400(self):
        response = self._post({})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# VerifyOTPView

class VerifyOTPViewTests(TestCase):

    def _post(self, data):
        request = factory.post("/auth/verify-otp/", data, format="json")
        return VerifyOTPView.as_view()(request)

    @patch("accounts.views.verify_otp", return_value=True)
    def test_valid_otp_returns_token_pair_and_profile_status(self, _):
        user = create_user(is_active=False)
        response = self._post({"email": user.email, "otp": "123456"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("has_profile", response.data)
        self.assertFalse(response.data["has_profile"])  # Pas encore de profil

    @patch("accounts.views.verify_otp", return_value=True)
    def test_valid_otp_reflects_existing_profile(self, _):
        user = create_user(is_active=False, role=Role.PLAYER)
        create_player_profile(user=user)

        response = self._post({"email": user.email, "otp": "123456"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["has_profile"]) # Existing profile detected

    @patch("accounts.views.verify_otp", return_value=True)
    def test_valid_otp_activates_user(self, _):
        user = create_user(is_active=False)
        self._post({"email": user.email, "otp": "123456"})
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    @patch("accounts.views.verify_otp", return_value=False)
    def test_invalid_otp_returns_400(self, _):
        user = create_user(is_active=False)
        response = self._post({"email": user.email, "otp": "000000"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)

    def test_unknown_email_returns_400(self):
        response = self._post({"email": "ghost@test.com", "otp": "123456"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_fields_returns_400(self):
        response = self._post({"email": make_email()})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ResendOTPView

class ResendOTPViewTests(TestCase):

    def _post(self, data):
        request = factory.post("/auth/resend-otp/", data, format="json")
        return ResendOTPView.as_view()(request)

    @patch("accounts.views.send_otp_email")
    @patch("accounts.views.generate_otp", return_value="654321")
    def test_resend_otp_known_email(self, mock_otp, mock_email):
        user = create_user(is_active=False)
        response = self._post({"email": user.email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_email.assert_called_once_with(user, "654321")

    def test_resend_otp_unknown_email_returns_404(self):
        response = self._post({"email": "nobody@test.com"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_resend_otp_missing_email_returns_400(self):
        response = self._post({})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# Toggle2FAView

class Toggle2FAViewTests(TestCase):

    def _post(self, user, data):
        request = factory.post("/auth/2fa/", data, format="json")
        force_authenticate(request, user=user)
        return Toggle2FAView.as_view()(request)

    def test_enable_2fa(self):
        user = create_user()
        response = self._post(user, {"enabled": True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.is_2fa_enabled)

    def test_disable_2fa(self):
        user = create_user()
        user.is_2fa_enabled = True
        user.save()
        response = self._post(user, {"enabled": False})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertFalse(user.is_2fa_enabled)

    def test_toggle_2fa_unauthenticated_returns_401(self):
        request = factory.post("/auth/2fa/", {"enabled": True}, format="json")
        response = Toggle2FAView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_toggle_2fa_missing_field_returns_400(self):
        user = create_user()
        response = self._post(user, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# LogoutView

class LogoutViewTests(TestCase):

    def _post(self, user, data):
        request = factory.post("/auth/logout/", data, format="json")
        force_authenticate(request, user=user)
        return LogoutView.as_view()(request)

    def test_logout_with_valid_token_returns_204(self):
        user = create_user()
        real_token = RealRefreshToken.for_user(user)

        with patch.object(RealRefreshToken, 'blacklist', return_value=None):
            response = self._post(user, {"refresh": str(real_token)})

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_logout_with_invalid_token_still_returns_204(self):
        user = create_user()
        response = self._post(user, {"refresh": "bad.token.format"})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_logout_unauthenticated_returns_401(self):
        request = factory.post("/auth/logout/", {"refresh": "token"}, format="json")
        response = LogoutView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# PlayerProfileView

class PlayerProfileViewTests(TestCase):

    def setUp(self):
        self.user = create_user(role=Role.PLAYER)
        self.profile = create_player_profile(user=self.user)

    def _get(self, user):
        request = factory.get("/accounts/profile/player/")
        force_authenticate(request, user=user)
        return PlayerProfileView.as_view()(request)

    def _put(self, user, data):
        request = factory.put("/accounts/profile/player/", data, format="json")
        force_authenticate(request, user=user)
        return PlayerProfileView.as_view()(request)

    def test_get_own_profile_returns_200(self):
        response = self._get(self.user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"], "Bob")

    def test_get_profile_not_found_returns_404(self):
        user_no_profile = create_user(role=Role.PLAYER)
        response = self._get(user_no_profile)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_updates_profile(self):
        response = self._put(self.user, {"first_name": "Updated", "last_name": "Name"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.first_name, "Updated")

    def test_put_creates_profile_if_missing(self):
        user_no_profile = create_user(role=Role.PLAYER)
        response = self._put(user_no_profile, {
            "first_name": "New",
            "last_name": "Player",
            "gender": Gender.MALE,
            "level": SkillLevel.BEGINNER,
            "position": PlayerPosition.FORWARD,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(PlayerProfile.objects.filter(user=user_no_profile).exists())

    def test_club_user_cannot_access_player_profile(self):
        club_user = create_user(role=Role.CLUB)
        response = self._get(club_user)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ClubProfileView

class ClubProfileViewTests(TestCase):

    def setUp(self):
        self.user = create_user(role=Role.CLUB)
        self.profile = create_club_profile(user=self.user)

    def _get(self, user):
        request = factory.get("/accounts/profile/club/")
        force_authenticate(request, user=user)
        return ClubProfileView.as_view()(request)

    def _put(self, user, data):
        request = factory.put("/accounts/profile/club/", data, format="json")
        force_authenticate(request, user=user)
        return ClubProfileView.as_view()(request)

    def test_get_own_profile(self):
        response = self._get(self.user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["club_name"], "Test FC")

    def test_get_profile_not_found(self):
        user_no_profile = create_user(role=Role.CLUB)
        response = self._get(user_no_profile)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_updates_club_name(self):
        response = self._put(self.user, {"club_name": "Elite FC"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.club_name, "Elite FC")

    def test_put_creates_profile_if_missing(self):
        user_no_profile = create_user(role=Role.CLUB)
        response = self._put(user_no_profile, {
            "club_name": "New Club",
            "president_name": "John Smith",
            "foundation_date": date(2005, 1, 1),
            "city": "Paris",
            "country": "France",
            "league": "Régional",
            "district": "Île-de-France",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(ClubProfile.objects.filter(user=user_no_profile).exists())

    def test_player_user_cannot_access_club_profile(self):
        player_user = create_user(role=Role.PLAYER)
        response = self._get(player_user)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# Public Club Views (Public Endpoints)

class ClubPublicProfileViewTests(TestCase):

    def setUp(self):
        self.club_user = create_user(role=Role.CLUB)
        self.profile = create_club_profile(user=self.club_user)

    def test_retrieve_public_profile(self):
        request = factory.get(f"/clubs/{self.club_user.id}/")
        response = ClubPublicProfileView.as_view()(request, user_id=self.club_user.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["club_name"], self.profile.club_name)

        self.assertEqual(str(response.data["user_id"]), str(self.club_user.id))

    def test_retrieve_public_profile_fails_for_player_uuid(self):
        player_user = create_user(role=Role.PLAYER)
        request = factory.get(f"/clubs/{player_user.id}/")
        response = ClubPublicProfileView.as_view()(request, user_id=player_user.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ClubListViewTests(TestCase):

    def setUp(self):
        self.club_user1 = create_user(role=Role.CLUB)
        create_club_profile(user=self.club_user1, club_name="Club A")
        self.club_user2 = create_user(role=Role.CLUB)
        create_club_profile(user=self.club_user2, club_name="Club B")

    def test_list_clubs(self):
        request = factory.get("/clubs/")
        response = ClubListView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
