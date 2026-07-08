from django.urls import path
from . import views

urlpatterns = [
    path('posts/', views.PostListCreateView.as_view()),
    path('posts/<uuid:pk>/', views.PostDetailView.as_view()),
    path('posts/<uuid:pk>/applicants/', views.PostApplicantsView.as_view()),

    # Application
    path('applications/', views.ApplicationSubmitView.as_view()),
    path('applications/me/', views.MyApplicationsView.as_view()),
    path('applications/<uuid:pk>/', views.ApplicationUpdateView.as_view()),
]
