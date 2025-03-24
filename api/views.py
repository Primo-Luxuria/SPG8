from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from django.db import transaction
from django.http import JsonResponse

from welcome.models import (
    Course, Textbook, Question, Test, Template, CoverPage, 
    Attachment, TestQuestion, Options, Answers, UserProfile, Feedback, DynamicQuestionParameter
)
from .serializers import (
    CourseSerializer, TextbookSerializer, QuestionSerializer, 
    TestSerializer, TemplateSerializer, CoverPageSerializer, 
    AttachmentSerializer
)

"""
GET Methods
"""
@api_view(['GET']) 
def load_data(request):
    # Check if request has a user
    if not request.user or not request.user.is_authenticated:
        return Response({"error": "Authentication required"}, status=401)

    try:
        # Try to get user profile
        user = request.user
        try:
            user_profile = UserProfile.objects.get(user=user)
            role = user_profile.role
        except UserProfile.DoesNotExist:
            return Response({"error": "User profile not found"}, status=404)
        
        # Initialize data dictionary based on role
        if role == 'teacher':
            data = {"courseList": []}
            # Get courses associated with the user
            courses = Course.objects.filter(teachers=user)
            if not courses.exists():
                return Response({"message": "No courses available for this teacher.", "courseList": []}, status=200)
                
            for course in courses:
                try:
                    course_data = {
                        "course": CourseSerializer(course).data,
                        "questionList": get_resource_list('question', course, 'teacher'),
                        "testList": get_resource_list('test', course, 'teacher'),
                        "templateList": get_resource_list('template', course, 'teacher'),
                        "attachmentList": get_resource_list('attachment', course, 'teacher'),
                        "coverpageList": get_resource_list('coverpage', course, 'teacher'),
                    }
                    data["courseList"].append(course_data)
                except Exception as e:
                    # If processing a specific course fails, print the error but continue with others
                    print(f"Error processing course {course.id}: {str(e)}")
                    continue
        
        elif role == 'publisher':
            data = {"textbookList": []}
            try:
                books = Textbook.objects.filter(publisher=user)
                if not books.exists():
                    return Response({"message": "No textbooks available for this publisher.", "textbookList": []}, status=200)
                    
                for book in books:
                    try:
                        book_data = {
                            "book": TextbookSerializer(book).data,
                            "questionList": get_resource_list('question', book, 'publisher'),
                            "testList": get_resource_list('test', book, 'publisher'),
                            "templateList": get_resource_list('template', book, 'publisher'),
                            "attachmentList": get_resource_list('attachment', book, 'publisher'),
                            "coverpageList": get_resource_list('coverpage', book, 'publisher'),
                        }
                        data["textbookList"].append(book_data)
                    except Exception as e:
                        # If processing a specific book fails, print the error but continue with others
                        print(f"Error processing textbook {book.id}: {str(e)}")
                        continue
            except Exception as e:
                return Response({"error": f"Error retrieving textbooks: {str(e)}"}, status=500)
        else:
            return Response({"error": f"Unsupported role: {role}"}, status=400)
            
        return Response(data)
        
    except Exception as e:
        # Catch-all for any other unexpected errors
        print(f"Unexpected error in load_data: {str(e)}")
        return Response({"error": "An unexpected error occurred"}, status=500)

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

def get_test_feedbacklist(test, role):
    pass # see below

def get_question_feedbacklist(question, role):
    feedback = Feedback.objects.filter(question=question)
    #serializer for feedback here
    return feedback#_serializer.data 


def get_test_questionlist(test, role):
    pass 





"""
POST Methods
"""

import json
from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response
from datetime import datetime

import json
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.db import transaction
from welcome.models import Course, Textbook, UserProfile


@api_view(['POST'])
@transaction.atomic  # Ensures data consistency
def save_course_data(request):
    user = request.user
    print(f"Received course data from user: {user}")

    # Validate user profile
    try:
        user_profile = UserProfile.objects.get(user=user)
        print(f"User profile found: {user_profile}")
    except UserProfile.DoesNotExist:
        print("User profile not found")
        return Response({"error": "User profile not found"}, status=404)

    data = request.data
    courseList = data.get('courseList', {})

    # Handle JSON string case
    if isinstance(courseList, str):
        try:
            courseList = json.loads(courseList)
        except json.JSONDecodeError:
            print("Invalid JSON format")
            return Response({"error": "Invalid JSON format"}, status=400)

    print(f"Parsed course data: {courseList}")

    for courseID, courseData in courseList.items():
        print(f"Processing course ID: {courseID}")
        textbook_data = courseData.get('textbook')

        if textbook_data:
            isbn = textbook_data.get('isbn')
            if isbn:
                textbook, created = Textbook.objects.update_or_create(
                    isbn=isbn,
                    defaults={
                        "title": textbook_data.get('title'),
                        "author": textbook_data.get('author'),
                        "version": textbook_data.get('version'),
                        "link": textbook_data.get('link')
                    }
                )
                print(f"Textbook {'created' if created else 'updated'}: {textbook}")
            else:
                print("Textbook ISBN is missing")
                return Response({"error": "Textbook ISBN is missing"}, status=400)
        else:
            textbook = None
            print("No textbook found for this course")

        newDefaults = {
            "name": courseData.get('name'),
            "crn": courseData.get('crn'),
            "sem": courseData.get('sem'),
            "published": courseData.get('published')
        }

        course, created = Course.objects.update_or_create(
            course_id=courseID,
            defaults=newDefaults
        )

        if textbook:
            course.textbook = textbook

        # Assign teacher to the course
        course.teachers.add(user)  
        print(f"User is {user.id}")
        course.save()

        print(f"Course {'created' if created else 'updated'}: {course}")

    print("Successfully saved all courses!")
    return Response({"status": "Successfully saved course!"})


    
@api_view(['POST'])
@transaction.atomic
def save_question_data(request):
    user = request.user
    try:
        user_profile = UserProfile.objects.get(user=user)
        role = user_profile.role
    except UserProfile.DoesNotExist:
        return Response({"error": "User profile not found"}, status=404)
    data = request.data
    return Response({"status": "Successfully saved question!"})

@api_view(['POST'])
@transaction.atomic
def save_test_data(request):
    user = request.user
    try:
        user_profile = UserProfile.objects.get(user=user)
        role = user_profile.role
    except UserProfile.DoesNotExist:
        return Response({"error": "User profile not found"}, status=404)
    data = request.data
    return Response({"status": "Successfully saved test!"})

@api_view(['POST'])
@transaction.atomic
def save_textbook_data(request):
    user = request.user
    try:
        user_profile = UserProfile.objects.get(user=user)
        role = user_profile.role
    except UserProfile.DoesNotExist:
        return Response({"error": "User profile not found"}, status=404)
    data = request.data
    return Response({"status": "Successfully saved textbook!"})


@api_view(['POST'])
@transaction.atomic
def save_template_data(request):
    user = request.user
    try:
        user_profile = UserProfile.objects.get(user=user)
        role = user_profile.role
    except UserProfile.DoesNotExist:
        return Response({"error": "User profile not found"}, status=404)
    data = request.data
    return Response({"status": "Successfully saved template!"})

@api_view(['POST'])
@transaction.atomic
def save_cpage_data(request):
    user = request.user
    try:
        user_profile = UserProfile.objects.get(user=user)
        role = user_profile.role
    except UserProfile.DoesNotExist:
        return Response({"error": "User profile not found"}, status=404)
    data = request.data
    return Response({"status": "Successfully saved cover page!"})

