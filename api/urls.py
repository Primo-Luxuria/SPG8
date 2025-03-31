from django.urls import path
from . import views


urlpatterns = [
    path('fetch_user_data/', views.fetch_user_data, name='fetch_user_data'),
    path('delete_item/', views.delete_item, name='delete_item'),
    path('update_user/', views.update_user, name='update_user')
]