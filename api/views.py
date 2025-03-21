from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from django.db import transaction

from welcome.models import (
    Course, Book, Question, Test, Template, CoverPage, 
    Attachment, TestQuestion, AnswerOption, MatchingOption, UserProfile, Feedback
)
from .serializers import (
    CourseSerializer, BookSerializer, QuestionSerializer, 
    TestSerializer, TemplateSerializer, CoverPageSerializer, 
    AttachmentSerializer
)

"""
GET Methods
"""
@api_view(['GET']) 
def load_data(request):
    user = request.user
    try:
        user_profile = UserProfile.objects.get(user=user)
        role = user_profile.role
    except UserProfile.DoesNotExist:
        return Response({"error": "User profile not found"}, status=404)
    
    if role == 'teacher':
        # Get courses associated with the user
        courses = Course.objects.filter(teachers=user)
        data = {"courseList": []}
        for course in courses:
            course_data = {
                "course": CourseSerializer(course).data,
                "questionList": get_questionlist(course, "teacher"),
                "testList": get_testlist(course, "teacher"),
                "templateList": get_templatelist(course, "teacher"),
                "attachmentList": get_attachmentlist(course, "teacher"),
                "coverpageList": get_coverpagelist(course, "teacher"),
            }
        data["courseList"].append(course_data)
    elif role == 'publisher':
        # This code is actually basically the same
        books = Book.objects.filter(publisher=user)
        data = {"textbookList": []}
        for book in books:
            book_data = {
                "book": BookSerializer(book).data,
                "questionList": get_resource_list(resource_type, parent, role),
                "testList": get_resource_list(resource_type, parent, role),
                "templateList": get_resource_list(resource_type, parent, role),
                "attachmentList": get_resource_list(resource_type, parent, role),
                "coverpageList": get_resource_list(resource_type, parent, role),
            }
        data["textbookList"].append(book_data)

    return Response(data) 

@api_view(['GET'])
# Replace repetitive get_*list functions with a single function
def get_resource_list(resource_type, parent, role):
    """Generic function to get resources by type"""
    model_map = {
        'question': Question,
        'test': Test,
        'template': Template,
        'attachment': Attachment,
        'coverpage': CoverPage
    }
    serializer_map = {
        'question': QuestionSerializer,
        'test': TestSerializer,
        'template': TemplateSerializer,
        'attachment': AttachmentSerializer,
        'coverpage': CoverPageSerializer
    }
    
    filter_field = 'course' if role == 'teacher' else 'book'
    filter_params = {filter_field: parent}
    
    model = model_map[resource_type]
    serializer_class = serializer_map[resource_type]
    
    resources = model.objects.filter(**filter_params)
    serializer = serializer_class(resources, many=True)
    return serializer.data

@api_view(['GET'])
def get_test_feedbacklist(test, role):
    pass # see below

@api_view(['GET'])
def get_question_feedbacklist(question, role):
    feedback = Feedback.objects.filter(question=question)
    #serializer for feedback here
    return feedback#_serializer.data 

@api_view(['GET'])
def get_test_questionlist(test, role):
    pass 




"""
POST Methods
"""
@api_view(['POST'])
@transaction.atomic # If saving fails, we want to rollback changes and not poison our data
def save_data(request):
    pass