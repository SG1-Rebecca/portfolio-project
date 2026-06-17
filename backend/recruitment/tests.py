import uuid
from datetime import date, timedelta

from django.test import TestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError

from accounts.models import User, PlayerProfile, ClubProfile
from core.enums import Gender, SkillLevel, Status, ApplicationStatus, Position, SectionCategory
from .models import RecruitmentPost, Application


# --- Helpers / Factory Functions ---
def create_user(**kwargs):
    defaults = {
        "username": f"user_{uuid.uuid4().hex[:8]}",
        "email": f"{uuid.uuid4().hex[:8]}@example.com",
    }
    defaults.update(kwargs)
    return User.objects.create_user(**defaults)


def create_player(gender=Gender.MALE, level=SkillLevel.BEGINNER, **kwargs):
    user = create_user()
    profile_data = {"user": user, "gender": gender, "level": level}
    profile_data.update(kwargs)
    return PlayerProfile.objects.create(**profile_data)


def create_club(**kwargs):
    club_data = {
        "club_name": "Recruit FC",
        "president_name": "Jane Doe",
        "foundation_date": date(2000, 1, 1),
        "city": "Lyon",
        "country": "France",
        "league": "National",
        "district": "Rhône-Alpes",
        "social_link": "https://recruitfc.example.com",
    }
    club_data.update(kwargs)
    return ClubProfile.objects.create(**club_data)


def create_post(club=None, category=SectionCategory.MEN, **kwargs):
    club = club or create_club()
    post_data = {
        "club": club,
        "category": category,
        "position_needed": Position.FORWARD,
        "status": Status.OPEN,
        "title": "Recherche attaquant",
        "level_required": SkillLevel.INTERMEDIATE,
        "region": "Rhône-Alpes",
        "description": "Club ambitieux.",
        "application_deadline": date.today() + timedelta(days=30),
    }
    post_data.update(kwargs)
    return RecruitmentPost.objects.create(**post_data)


def apply(player, post, message="I want to join the club", **kwargs):
    app_data = {
        "player": player,
        "post": post,
        "player_message": message,
        "contact_revealed": False,
        "status": ApplicationStatus.PENDING,
    }
    app_data.update(kwargs)
    return Application.objects.create(**app_data)


class RecruitmentPostTests(TestCase):
    """
    Basic tests for the RecruitmentPost model.
    """

    def setUp(self):
        self.club = create_club()

    def test_description_optional(self):
        """La description peut être vide"""
        post = create_post(self.club, description="")
        self.assertEqual(post.description, "")

    def test_title_is_required(self):
        post = RecruitmentPost(
            club=self.club,
            category=SectionCategory.MEN,
            position_needed=Position.FORWARD,
            status=Status.OPEN,
            title="",
            level_required=SkillLevel.INTERMEDIATE,
            region="Rhône-Alpes",
            application_deadline=date.today()
        )

        with self.assertRaises(ValidationError):
            post.full_clean()

    def test_ordering_by_deadline(self):
        """
        Posts should be ordered by deadline descending (furthest deadline first).
        """
        post_with_later_deadline = create_post(self.club, application_deadline=date.today() + timedelta(days=10))
        post_with_earlier_deadline = create_post(self.club, application_deadline=date.today() + timedelta(days=5))

        posts = list(RecruitmentPost.objects.all())
        # '-application_deadline' ordering is descending, so the post with the
        # furthest deadline (largest date value) comes first.
        self.assertEqual(posts[0], post_with_later_deadline)
        self.assertEqual(posts[1], post_with_earlier_deadline)


class ApplicationLogicTests(TestCase):
    """
    Complex tests covering business rules, gender constraints, and model validation.
    """

    def setUp(self):
        self.male_player = create_player(gender=Gender.MALE)
        self.female_player = create_player(gender=Gender.FEMALE)
        self.mens_post = create_post(category=SectionCategory.MEN)
        self.womens_post = create_post(category=SectionCategory.WOMEN)

    def test_defaults_are_correct(self):
        """Vérifie les valeurs par défaut d'une candidature"""
        app = apply(self.male_player, self.mens_post)
        self.assertEqual(app.status, ApplicationStatus.PENDING)
        self.assertFalse(app.contact_revealed)
        self.assertEqual(app.player_message, "I want to join the club")

    def test_allowed_gender_match(self):
        """
        A player should be able to apply to a post matching their gender.
        """
        Application(
            player=self.male_player,
            post=self.mens_post
        ).full_clean()

        Application(
            player=self.female_player,
            post=self.womens_post
        ).full_clean()

    def test_blocked_gender_mismatch(self):
        """
        A player must not be able to apply to a post intended for the opposite gender.
        """
        woman_on_mens_post = Application(player=self.female_player, post=self.mens_post)
        with self.assertRaises(ValidationError) as ctx:
            woman_on_mens_post.full_clean()
        self.assertIn("reserved for men", str(ctx.exception).lower())

        man_on_female_post = Application(player=self.male_player, post=self.womens_post)
        with self.assertRaises(ValidationError) as ctx:
            man_on_female_post.full_clean()
        self.assertIn("reserved for women", str(ctx.exception).lower())

    def test_unique_application(self):
        """
        A player should not be able to submit more than one application for the same post.
        """
        apply(self.male_player, self.mens_post)

        duplicate_app = Application(player=self.male_player, post=self.mens_post)
        with self.assertRaises(IntegrityError):
            duplicate_app.save()

    def test_ordering_newest_first(self):
        """
        Applications should be sorted by creation date with the most recent first.
        """
        first_player = create_player()
        second_player = create_player()

        first_applicant = apply(first_player, self.mens_post)
        second_applicant = apply(second_player, self.mens_post)

        apps = list(Application.objects.all())
        # second_application was created after first_application, so it should appear first
        # due to the '-created_at' ordering.

        self.assertEqual(apps[0], second_applicant)
        self.assertEqual(apps[1], first_applicant)

    def test_cannot_apply_after_deadline(self):
        """
        Applying to a post whose deadline has passed should fail validation.
        """
        expired_post = create_post(
            application_deadline=date.today() - timedelta(days=1)
        )

        app = Application(
            player=self.male_player,
            post=expired_post
        )

        with self.assertRaises(ValidationError):
            app.full_clean()

    def test_player_message_can_be_blank(self):
        app = apply(
            self.male_player,
            self.mens_post,
            message=""
        )

        self.assertEqual(app.player_message, "")
