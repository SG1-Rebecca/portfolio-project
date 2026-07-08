import uuid
from datetime import date, timedelta

from django.test import TestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError

from accounts.models import User, PlayerProfile, ClubProfile
from core.enums import (
    Gender, SkillLevel, RecruitmentStatus, ApplicationStatus,
    RecruitmentPosition, PlayerPosition, SectionCategory,
)
from .models import RecruitmentPost, Application


# --- Helpers / Factory Functions ---

def create_user(**kwargs):
    defaults = {
        "email": f"{uuid.uuid4().hex[:8]}@example.com",
        "birth_date": date(1995, 6, 15),   # majeur, toujours valide
    }
    defaults.update(kwargs)
    return User.objects.create_user(**defaults)


def create_player(
    gender=Gender.MALE,
    level=SkillLevel.BEGINNER,
    position=PlayerPosition.FORWARD,
    **kwargs,
):
    user = create_user()
    profile_data = {
        "user": user,
        "first_name": "Alice" if gender == Gender.FEMALE else "Bob",
        "last_name": "Test",
        "gender": gender,
        "level": level,
        "position": position,
    }
    profile_data.update(kwargs)
    return PlayerProfile.objects.create(**profile_data)


def create_club(**kwargs):
    user = create_user()
    club_data = {
        "user": user,
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
        "position_needed": RecruitmentPosition.FORWARD,
        "status": RecruitmentStatus.OPEN,
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
    """Tests du modèle RecruitmentPost."""

    def setUp(self):
        self.club = create_club()

    def test_description_optional(self):
        post = create_post(self.club, description="")
        self.assertEqual(post.description, "")

    def test_title_required(self):
        post = RecruitmentPost(
            club=self.club,
            category=SectionCategory.MEN,
            position_needed=RecruitmentPosition.FORWARD,
            status=RecruitmentStatus.OPEN,
            title="",
            level_required=SkillLevel.INTERMEDIATE,
            region="Rhône-Alpes",
            application_deadline=date.today() + timedelta(days=10),
        )
        with self.assertRaises(ValidationError):
            post.full_clean()

    def test_title_max_length(self):
        post = RecruitmentPost(
            club=self.club,
            category=SectionCategory.MEN,
            position_needed=RecruitmentPosition.FORWARD,
            status=RecruitmentStatus.OPEN,
            title="A" * 151,
            level_required=SkillLevel.INTERMEDIATE,
            region="Rhône-Alpes",
            application_deadline=date.today() + timedelta(days=10),
        )
        with self.assertRaises(ValidationError):
            post.full_clean()

    def test_region_cannot_be_blank(self):
        """La région ne peut pas être vide."""
        post = RecruitmentPost(
            club=self.club,
            category=SectionCategory.MEN,
            position_needed=RecruitmentPosition.FORWARD,
            status=RecruitmentStatus.OPEN,
            title="Recherche joueur",
            level_required=SkillLevel.INTERMEDIATE,
            region="",
            application_deadline=date.today() + timedelta(days=10),
        )
        with self.assertRaises(ValidationError):
            post.full_clean()

    # --- Ordering ---

    def test_ordering_by_deadline_descending(self):
        """Les posts sont triés par deadline décroissante (la plus lointaine en premier)."""
        later = create_post(self.club, application_deadline=date.today() + timedelta(days=10))
        earlier = create_post(self.club, application_deadline=date.today() + timedelta(days=5))

        posts = list(RecruitmentPost.objects.all())
        self.assertEqual(posts[0], later)
        self.assertEqual(posts[1], earlier)

    # --- Statut ---

    def test_post_status_open_by_default_in_factory(self):
        post = create_post(self.club)
        self.assertEqual(post.status, RecruitmentStatus.OPEN)

    def test_post_can_be_closed(self):
        post = create_post(self.club, status=RecruitmentStatus.CLOSED)
        self.assertEqual(post.status, RecruitmentStatus.CLOSED)

    # --- Cascade ---

    def test_delete_club_cascades_to_posts(self):
        """Supprimer un club supprime ses annonces."""
        post_id = create_post(self.club).pk
        self.club.delete()
        self.assertFalse(RecruitmentPost.objects.filter(pk=post_id).exists())

    def test_delete_post_cascades_to_applications(self):
        """Supprimer un post supprime les candidatures associées."""
        post = create_post(self.club)
        player = create_player()
        app = apply(player, post)
        post.delete()
        self.assertFalse(Application.objects.filter(pk=app.pk).exists())


class ApplicationDefaultsTests(TestCase):
    """Valeurs par défaut et champs facultatifs."""

    def setUp(self):
        self.player = create_player(gender=Gender.MALE, position=PlayerPosition.FORWARD)
        self.post = create_post(
            category=SectionCategory.MEN,
            position_needed=RecruitmentPosition.FORWARD,
        )

    def test_defaults_are_correct(self):
        """Statut PENDING et contact_revealed False par défaut."""
        app = apply(self.player, self.post)
        self.assertEqual(app.status, ApplicationStatus.PENDING)
        self.assertFalse(app.contact_revealed)

    def test_player_message_can_be_blank(self):
        """Le message de motivation peut être vide."""
        app = apply(self.player, self.post, message="")
        self.assertEqual(app.player_message, "")

    def test_contact_revealed_can_be_set_true(self):
        """contact_revealed peut être mis à True (ex : après acceptation)."""
        app = apply(self.player, self.post, contact_revealed=True)
        self.assertTrue(app.contact_revealed)


class ApplicationGenderTests(TestCase):
    """Règles de genre : cohérence joueur ↔ catégorie de l'annonce."""

    def setUp(self):
        self.male_player = create_player(gender=Gender.MALE, position=PlayerPosition.FORWARD)
        self.female_player = create_player(gender=Gender.FEMALE, position=PlayerPosition.FORWARD)
        self.mens_post = create_post(
            category=SectionCategory.MEN,
            position_needed=RecruitmentPosition.FORWARD,
        )
        self.womens_post = create_post(
            category=SectionCategory.WOMEN,
            position_needed=RecruitmentPosition.FORWARD,
        )

    def test_male_can_apply_to_mens_post(self):
        """Un homme peut postuler à une annonce masculine."""
        Application(player=self.male_player, post=self.mens_post).full_clean()

    def test_female_can_apply_to_womens_post(self):
        """Une femme peut postuler à une annonce féminine."""
        Application(player=self.female_player, post=self.womens_post).full_clean()

    def test_female_blocked_on_mens_post(self):
        """Une femme ne peut pas postuler à une annonce masculine."""
        app = Application(player=self.female_player, post=self.mens_post)
        with self.assertRaises(ValidationError) as ctx:
            app.full_clean()
        self.assertIn("men", str(ctx.exception).lower())

    def test_male_blocked_on_womens_post(self):
        app = Application(player=self.male_player, post=self.womens_post)
        with self.assertRaises(ValidationError) as ctx:
            app.full_clean()
        self.assertIn("women", str(ctx.exception).lower())


class ApplicationPositionTests(TestCase):

    def setUp(self):
        self.club = create_club()

    def test_matching_position_is_valid(self):
        player = create_player(position=PlayerPosition.FORWARD)
        post = create_post(
            self.club,
            category=SectionCategory.MEN,
            position_needed=RecruitmentPosition.FORWARD,
        )
        Application(player=player, post=post).full_clean()

    def test_mismatched_position_is_blocked(self):
        player = create_player(position=PlayerPosition.GOALKEEPER)
        post = create_post(
            self.club,
            category=SectionCategory.MEN,
            position_needed=RecruitmentPosition.FORWARD,
        )
        app = Application(player=player, post=post)
        with self.assertRaises(ValidationError) as ctx:
            app.full_clean()
        self.assertIn("position", str(ctx.exception).lower())

    def test_universal_player_bypasses_position_check(self):
        player = create_player(position=PlayerPosition.UNIVERSAL)
        post = create_post(
            self.club,
            category=SectionCategory.MEN,
            position_needed=RecruitmentPosition.FORWARD,
        )
        Application(player=player, post=post).full_clean()

    def test_any_position_post_accepts_all_players(self):
        player = create_player(position=PlayerPosition.GOALKEEPER)
        post = create_post(
            self.club,
            category=SectionCategory.MEN,
            position_needed=RecruitmentPosition.ANY,
        )
        Application(player=player, post=post).full_clean()

    def test_universal_player_on_any_post(self):
        player = create_player(position=PlayerPosition.UNIVERSAL)
        post = create_post(
            self.club,
            category=SectionCategory.MEN,
            position_needed=RecruitmentPosition.ANY,
        )
        Application(player=player, post=post).full_clean()


class ApplicationDeadlineTests(TestCase):

    def setUp(self):
        self.player = create_player(position=PlayerPosition.FORWARD)

    def test_apply_after_deadline(self):
        expired_post = create_post(
            application_deadline=date.today() - timedelta(days=1),
        )
        app = Application(player=self.player, post=expired_post)
        with self.assertRaises(ValidationError):
            app.full_clean()

    def test_apply_on_deadline_day(self):
        post = create_post(application_deadline=date.today())
        Application(player=self.player, post=post).full_clean()

    def test_apply_before_deadline(self):
        post = create_post(application_deadline=date.today() + timedelta(days=1))
        Application(player=self.player, post=post).full_clean()


class ApplicationConstraintTests(TestCase):

    def setUp(self):
        self.player = create_player(position=PlayerPosition.FORWARD)
        self.post = create_post(
            category=SectionCategory.MEN,
            position_needed=RecruitmentPosition.FORWARD,
        )

    def test_unique_application(self):
        apply(self.player, self.post)
        with self.assertRaises(IntegrityError):
            Application(player=self.player, post=self.post).save()

    def test_player_can_apply_to_different_posts(self):
        second_post = create_post(
            category=SectionCategory.MEN,
            position_needed=RecruitmentPosition.FORWARD,
        )
        apply(self.player, self.post)
        app2 = apply(self.player, second_post)
        self.assertIsNotNone(app2.pk)

    def test_different_players_can_apply_to_same_post(self):
        second_player = create_player(position=PlayerPosition.FORWARD)
        app1 = apply(self.player, self.post)
        app2 = apply(second_player, self.post)
        self.assertNotEqual(app1.pk, app2.pk)


class ApplicationStatusTests(TestCase):
    """Transitions de statut d'une candidature."""

    def setUp(self):
        self.player = create_player(position=PlayerPosition.FORWARD)
        self.post = create_post(
            category=SectionCategory.MEN,
            position_needed=RecruitmentPosition.FORWARD,
        )

    def test_accept_application(self):
        app = apply(self.player, self.post)
        app.status = ApplicationStatus.ACCEPTED
        app.save()
        app.refresh_from_db()
        self.assertEqual(app.status, ApplicationStatus.ACCEPTED)

    def test_reject_application(self):
        app = apply(self.player, self.post)
        app.status = ApplicationStatus.REJECTED
        app.save()
        app.refresh_from_db()
        self.assertEqual(app.status, ApplicationStatus.REJECTED)

    def test_withdraw_application(self):
        app = apply(self.player, self.post)
        app.status = ApplicationStatus.WITHDRAWN
        app.save()
        app.refresh_from_db()
        self.assertEqual(app.status, ApplicationStatus.WITHDRAWN)


class ApplicationOrderingTests(TestCase):

    def setUp(self):
        self.post = create_post(
            category=SectionCategory.MEN,
            position_needed=RecruitmentPosition.FORWARD,
        )

    def test_ordering_newest_first(self):
        first_app = apply(create_player(position=PlayerPosition.FORWARD), self.post)
        second_app = apply(create_player(position=PlayerPosition.FORWARD), self.post)

        apps = list(Application.objects.all())
        self.assertEqual(apps[0], second_app)
        self.assertEqual(apps[1], first_app)


class ApplicationCascadeTests(TestCase):

    def test_delete_player_cascades_to_applications(self):
        player = create_player(position=PlayerPosition.FORWARD)
        post = create_post(
            category=SectionCategory.MEN,
            position_needed=RecruitmentPosition.FORWARD,
        )
        app = apply(player, post)
        player.delete()
        self.assertFalse(Application.objects.filter(pk=app.pk).exists())