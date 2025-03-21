from django.urls import path
from . import views


urlpatterns = [
    path('load_data/', views.load_data, name='load_data'),
    path('save_data/', views.save_data, name='save_data')
]