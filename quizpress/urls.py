"""
URL configuration for quizpress project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from django.contrib import admin
from django.urls import include, path
from django.http import HttpResponse
from django.shortcuts import render

from quizpress import settings
from welcome import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('welcome.urls')),
    path("teacher/", views.teacher_dashboard, name="teacher_dashboard"),  # Load the HTM page
    path('parse_qti_xml/', views.parse_qti_xml, name='parse_qti_xml'), # Process file (AJAX)
    path('api/', include('api.urls')),
    path("export-csv/", views.export_csv, name="export_csv"),
    path('export_preview/', views.export_preview, name='export_preview')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

"""
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
"""
