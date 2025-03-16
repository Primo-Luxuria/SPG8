from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('publisher/', views.publisher_dashboard, name='publisher_dashboard'),
]

    