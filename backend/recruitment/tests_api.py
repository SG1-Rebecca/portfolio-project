import uuid
from datetime import date, timedelta

from django.test import TestCase

from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from accounts.models import User, PlayerProfile, ClubProfile
from core.enums import (
    Gender, SkillLevel, Role,
    PlayerPosition, RecruitmentPosition,
    RecruitmentStatus, ApplicationStatus, SectionCategory,
)
from recruitment.models import RecruitmentPost, Application
from recruitment.views import (
    PostListCreateView,
    PostDetailView,
    ApplicationSubmitView,
    MyApplicationsView,
    PostApplicantsView,
    ApplicationUpdateView,
)

factory = APIRequestFactory()


# Helpers

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
    return User.objects.create_user(password="StrongPass123!", **defaults)


def create_player(gender=Gender.MALE, position=PlayerPosition.FORWARD, **kwargs):
    user = create_user(role=Role.PLAYER)
    defaults = {
        "user": user,
        "first_name": "Alice" if gender == Gender.FEMALE else "Bob",
        "last_name": "Test",
        "gender": gender,
        "level": SkillLevel.INTERMEDIATE,
        "position": position,
    }
    defaults.update(kwargs)
    return PlayerProfile.objects.create(**defaults)


def create_club(**kwargs):
    user = create_user(role=Role.CLUB)
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


def create_post(club, category=SectionCategory.MEN, position=RecruitmentPosition.FORWARD, **kwargs):
    defaults = {
        "club": club,
        "title": "Recherche attaquant",
        "status": RecruitmentStatus.OPEN,
        "category": category,
        "position_needed": position,
        "level_required": SkillLevel.INTERMEDIATE,
        "region": "Rhône-Alpes",
        "description": "Club ambitieux.",
        "application_deadline": date.today() + timedelta(days=30),
    }
    defaults.update(kwargs)
    return RecruitmentPost.objects.create(**defaults)


def create_application(player, post, **kwargs):
    defaults = {
        "player": player,
        "post": post,
        "player_message": "Je veux rejoindre le club.",
        "status": ApplicationStatus.PENDING,
    }
    defaults.update(kwargs)
    return Application.objects.create(**defaults)


# PostListCreateView  GET=AllowAny  POST=IsClub

class PostListCreateViewTests(TestCase):

    def setUp(self):
        self.club = create_club()
        self.post = create_post(self.club)

    def _get(self, user=None, params=None):
        request = factory.get("/recruitment/posts/", params or {})
        if user:
            force_authenticate(request, user=user)
        return PostListCreateView.as_view()(request)

    def _post(self, user, data):
        request = factory.post("/recruitment/posts/", data, format="json")
        force_authenticate(request, user=user)
        return PostListCreateView.as_view()(request)

    # --- GET public ---

    def test_anyone_can_list_open_posts(self):
        response = self._get()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_closed_posts_not_returned(self):
        create_post(self.club, status=RecruitmentStatus.CLOSED)
        response = self._get()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_by_position(self):
        create_post(self.club, position=RecruitmentPosition.GOALKEEPER)
        response = self._get(params={"position": RecruitmentPosition.GOALKEEPER})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["position_needed"], RecruitmentPosition.GOALKEEPER)

    def test_filter_by_region(self):
        create_post(self.club, region="Paris")
        response = self._get(params={"region": "Paris"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["region"], "Paris")

    def test_filter_by_level(self):
        create_post(self.club, level_required=SkillLevel.PRO)
        response = self._get(params={"level": SkillLevel.PRO})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_returns_empty_if_no_match(self):
        response = self._get(params={"region": "Inexistant"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    # --- POST (IsClub) ---

    def test_club_can_create_post(self):
        data = {
            "title": "Nouveau poste",
            "status": RecruitmentStatus.OPEN,
            "category": SectionCategory.MEN,
            "position_needed": RecruitmentPosition.DEFENDER,
            "level_required": SkillLevel.ADVANCED,
            "region": "Paris",
            "description": "Recherche défenseur.",
            "application_deadline": (date.today() + timedelta(days=15)).isoformat(),
        }
        response = self._post(self.club.user, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RecruitmentPost.objects.count(), 2)

    def test_club_without_profile_cannot_create_post(self):
        user_no_profile = create_user(role=Role.CLUB)
        data = {
            "title": "Test",
            "status": RecruitmentStatus.OPEN,
            "category": SectionCategory.MEN,
            "position_needed": RecruitmentPosition.FORWARD,
            "level_required": SkillLevel.BEGINNER,
            "region": "Lyon",
            "description": "Test.",
            "application_deadline": (date.today() + timedelta(days=10)).isoformat(),
        }
        response = self._post(user_no_profile, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_player_cannot_create_post(self):
        player = create_player()
        data = {"title": "Hack", "status": RecruitmentStatus.OPEN}
        response = self._post(player.user, data)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED])

    def test_unauthenticated_cannot_create_post(self):
        request = factory.post("/recruitment/posts/", {}, format="json")
        response = PostListCreateView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_post_missing_required_field_returns_400(self):
        data = {"title": ""}
        response = self._post(self.club.user, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# PostDetailView  GET=AllowAny  PUT=IsClub

class PostDetailViewTests(TestCase):

    def setUp(self):
        self.club = create_club()
        self.post = create_post(self.club)
        self.other_club = create_club()

    def _get(self, pk, user=None):
        request = factory.get(f"/recruitment/posts/{pk}/")
        if user:
            force_authenticate(request, user=user)
        return PostDetailView.as_view()(request, pk=str(pk))

    def _put(self, pk, user, data):
        request = factory.put(f"/recruitment/posts/{pk}/", data, format="json")
        force_authenticate(request, user=user)
        return PostDetailView.as_view()(request, pk=str(pk))

    def _patch(self, pk, user, data):
        request = factory.patch(f"/recruitment/posts/{pk}/", data, format="json")
        force_authenticate(request, user=user)
        return PostDetailView.as_view()(request, pk=str(pk))

    # --- GET ---

    def test_anyone_can_get_post_detail(self):
        response = self._get(self.post.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Recherche attaquant")

    def test_get_nonexistent_post_returns_404(self):
        response = self._get(uuid.uuid4())
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- PUT ---

    def test_owner_club_can_update_post(self):
        response = self._patch(self.post.pk, self.club.user, {"title": "Titre modifié"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "Titre modifié")

    def test_other_club_cannot_update_post(self):
        response = self._put(self.post.pk, self.other_club.user, {"title": "Hack"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_player_cannot_update_post(self):
        player = create_player()
        response = self._put(self.post.pk, player.user, {"title": "Hack"})
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED])

    def test_update_nonexistent_post_returns_404(self):
        response = self._put(uuid.uuid4(), self.club.user, {"title": "X"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_post_returns_405(self):
        request = factory.delete(f"/recruitment/posts/{self.post.pk}/")
        force_authenticate(request, user=self.club.user)
        response = PostDetailView.as_view()(request, pk=str(self.post.pk))

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


# ApplicationSubmitView  POST=IsPlayer

class ApplicationSubmitViewTests(TestCase):

    def setUp(self):
        self.club = create_club()
        self.player = create_player(
            gender=Gender.MALE,
            position=PlayerPosition.FORWARD,
        )
        self.post = create_post(
            self.club,
            category=SectionCategory.MEN,
            position=RecruitmentPosition.FORWARD,
        )

    def _post(self, user, data):
        request = factory.post("/recruitment/applications/", data, format="json")
        force_authenticate(request, user=user)
        return ApplicationSubmitView.as_view()(request)

    def test_player_can_submit_application(self):
        response = self._post(self.player.user, {
            "post": str(self.post.pk),
            "player_message": "Je suis motivé.",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Application.objects.count(), 1)

    def test_application_default_status_is_pending(self):
        self._post(self.player.user, {"post": str(self.post.pk)})
        app = Application.objects.first()
        self.assertEqual(app.status, ApplicationStatus.PENDING)

    def test_player_without_profile_gets_400(self):
        user_no_profile = create_user(role=Role.PLAYER)
        response = self._post(user_no_profile, {"post": str(self.post.pk)})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_club_cannot_submit_application(self):
        response = self._post(self.club.user, {"post": str(self.post.pk)})
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED])

    def test_unauthenticated_cannot_submit(self):
        request = factory.post("/recruitment/applications/", {"post": str(self.post.pk)}, format="json")
        response = ApplicationSubmitView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_duplicate_application_returns_400(self):
        self._post(self.player.user, {"post": str(self.post.pk)})
        response = self._post(self.player.user, {"post": str(self.post.pk)})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_apply_to_expired_post(self):
        expired_post = create_post(
            self.club,
            category=SectionCategory.MEN,
            position=RecruitmentPosition.FORWARD,
            application_deadline=date.today() - timedelta(days=1),
        )
        response = self._post(self.player.user, {"post": str(expired_post.pk)})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_gender_mismatch_returns_400(self):
        female_player = create_player(gender=Gender.FEMALE, position=PlayerPosition.FORWARD)
        response = self._post(female_player.user, {"post": str(self.post.pk)})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_position_mismatch_returns_400(self):
        gk_player = create_player(gender=Gender.MALE, position=PlayerPosition.GOALKEEPER)
        response = self._post(gk_player.user, {"post": str(self.post.pk)})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_universal_player_can_apply_to_any_position(self):
        universal = create_player(gender=Gender.MALE, position=PlayerPosition.UNIVERSAL)
        response = self._post(universal.user, {"post": str(self.post.pk)})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


# MyApplicationsView  GET=IsPlayer

class MyApplicationsViewTests(TestCase):

    def setUp(self):
        self.club = create_club()
        self.player = create_player()
        self.post = create_post(self.club)
        self.application = create_application(self.player, self.post)

    def _get(self, user=None):
        request = factory.get("/recruitment/applications/me/")
        if user:
            force_authenticate(request, user=user)
        return MyApplicationsView.as_view()(request)

    def test_player_sees_own_applications(self):
        response = self._get(self.player.user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_player_does_not_see_other_players_applications(self):
        other_player = create_player()
        create_application(other_player, create_post(self.club))
        response = self._get(self.player.user)
        self.assertEqual(len(response.data), 1)

    def test_club_cannot_access_my_applications(self):
        response = self._get(self.club.user)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED])

    def test_unauthenticated_returns_401(self):
        response = self._get()
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# PostApplicantsView  GET=IsClub

class PostApplicantsViewTests(TestCase):

    def setUp(self):
        self.club = create_club()
        self.post = create_post(self.club)
        self.player = create_player()
        self.application = create_application(self.player, self.post)
        self.other_club = create_club()

    def _get(self, pk, user=None):
        request = factory.get(f"/recruitment/posts/{pk}/applicants/")
        if user:
            force_authenticate(request, user=user)
        return PostApplicantsView.as_view()(request, pk=str(pk))

    def test_owner_club_sees_applicants(self):
        response = self._get(self.post.pk, self.club.user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_other_club_sees_no_applicants(self):
        response = self._get(self.post.pk, self.other_club.user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_player_cannot_see_applicants(self):
        response = self._get(self.post.pk, self.player.user)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED])

    def test_unauthenticated_returns_401(self):
        response = self._get(self.post.pk)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_multiple_applicants_returned(self):
        second_player = create_player()
        create_application(second_player, self.post)
        response = self._get(self.post.pk, self.club.user)
        self.assertEqual(len(response.data), 2)


# ApplicationUpdateView  PATCH=IsClub (propriétaire du post)

class ApplicationUpdateViewTests(TestCase):

    def setUp(self):
        self.club = create_club()
        self.post = create_post(self.club)
        self.player = create_player()
        self.application = create_application(self.player, self.post)
        self.other_club = create_club()

    def _patch(self, pk, user, data):
        request = factory.patch(f"/recruitment/applications/{pk}/", data, format="json")
        force_authenticate(request, user=user)
        return ApplicationUpdateView.as_view()(request, pk=str(pk))

    # --- ACCEPTED ---

    def test_club_can_accept_application(self):
        response = self._patch(self.application.pk, self.club.user, {"status": ApplicationStatus.ACCEPTED})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, ApplicationStatus.ACCEPTED)

    def test_accept_reveals_contact(self):
        self._patch(self.application.pk, self.club.user, {"status": ApplicationStatus.ACCEPTED})
        self.application.refresh_from_db()
        self.assertTrue(self.application.contact_revealed)

    def test_contact_field_populated_after_accept(self):
        response = self._patch(self.application.pk, self.club.user, {"status": ApplicationStatus.ACCEPTED})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data.get("contact"))
        self.assertEqual(response.data["contact"], self.player.user.email)

    # --- REJECTED ---

    def test_club_can_reject_application(self):
        response = self._patch(self.application.pk, self.club.user, {"status": ApplicationStatus.REJECTED})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, ApplicationStatus.REJECTED)

    def test_reject_does_not_reveal_contact(self):
        self._patch(self.application.pk, self.club.user, {"status": ApplicationStatus.REJECTED})
        self.application.refresh_from_db()
        self.assertFalse(self.application.contact_revealed)

    # --- Permissions ---

    def test_other_club_cannot_update_application(self):
        response = self._patch(self.application.pk, self.other_club.user, {"status": ApplicationStatus.ACCEPTED})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_player_cannot_update_application_status(self):
        response = self._patch(self.application.pk, self.player.user, {"status": ApplicationStatus.ACCEPTED})
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED])

    def test_unauthenticated_returns_401(self):
        request = factory.patch(
            f"/recruitment/applications/{self.application.pk}/",
            {"status": ApplicationStatus.ACCEPTED},
            format="json",
        )
        response = ApplicationUpdateView.as_view()(request, pk=str(self.application.pk))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_nonexistent_application_returns_404(self):
        response = self._patch(uuid.uuid4(), self.club.user, {"status": ApplicationStatus.ACCEPTED})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
