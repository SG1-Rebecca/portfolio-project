from rest_framework import status, generics
from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from accounts.models import ClubProfile, PlayerProfile
from accounts.permissions import IsPlayer, IsClub
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
        return [IsClub()] if self.request.method == 'POST' else [AllowAny()]

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
        qs = RecruitmentPost.objects.filter(status='OPEN')
        for param, field in self.FILTERS.items():
            value = request.query_params.get(param)
            if value:
                qs = qs.filter(**{field: value})
        return Response(RecruitmentPostSerializer(qs, many=True).data)

    @extend_schema(
        request=RecruitmentPostSerializer,
        responses={201: RecruitmentPostSerializer},
    )

    def post(self, request):
        club = ClubProfile.objects.filter(user=request.user).first()

        if not club:
            return Response({'detail': 'Club profile required.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = RecruitmentPostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(club=club)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PostDetailView(APIView):

    def get_permissions(self):
        return [IsClub()] if self.request.method == 'PUT' else [AllowAny()]

    def _get_own_post(self, request, pk):
        try:
            club = request.user.clubprofile
            return RecruitmentPost.objects.get(pk=pk, club=club)
        except (RecruitmentPost.DoesNotExist, ClubProfile.DoesNotExist):
            return None

    @extend_schema(operation_id='posts_retrieve', responses=RecruitmentPostSerializer)
    def get(self, request, pk):
        post = RecruitmentPost.objects.filter(pk=pk).first()
        if not post:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(RecruitmentPostSerializer(post).data)

    @extend_schema(request=RecruitmentPostSerializer, responses=RecruitmentPostSerializer)
    def put(self, request, pk):
        post = self._get_own_post(request, pk)
        if not post:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = RecruitmentPostSerializer(post, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ApplicationSubmitView(GenericAPIView):
    permission_classes = [IsPlayer]
    serializer_class = ApplicationSerializer

    def post(self, request):
        player = PlayerProfile.objects.filter(user=request.user).first()
        if not player:
            return Response({'detail': 'Player profile required.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(player=player)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MyApplicationsView(generics.ListAPIView):
    permission_classes = [IsPlayer]
    serializer_class = ApplicationSerializer

    def get_queryset(self):
        return Application.objects.filter(player__user=self.request.user)


class PostApplicantsView(generics.ListAPIView):
    permission_classes = [IsClub]
    serializer_class = ApplicationSerializer

    def get_queryset(self):
        return Application.objects.filter(
            post_id=self.kwargs['pk'],
            post__club__user=self.request.user,
        )


class ApplicationUpdateView(APIView):
    permission_classes = [IsClub]

    @extend_schema(
        request=ApplicationStatusSerializer,
        responses=ApplicationSerializer,
    )

    def patch(self, request, pk):
        try:
            app = Application.objects.get(pk=pk, post__club__user=request.user)
        except Application.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = ApplicationStatusSerializer(app, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data.get('status')

        if new_status == ApplicationStatus.ACCEPTED:
            app.contact_revealed = True
            app.save(update_fields=['contact_revealed'])
        serializer.save()
        return Response(ApplicationSerializer(app).data)

