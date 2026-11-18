from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('tasks/new/', views.TaskCreateView.as_view(), name='task_create'),
    path('projects/new/', views.ProjectCreateView.as_view(), name='project_create'), # <-- AGREGAR ESTA LÍNEA
    path('profile/', views.ProfileView.as_view(), name='profile'),
]