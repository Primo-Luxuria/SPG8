from django.urls import path
from . import views


urlpatterns = [
    path('load_data/', views.load_data, name='load_data'),
    path('save_data/question/', views.save_question_data, name='save_question_data'),
    path('save_data/test/', views.save_test_data, name='save_test_data'),
    path('save_data/template/', views.save_template_data, name='save_template_data'),
    path('save_data/cpage/', views.save_cpage_data, name='save_cpage_data'),
    path('save_data/course/', views.save_course_data, name='save_course_data'),
    path('save_data/textbook/', views.save_textbook_data, name='save_textbook_data'),
]