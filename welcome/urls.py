from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('publisher/', views.publisher_dashboard, name='publisher_dashboard'),
    path('webmaster-dashboard/', views.webmaster_dashboard, name='webmaster_dashboard'),
    path('login-handler/', views.login_handler, name='login_handler'),
    path('signup-handler/', views.signup_handler, name='signup_handler'),
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)