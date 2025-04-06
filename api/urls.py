from django.urls import path
from . import views


urlpatterns = [
    path('fetch_user_data/', views.fetch_user_data, name='fetch_user_data'),
    path('delete_item/', views.delete_item, name='delete_item'),
    path('update_user/', views.update_user, name='update_user'),
    path('save_course/', views.save_course, name='save_course'),
    path('save_textbook/',views.save_textbook, name='save_textbook'),
    path('save_cpage/', views.save_cpage, name='save_cpage'),
    path('save_template/', views.save_template, name='save_template'),
    path('save_question/', views.save_question, name='save_question'),
    path('save_test/', views.save_test, name='save_test'),
    path('save_attachment/', views.save_attachment, name='save_attachment')
]