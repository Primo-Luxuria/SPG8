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
    Attachment, TestQuestion, Options, Answers, UserProfile, Feedback, DynamicQuestionParameter,
    TestPart, TestSection
)
from .serializers import (
    CourseSerializer, TextbookSerializer, QuestionSerializer, 
    TestSerializer, TemplateSerializer, CoverPageSerializer, 
    AttachmentSerializer, TestSectionSerializer, TestPartSerializer
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
    print(f"Received question data from user: {user}")
    
    # Validate user profile
    try:
        user_profile = UserProfile.objects.get(user=user)
        role = user_profile.role
        print(f"User profile found: {user_profile}")
    except UserProfile.DoesNotExist:
        print("User profile not found")
        return Response({"error": "User profile not found"}, status=404)
    
    data = request.data
    questionList = data.get('questionList', {})
    
    # Handle JSON string case
    if isinstance(questionList, str):
        try:
            questionList = json.loads(questionList)
        except json.JSONDecodeError:
            print("Invalid JSON format")
            return Response({"error": "Invalid JSON format"}, status=400)
    
    print(f"Parsed question data: {questionList}")
    
    for questionID, questionData in questionList.items():
        print(f"Processing question ID: {questionID}")
        
        # Get course or textbook based on role
        if role == 'teacher':
            course_id = questionData.get('courseID')
            try:
                course = Course.objects.get(course_id=course_id)
            except Course.DoesNotExist:
                return Response({"error": f"Course not found: {course_id}"}, status=404)
            textbook = None
        else:  # publisher
            textbook_isbn = questionData.get('textbook', {}).get('isbn')
            try:
                textbook = Textbook.objects.get(isbn=textbook_isbn)
            except Textbook.DoesNotExist:
                return Response({"error": f"Textbook not found: {textbook_isbn}"}, status=404)
            course = None
        
        # Create or update the question
        question_defaults = {
            "text": questionData.get('text'),
            "answer": questionData.get('answer'),
            "qtype": questionData.get('qtype'),
            "score": questionData.get('score', 1.0),
            "directions": questionData.get('directions'),
            "reference": questionData.get('reference'),
            "eta": questionData.get('eta', 1),
            "comments": questionData.get('comments'),
            "chapter": questionData.get('chapter', 0),
            "section": questionData.get('section', 0),
            "author": user,
        }
        
        # Handle image fields if present
        if 'img' in questionData and questionData['img']:
            question_defaults['img'] = questionData['img']
        if 'ansimg' in questionData and questionData['ansimg']:
            question_defaults['ansimg'] = questionData['ansimg']
        
        # Create or update the question
        question, created = Question.objects.update_or_create(
            id=None if questionID == '0' or questionID == 'new' else questionID,
            defaults=question_defaults
        )
        
        # Set course or textbook based on role
        if role == 'teacher':
            question.course = course
            question.textbook = None
        else:  # publisher
            question.textbook = textbook
            question.course = None
        
        question.save()
        print(f"Question {'created' if created else 'updated'}: {question}")
        
        # Process options if present
        if 'options' in questionData and questionData['options']:
            # First, delete existing options to avoid duplicates
            Options.objects.filter(question=question).delete()
            
            for option_text in questionData['options']:
                option = Options.objects.create(
                    question=question,
                    text=option_text
                )
                print(f"Option created: {option}")
    
    print("Successfully saved all questions!")
    return Response({"status": "Successfully saved questions!"})

# Define this outside any other function
def process_test(test_data, user, role, is_published=False):
    """Process a single test object from the frontend data"""
    print(f"Processing test: {test_data.get('name', 'Unknown')}")
    
    # Get required fields
    course_id = test_data.get('courseID')
    template_index = test_data.get('templateIndex')
    
    # Find the course
    try:
        course = Course.objects.get(course_id=course_id)
    except Course.DoesNotExist:
        print(f"Course not found: {course_id}")
        return None
    
    # Find or create template
    template = None
    if template_index is not None:
        try:
            template = Template.objects.get(id=template_index)
        except Template.DoesNotExist:
            print(f"Template not found: {template_index}")
    
    
    # Update test fields
    test, created = Test.objects.update_or_create(
        course=course,
        name=test_data.get('name'),
        defaults={"name":test_data.get('name'),"template":template, "is_final":is_published}
    )
    test.save()
    
    # Clear existing parts and sections to rebuild
    TestPart.objects.filter(test=test).delete()
    
    # Process parts
    parts_data = test_data.get('parts', [])
    for part_data in parts_data:
        part = TestPart.objects.create(
            test=test,
            part_number=part_data.get('partNumber', 1)
        )
        
        # Process sections
        sections_data = part_data.get('sections', [])
        for section_data in sections_data:
            section = TestSection.objects.create(
                part=part,
                section_number=section_data.get('sectionNumber', 1),
                question_type=section_data.get('questionType', '')
            )
            
            # Process questions
            questions_data = section_data.get('questions', [])
            for idx, question_data in enumerate(questions_data):
                # Find or create the question
                q_id = question_data.get('id')
                try:
                    question = Question.objects.get(id=q_id)
                except Question.DoesNotExist:
                    print(f"Question {q_id} not found, skipping")
                    continue
                
                # Create test question linking
                TestQuestion.objects.update_or_create(
                    test=test,
                    question=question,
                    defaults={
                        "test":test,
                        "question":question,
                        "assigned_points":question_data.get('score', 1),
                        "order":idx,
                        "section":section}
                )
    
    return test

@api_view(['POST'])
@transaction.atomic
def save_test_data(request):
    user = request.user
    print(f"Received test data from user: {user}")
    
    # Validate user profile
    try:
        user_profile = UserProfile.objects.get(user=user)
        role = user_profile.role
        print(f"User profile found: {user_profile}")
    except UserProfile.DoesNotExist:
        print("User profile not found")
        return Response({"error": "User profile not found"}, status=404)
    
    data = request.data
    testList = data.get('testList', {})
    
    # Handle JSON string case
    if isinstance(testList, str):
        try:
            testList = json.loads(testList)
        except json.JSONDecodeError:
            print("Invalid JSON format")
            return Response({"error": "Invalid JSON format"}, status=400)
    
    print(f"Parsed test data: {testList}")
    
    # Check if testList has 'drafts' and 'published' structure or direct test IDs
    if 'drafts' in testList or 'published' in testList:
        # Original structure with drafts/published keys
        for status in ['drafts', 'published']:
            tests = testList.get(status, [])
            for test_data in tests:
                process_test(test_data, user, role, status == 'published')
    else:
        # Direct test ID structure
        for test_id, test_data in testList.items():
            is_published = test_data.get('published', False)
            process_test(test_data, user, role, is_published)
    
    print("Successfully saved all tests!")
    return Response({"status": "Successfully saved tests!"})

@api_view(['POST'])
@transaction.atomic
def save_textbook_data(request):
    user = request.user
    print(f"Received textbook data from user: {user}")
    
    # Validate user profile
    try:
        user_profile = UserProfile.objects.get(user=user)
        role = user_profile.role
        print(f"User profile found: {user_profile}")
    except UserProfile.DoesNotExist:
        print("User profile not found")
        return Response({"error": "User profile not found"}, status=404)
    
    data = request.data
    textbookList = data.get('textbookList', {})
    
    # Handle JSON string case
    if isinstance(textbookList, str):
        try:
            textbookList = json.loads(textbookList)
        except json.JSONDecodeError:
            print("Invalid JSON format")
            return Response({"error": "Invalid JSON format"}, status=400)
    
    print(f"Parsed textbook data: {textbookList}")
    
    for isbn, textbookData in textbookList.items():
        print(f"Processing textbook ISBN: {isbn}")
        
        # Create or update the textbook
        textbook, created = Textbook.objects.update_or_create(
            isbn=isbn,
            defaults={
                "title": textbookData.get('title'),
                "author": textbookData.get('author'),
                "version": textbookData.get('version'),
                "link": textbookData.get('link'),
                "publisher": user if role == 'publisher' else None,
                "published": textbookData.get('published', False)
            }
        )
        
        print(f"Textbook {'created' if created else 'updated'}: {textbook}")
    
    print("Successfully saved all textbooks!")
    return Response({"status": "Successfully saved textbooks!"})

@api_view(['POST'])
@transaction.atomic
def save_template_data(request):
    user = request.user
    print(f"Received template data from user: {user}")
    
    # Validate user profile
    try:
        user_profile = UserProfile.objects.get(user=user)
        role = user_profile.role
        print(f"User profile found: {user_profile}")
    except UserProfile.DoesNotExist:
        print("User profile not found")
        return Response({"error": "User profile not found"}, status=404)
    
    data = request.data
    templateList = data.get('templateList', {})
    
    # Handle JSON string case
    if isinstance(templateList, str):
        try:
            templateList = json.loads(templateList)
        except json.JSONDecodeError:
            print("Invalid JSON format")
            return Response({"error": "Invalid JSON format"}, status=400)
    
    print(f"Parsed template data: {templateList}")
    
    for templateName, templateData in templateList.items():
        print(f"Processing template: {templateName}")
        
        # Get course or textbook based on role
        if role == 'teacher':
            course_id = templateData.get('courseID')
            try:
                course = Course.objects.get(course_id=course_id)
            except Course.DoesNotExist:
                return Response({"error": f"Course not found: {course_id}"}, status=404)
            textbook = None
        else:  # publisher
            textbook_isbn = templateData.get('textbook', {}).get('isbn')
            try:
                textbook = Textbook.objects.get(isbn=textbook_isbn)
            except Textbook.DoesNotExist:
                return Response({"error": f"Textbook not found: {textbook_isbn}"}, status=404)
            textbook = None
        
        # Create or update the template
        template_defaults = {
            "titleFont": templateData.get('titleFont', 'Arial'),
            "titleFontSize": templateData.get('titleFontSize', 48),
            "subtitleFont": templateData.get('subtitleFont', 'Arial'),
            "subtitleFontSize": templateData.get('subtitleFontSize', 24),
            "bodyFont": templateData.get('bodyFont', 'Arial'),
            "bodyFontSize": templateData.get('bodyFontSize', 12),
            "pageNumbersInHeader": templateData.get('pageNumbersInHeader', False),
            "pageNumbersInFooter": templateData.get('pageNumbersInFooter', False),
            "headerText": templateData.get('headerText'),
            "footerText": templateData.get('footerText'),
            "coverPage": templateData.get('coverPageType', 0),
            "part_structure": templateData.get('partStructure')  # Add this line
        }
        
        # Create or update the template
        template, created = Template.objects.update_or_create(
            name=templateName,
            defaults=template_defaults
        )
        
        # Set course or textbook based on role
        if role == 'teacher':
            template.course = course
            template.textbook = None
        else:  # publisher
            template.textbook = textbook
            template.course = None
        
        template.save()
        print(f"Template {'created' if created else 'updated'}: {template}")
    
    print("Successfully saved all templates!")
    return Response({"status": "Successfully saved templates!"})


@api_view(['POST'])
@transaction.atomic
def save_cpage_data(request):
    user = request.user
    print(f"Received cover page data from user: {user}")
    
    # Validate user profile
    try:
        user_profile = UserProfile.objects.get(user=user)
        role = user_profile.role
        print(f"User profile found: {user_profile}")
    except UserProfile.DoesNotExist:
        print("User profile not found")
        return Response({"error": "User profile not found"}, status=404)
    
    data = request.data
    cpageList = data.get('cpageList', {})
    
    # Handle JSON string case
    if isinstance(cpageList, str):
        try:
            cpageList = json.loads(cpageList)
        except json.JSONDecodeError:
            print("Invalid JSON format")
            return Response({"error": "Invalid JSON format"}, status=400)
    
    print(f"Parsed cover page data: {cpageList}")
    
    for cpageID, cpageData in cpageList.items():
        print(f"Processing cover page ID: {cpageID}")
        id = '';
        # Get course or textbook based on role
        if role == 'teacher':
            newid = cpageData.get('courseID')
            try:
                course = Course.objects.get(course_id=newid)
            except Course.DoesNotExist:
                return Response({"error": f"Course not found: {newid}"}, status=404)
            textbook = None
        else:  # publisher
            newid = cpageData.get('textbook', {}).get('isbn')
            try:
                textbook = Textbook.objects.get(isbn=newid)
            except Textbook.DoesNotExist:
                return Response({"error": f"Textbook not found: {newid}"}, status=404)
            course = None
        
        # Parse date if present
        test_date = None
        if cpageData.get('date'):
            try:
                test_date = datetime.strptime(cpageData.get('date'), '%Y-%m-%d').date()
            except ValueError:
                print(f"Invalid date format: {cpageData.get('date')}")
                test_date = datetime.now().date()
        
        # Create or update the cover page
        cpage_defaults = {
            "name": cpageData.get('name'),
            "testNum": cpageData.get('testNum'),
            "date": test_date or datetime.now().date(),
            "file": cpageData.get('file', ''),
            "showFilename": cpageData.get('showFilename', False),
            "blank": cpageData.get('blank', 'TL'),
            "instructions": cpageData.get('instructions'),
            "published": cpageData.get('published', False)
        }
        
        if role == 'teacher':
            # Create or update the cover page
            cpage, created = CoverPage.objects.update_or_create(
            course=course,
            name=cpage_defaults['name'],
            defaults=cpage_defaults
            )
        else:
            # Create or update the cover page
            cpage, created = CoverPage.objects.update_or_create(
            textbook=textbook,
            name=cpage_defaults['name'],
            defaults=cpage_defaults
            )
        
        # Set course or textbook based on role
        if role == 'teacher':
            cpage.course = course
            cpage.textbook = None
        else:  # publisher
            cpage.textbook = textbook
            cpage.course = None
        
        cpage.save()
        print(f"Cover page {'created' if created else 'updated'}: {cpage}")
    
    print("Successfully saved all cover pages!")
    return Response({"status": "Successfully saved cover pages!"})