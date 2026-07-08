from rest_framework import status, generics
from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.http import Http404
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from accounts.models import ClubProfile, PlayerProfile
from accounts.permissions import IsPlayer, IsClub, IsOwnerOrReadOnly
from core.enums import ApplicationStatus
from .models import RecruitmentPost, Application
from .serializers import (
    RecruitmentPostSerializer, ApplicationSerializer, ApplicationStatusSerializer
)


class PostListCreateView(APIView):
    FILTERS = {
        'position': 'position_needed',
        'level': 'level_required',
        'region': 'region',
    }

    def get_permissions(self):
        return [IsAuthenticated(), IsClub()] if self.request.method == 'POST' else [AllowAny()]

    @extend_schema(
        operation_id='posts_list',
        responses=RecruitmentPostSerializer(many=True),
        parameters=[
            OpenApiParameter('position', OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter('level', OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter('region', OpenApiTypes.STR, OpenApiParameter.QUERY),
        ],
    )
    def get(self, request):
        queryset = RecruitmentPost.objects.filter(status='OPEN').select_related('club__user')
        for param, field in self.FILTERS.items():
            value = request.query_params.get(param)
            if value:
                queryset = queryset.filter(**{field: value})
        return Response(RecruitmentPostSerializer(queryset, many=True).data)

    @extend_schema(request=RecruitmentPostSerializer, responses={201: RecruitmentPostSerializer})
    def post(self, request):
        club_profile = ClubProfile.objects.filter(user=request.user).first()
        if not club_profile:
            return Response(
                {"detail": "Club profile must be completed before creating a post."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = RecruitmentPostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(club=club_profile)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PostDetailView(generics.RetrieveUpdateAPIView):

    def get_permissions(self):
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
            return [AllowAny()]
        return [IsAuthenticated(), IsClub()]

    def _get_own_post(self, request, pk):

        try:
            club = request.user.clubprofile
            return RecruitmentPost.objects.select_related('club').get(pk=pk, club=club)
        except (RecruitmentPost.DoesNotExist, ClubProfile.DoesNotExist):
            return None

    @extend_schema(operation_id='posts_retrieve', responses=RecruitmentPostSerializer)
    def get(self, request, pk):
        post = RecruitmentPost.objects.select_related('club').filter(pk=pk).first()
        if not post:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(RecruitmentPostSerializer(post).data)

    @extend_schema(request=RecruitmentPostSerializer, responses=RecruitmentPostSerializer)
    def put(self, request, pk):
        post = self._get_own_post(request, pk)
        if not post:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = RecruitmentPostSerializer(post, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(request=RecruitmentPostSerializer, responses=RecruitmentPostSerializer)
    def patch(self, request, pk):
        post = self._get_own_post(request, pk)
        if not post:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = RecruitmentPostSerializer(post, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ApplicationSubmitView(GenericAPIView):
    permission_classes = [IsAuthenticated, IsPlayer]
    serializer_class = ApplicationSerializer

    @extend_schema(request=ApplicationSerializer, responses={201: ApplicationSerializer})
    def post(self, request):
        player_profile = PlayerProfile.objects.filter(user=request.user).first()
        if not player_profile:
            return Response(
                {"detail": "Player profile must be completed before applying."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ApplicationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(player=player_profile)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MyApplicationsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsPlayer]
    serializer_class = ApplicationSerializer

    def get_queryset(self):
        return Application.objects.filter(player__user=self.request.user).select_related('player__user', 'post__club')


class PostApplicantsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsClub]
    serializer_class = ApplicationSerializer

    def get_queryset(self):
        return Application.objects.filter(
            post_id=self.kwargs['pk'],
            post__club__user=self.request.user,
        ).select_related('player__user', 'post__club')


class ApplicationUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsClub]

    @extend_schema(request=ApplicationStatusSerializer, responses=ApplicationSerializer)
    def patch(self, request, pk):
        try:
            app = Application.objects.get(pk=pk, post__club__user=request.user)
        except Application.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = ApplicationStatusSerializer(app, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data.get('status')
        serializer.save()

        if new_status == ApplicationStatus.ACCEPTED and not app.contact_revealed:
            app.contact_revealed = True
            app.save(update_fields=['contact_revealed'])

        return Response(ApplicationSerializer(app).data, status=status.HTTP_200_OK)
