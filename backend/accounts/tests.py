import uuid
from datetime import date

from django.test import TestCase

from .models import User, PlayerProfile, ClubProfile
from core.enums import Gender, SkillLevel


# --- Helpers / Factory Functions ---
def create_user(**kwargs):
    defaults = {
        "username": f"user_{uuid.uuid4().hex[:8]}",
        "email": f"{uuid.uuid4().hex[:8]}@example.com",
    }
    defaults.update(kwargs)
    return User.objects.create_user(**defaults)

def create_player(user=None, gender=Gender.MALE, level=SkillLevel.BEGINNER, **kwargs):
    user = user or create_user()
    profile_data = {"user": user, "gender": gender, "level": level}
    profile_data.update(kwargs)
    return PlayerProfile.objects.create(**profile_data)

def create_club(**kwargs):
    club_data = {
        "club_name": "Test FC",
        "president_name": "John Doe",
        "foundation_date": date(2000, 1, 1),
        "city": "Paris",
        "country": "France",
        "league": "National 1",
        "district": "Île-de-France",
        "social_link": "https://testfc.example.com",
    }
    club_data.update(kwargs)
    return ClubProfile.objects.create(**club_data)


class UserTests(TestCase):

    def setUp(self):
        self.user = create_user()

    def test_default_state(self):
        """
        Two-factor authentication should be disabled by default.
        """
        self.assertFalse(self.user.is_2fa_enabled)


    def test_adult_check_logic(self):
        """
        Age calculation to identify minors, adults,
        and users with no birthdate.
        """
        today = date.today()

        minor = create_user(birth_date=today.replace(year=today.year - 17))
        self.assertFalse(minor.is_adult())

        try:
            birth_adult = today.replace(year=today.year - 18)
        except ValueError:
            birth_adult = today.replace(year=today.year - 18, day=28)
        adult = create_user(birth_date=birth_adult)
        self.assertTrue(adult.is_adult())

        no_date = create_user()
        self.assertFalse(no_date.is_adult())

    def test_profile_retrieval(self):
        self.assertIsNone(self.user.get_profile())

        player_profile = create_player(self.user)
        self.assertEqual(self.user.get_profile(), player_profile)


class PlayerProfileTests(TestCase):

    def setUp(self):
        self.user = create_user()

    def test_default_verification_status(self):
        """
        A newly created player profile should not be verified by default.
        """
        player_profile = create_player(self.user)
        self.assertFalse(player_profile.is_verified)


class ClubProfileTests(TestCase):

    def test_default_verification_status(self):
        """
        A newly created club profile should not be verified by default.
        """
        club = create_club()
        self.assertFalse(club.is_verified)
