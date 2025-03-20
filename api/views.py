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
                "questionList": get_questionlist(course, "publisher"),
                "testList": get_testlist(course, "publisher"),
                "templateList": get_templatelist(course, "publisher"),
                "attachmentList": get_attachmentlist(course, "publisher"),
                "coverpageList": get_coverpagelist(course, "publisher"),
            }
        data["textbookList"].append(book_data)

    return Response(data) 

@api_view(['GET'])
def get_questionlist(input, role):
    if(role == "teacher"):
        questions = Question.objects.filter(course=input)
        question_serializer = QuestionSerializer(questions, many=True)
    else:
        questions = Question.objects.filter(book=input)
        question_serializer = QuestionSerializer(questions, many=True)
    return question_serializer.data
    

@api_view(['GET'])
def get_testlist(input, role):
    if(role == "teacher"):
        tests = Test.objects.filter(course=input)
        test_serializer = TestSerializer(tests, many=True)
    else:
        tests = Test.objects.filter(book=input)
        test_serializer = TestSerializer(tests, many=True)
    return test_serializer.data

@api_view(['GET'])
def get_templatelist(input, role):
    if(role == "teacher"):
        templates = Template.objects.filter(course=input)
        template_serializer = TemplateSerializer(templates, many=True)
    else:
        templates = Template.objects.filter(book=input)
        template_serializer = TemplateSerializer(templates, many=True)
    return template_serializer.data

@api_view(['GET'])
def get_attachmentlist(input, role):
    if(role == "teacher"):
        attachments = Attachment.objects.filter(course=input)
        attachment_serializer = AttachmentSerializer(attachments, many=True)
    else:
        attachments = Attachment.objects.filter(book=input)
        attachment_serializer = AttachmentSerializer(attachments, many=True)
    return attachment_serializer.data

@api_view(['GET'])
def get_coverpagelist(input, role):
    if(role == "teacher"):
        cpages = CoverPage.objects.filter(course=input)
        cpage_serializer = CoverPageSerializer(cpages, many=True)
    else:
        cpages = CoverPage.objects.filter(book=input)
        cpage_serializer = CoverPageSerializer(cpages, many=True)
    return cpage_serializer.data

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