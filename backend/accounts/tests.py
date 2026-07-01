import uuid
from datetime import date, timedelta

from django.test import TestCase
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError

from .models import User, PlayerProfile, ClubProfile
from core.enums import Gender, SkillLevel, PlayerPosition


# --- Helpers / Factory Functions ---
def create_user(**kwargs):
    defaults = {
        "email": f"{uuid.uuid4().hex[:8]}@example.com",
        "birth_date": date(2000, 1, 1),
    }
    defaults.update(kwargs)
    return User.objects.create_user(**defaults)


def create_player(user=None, gender=Gender.MALE, level=SkillLevel.BEGINNER, **kwargs):
    user = user or create_user()
    profile_data = {"user": user, "gender": gender, "level": level}
    profile_data.update(kwargs)
    return PlayerProfile.objects.create(**profile_data)


def create_club(user=None, **kwargs):
    if user is None:
        user = create_user()

    club_data = {
        "user": user,
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

    def test_default_flags(self):
        user = create_user()

        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_2fa_enabled)

    def test_email_unique(self):
        create_user(email="email@example.com")

        with self.assertRaises(IntegrityError):
            create_user(email="email@example.com")

    def test_clean_raises_for_minor(self):
        today = date.today()
        minor = create_user(
            birth_date=today.replace(year=today.year - 17)
        )

        with self.assertRaises(ValidationError):
            minor.clean()

    def test_clean_accepts_adult(self):
        today = date.today()

        try:
            birth = today.replace(year=today.year - 18)
        except ValueError:
            birth = today.replace(year=today.year - 18, day=28)

        user = create_user(birth_date=birth)

        user.clean()

    def test_user_exactly_18_years_old(self):
        today = date.today()

        try:
            birth_date = today.replace(year=today.year - 18)
        except ValueError:
            # 29 février
            birth_date = today.replace(year=today.year - 18, day=28)

        user = create_user(birth_date=birth_date)

        self.assertTrue(user.is_adult())

    def test_user_turning_18_tomorrow(self):
        today = date.today()

        try:
            birth_date = today.replace(
                year=today.year - 18,
                day=today.day + 1
            )
        except ValueError:
            tomorrow = today + timedelta(days=1)
            birth_date = tomorrow.replace(year=tomorrow.year - 18)

        user = create_user(birth_date=birth_date)

        self.assertFalse(user.is_adult())

    def test_user_who_turned_18_yesterday(self):
        today = date.today()

        try:
            birth_date = today.replace(
                year=today.year - 18,
                day=today.day - 1
            )
        except ValueError:
            yesterday = today - timedelta(days=1)
            birth_date = yesterday.replace(year=yesterday.year - 18)

        user = create_user(birth_date=birth_date)

        self.assertTrue(user.is_adult())

    def test_profile_retrieval(self):
        self.assertIsNone(self.user.get_profile())

        player_profile = create_player(self.user)
        self.assertEqual(self.user.get_profile(), player_profile)

    def test_get_profile_returns_none(self):
        user = create_user()
        self.assertIsNone(user.get_profile())

    def test_user_has_uuid(self):
        user = create_user()

        self.assertIsInstance(user.id, uuid.UUID)


class PlayerProfileTests(TestCase):

    def setUp(self):
        self.user = create_user()

    def test_default_verification_status(self):
        """
        A newly created player profile should not be verified by default.
        """
        player_profile = create_player(self.user)
        self.assertFalse(player_profile.is_verified)

    def test_profile_return_player_profile(self):
        """

        """
        user = create_user()
        player_profile = create_player(user=user)
        self.assertEqual(user.get_profile(), player_profile)

    def test_create_player_assigns_user(self):
        player = create_player()

        self.assertIsNotNone(player.user)


class ClubProfileTests(TestCase):

    def test_default_verification_status(self):
        """
        A newly created club profile should not be verified by default.
        """
        club = create_club()
        self.assertFalse(club.is_verified)

    def test_get_profile_returns_club_profile(self):
        user = create_user()
        club_profile = create_club(user=user)
        self.assertEqual(user.get_profile(), club_profile)

    def test_create_club_assigns_user(self):
        club = create_club()

        self.assertIsNotNone(club.user)
