from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from django.db import transaction
from django.http import JsonResponse

from welcome.models import (
    Course, Book, Question, Test, Template, CoverPage, 
    Attachment, TestQuestion, AnswerOption, MatchingOption, UserProfile, Feedback, DynamicQuestionParameter
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

    data = {"courseList": []}
    courses = Course.objects.all()  
    if not courses.exists():  # Check if there are no courses
        return JsonResponse({"message": "No courses available yet.", "courseList": []}, status=200)


    user = request.user
    try:
        user_profile = UserProfile.objects.get(user=user)
        role = user_profile.role
    except UserProfile.DoesNotExist:
        return Response({"error": "User profile not found"}, status=404)
    
    if role == 'teacher':
        # Get courses associated with the user
        courses = Course.objects.filter(teachers=user)
        for course in courses:
            course_data = {
                "course": CourseSerializer(course).data,
                "questionList": get_resource_list('question', course, 'teacher'),
                "testList": get_resource_list('test', course, 'teacher'),
                "templateList": get_resource_list('template', course, 'teacher'),
                "attachmentList": get_resource_list('attachment', course, 'teacher'),
                "coverpageList": get_resource_list('coverpage', course, 'teacher'),
            }
        data["courseList"].append(course_data)
    elif role == 'publisher':
        # This code is actually basically the same
        books = Book.objects.filter(publisher=user)
        data = {"textbookList": []}
        for book in books:
            book_data = {
                "book": BookSerializer(book).data,
                "questionList": get_resource_list('question', book, 'publisher'),
                "testList": get_resource_list('test', book, 'publisher'),
                "templateList": get_resource_list('template', book, 'publisher'),
                "attachmentList": get_resource_list('attachment', book, 'publisher'),
                "coverpageList": get_resource_list('coverpage', book, 'publisher'),
            }
        data["textbookList"].append(book_data)

    return Response(data) 

@api_view(['GET'])
# Replaced repetitive get_*list functions with a single function
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

import json
from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response
from datetime import datetime

@api_view(['POST'])
@transaction.atomic  # If saving fails, we want to rollback changes
def save_data(request):
    user = request.user
    try:
        user_profile = UserProfile.objects.get(user=user)
        role = user_profile.role
    except UserProfile.DoesNotExist:
        return Response({"error": "User profile not found"}, status=404)
    
    # Get the data from the request
    data = request.data
    
    if role == 'teacher':  
        # Parse the stringified JSON data
        master_question_list = json.loads(data.get('masterQuestionList', '{}'))
        master_test_list = json.loads(data.get('masterTestList', '{}'))
        master_template_list = json.loads(data.get('masterTemplateList', '{}'))
        master_attachment_list = json.loads(data.get('masterAttachmentList', '{}'))
        course_list = json.loads(data.get('courseList', '{}'))
        master_cover_page_list = json.loads(data.get('masterCoverPageList', '{}'))
        
        # Process Course data
        for course_id, course_data in course_list.items():
            course, created = Course.objects.update_or_create(
                id=int(course_id) if course_id.isdigit() else None,
                defaults={
                    'user': user,
                    'course_code': course_data.get('id', 'CS499'),
                    'course_name': course_data.get('name', 'Untitled Course'),
                    'course_crn': course_data.get('crn', '0000'),
                    'course_semester': course_data.get('sem', 'Fall 2021'),
                }
            )
            
            # Set textbook if provided
            textbook_data = course_data.get('textbook')
            if textbook_data and isinstance(textbook_data, dict):
                textbook_isbn = textbook_data.get('isbn')
                if textbook_isbn:
                    try:
                        # First see if we already processed this textbook
                        book = Book.objects.get(isbn=textbook_isbn)
                    except Book.DoesNotExist:
                        # If not, create the textbook
                        book = Book.objects.create(
                            title=textbook_data.get('title', 'Untitled Book'),
                            author=textbook_data.get('author'),
                            version=textbook_data.get('version'),
                            isbn=textbook_isbn,
                            link=textbook_data.get('link')
                        )
                    
                    # Associate the book with the course
                    course.book = book
                    course.save()
                    
            # Handle teachers for the course
            if not course.teachers.filter(id=user.id).exists():
                course.teachers.add(user)
        
        # Process Question data - questions are organized by course and question type
        for course_id, question_types in master_question_list.items():
            if not isinstance(question_types, dict):
                continue
                
            try:
                course = Course.objects.get(id=int(course_id)) if course_id.isdigit() else None
            except Course.DoesNotExist:
                continue
                
            # Iterate through question types (tf, mc, sa, etc.)
            for q_type, questions in question_types.items():
                if not isinstance(questions, list):
                    continue
                    
                for question_data in questions:
                    if not isinstance(question_data, dict) or not question_data.get('text'):
                        continue
                        
                    question_id = question_data.get('id')
                    
                    # Create or update the question
                    question, created = Question.objects.update_or_create(
                        id=int(question_id) if question_id and str(question_id).isdigit() else None,
                        defaults={
                            'course': course,
                            'question_type': question_data.get('qtype', 'SA'),
                            'question_text': question_data.get('text', 'Question text.'),
                            'default_points': float(question_data.get('score', 1.0)),
                            'estimated_time': int(question_data.get('eta', 1)),
                            'instructions_for_grading': question_data.get('directions'),
                            'references': question_data.get('reference'),
                            'instructor_comment': question_data.get('comments'),
                            'chapter': int(question_data.get('chapter', 0)),
                            'section': int(question_data.get('section', 0)),
                            'correct_answer': question_data.get('answer'),
                            'embedded_graphic': question_data.get('img'),
                            'correct_answer_graphic': question_data.get('ansimg'),
                            'include_formula': bool(question_data.get('include_formula', False)),
                            'owner': user,
                        }
                    )
                
                    # Process answer options for multiple choice, multiple selection questions
                    if question.question_type in ['MC', 'MS'] and 'options' in question_data:
                        # First clear existing options to avoid duplicates
                        AnswerOption.objects.filter(question=question).delete()
                        
                        for option_data in question_data['options']:
                            if not isinstance(option_data, dict):
                                continue
                                
                            # Check if option has the required text field
                            if 'text' not in option_data:
                                continue
                                
                            AnswerOption.objects.create(
                                question=question,
                                text=option_data.get('text', ''),
                                is_correct=bool(option_data.get('correct', False)),
                                response_feedback_text=option_data.get('feedback', '')
                                # Note: answer_graphic and response_feedback_graphic are missing from the data
                                # but are defined in the model. Could add these if frontend provides them.
                            )
                
                    # Process matching options for matching questions
                    if question.question_type == 'MA' and 'prompts' in question_data and 'options' in question_data:
                        # First clear existing matching options to avoid duplicates
                        MatchingOption.objects.filter(question=question).delete()
                        #need to fix this
                        prompts = question_data.get('prompts', [])
                        options = question_data.get('options', [])
                        
                        # Match up prompts and options for matching questions
                        for i, prompt in enumerate(prompts):
                            if isinstance(prompt, dict) and i < len(options) and isinstance(options[i], dict):
                                # Check if prompt and option have the required text fields
                                if 'text' not in prompt or 'text' not in options[i]:
                                    continue
                                    
                                MatchingOption.objects.create(
                                    question=question,
                                    option_text=prompt.get('text', ''),
                                    match_text=options[i].get('text', '')
                                )
                
                    # Process dynamic parameters for dynamic questions
                    if question.question_type == 'DY' and 'dynamicParams' in question_data:
                        dynamic_params = question_data['dynamicParams']
                        if isinstance(dynamic_params, dict):
                            # Ensure the required fields are present or provide defaults
                            formula = dynamic_params.get('formula', '')
                            try:
                                range_min = float(dynamic_params.get('min', 0))
                                range_max = float(dynamic_params.get('max', 100))
                            except (ValueError, TypeError):
                                # Handle case where min/max are not valid floats
                                range_min = 0
                                range_max = 100
                                
                            additional_params = dynamic_params.get('additionalParams', {})
                            # Ensure additional_params is JSON serializable
                            if not isinstance(additional_params, (dict, list)):
                                additional_params = {}
                                
                            DynamicQuestionParameter.objects.update_or_create(
                                question=question,
                                defaults={
                                    'formula': formula,
                                    'range_min': range_min,
                                    'range_max': range_max,
                                    'additional_params': additional_params
                                }
                            )
        
        # Process Template data
        for course_id, course_templates in master_template_list.items():
            # Skip special properties or non-list items
            if not isinstance(course_templates, list) or course_id == "bonusQuestions":
                continue
                
            try:
                course = Course.objects.get(id=int(course_id)) if course_id.isdigit() else None
            except Course.DoesNotExist:
                continue
                
            for template_data in course_templates:
                if not isinstance(template_data, dict):
                    continue
                    
                template_id = template_data.get('id')
                Template.objects.update_or_create(
                    id=int(template_id) if template_id and str(template_id).isdigit() else None,
                    defaults={
                        'course': course,
                        'name': template_data.get('name', 'Untitled Template'),
                        'font_name': template_data.get('bodyFont', 'Arial'),
                        'font_size': int(template_data.get('bodyFontSize', 12)),
                        'header_text': template_data.get('headerText', ''),
                        'footer_text': template_data.get('footerText', '')
                    }
                )
        
        # Process Cover Page data
        for course_id, cover_pages in master_cover_page_list.items():
            if not isinstance(cover_pages, list):
                continue
                
            try:
                course = Course.objects.get(id=int(course_id)) if course_id.isdigit() else None
            except Course.DoesNotExist:
                continue
                
            for cover_page_data in cover_pages:
                if not isinstance(cover_page_data, dict):
                    continue
                    
                cover_page_id = cover_page_data.get('id')
                
                # Parse date if provided
                test_date = None
                date_str = cover_page_data.get('date')
                if date_str:
                    try:
                        # Assuming date format is YYYY-MM-DD
                        test_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except (ValueError, TypeError):
                        pass
                
                # Only create cover page if we have the required test_date
                if test_date:
                    CoverPage.objects.update_or_create(
                        id=int(cover_page_id) if cover_page_id and str(cover_page_id).isdigit() else None,
                        defaults={
                            'course': course,
                            'cover_page_name': cover_page_data.get('name', 'Untitled Cover Page'),
                            'test_number': cover_page_data.get('testNum', ''),
                            'test_date': test_date,
                            'test_filename': cover_page_data.get('file', ''),
                            'filename_present': bool(cover_page_data.get('showFilename', False)),
                            'student_name_location': cover_page_data.get('blank', 'top_left'),
                            'grading_instructions_for_key': cover_page_data.get('instructions', '')
                        }
                    )
                else:
                    # Log warning about missing test_date
                    print(f"Warning: Could not create cover page, missing test_date for cover page ID: {cover_page_id}")
        
        # Process Attachment data
        for course_id, attachments in master_attachment_list.items():
            if not isinstance(attachments, list):
                continue
                
            try:
                course = Course.objects.get(id=int(course_id)) if course_id.isdigit() else None
            except Course.DoesNotExist:
                continue
                
            for attachment_data in attachments:
                if not isinstance(attachment_data, dict) or not attachment_data.get('file'):
                    continue
                    
                attachment_id = attachment_data.get('id')
                Attachment.objects.update_or_create(
                    id=int(attachment_id) if attachment_id and str(attachment_id).isdigit() else None,
                    defaults={
                        'course': course,
                        'file': attachment_data.get('file')
                    }
                )
        
        # Process Test data
        for course_id, test_types in master_test_list.items():
            if not isinstance(test_types, dict):
                continue
                
            try:
                course = Course.objects.get(id=int(course_id)) if course_id.isdigit() else None
            except Course.DoesNotExist:
                continue
                
            # Iterate through test types (drafts, published)
            for test_type, tests in test_types.items():
                if not isinstance(tests, list):
                    continue
                    
                for test_data in tests:
                    if not isinstance(test_data, dict):
                        continue
                        
                    test_id = test_data.get('id')
                    
                    # Get template if specified
                    template = None
                    template_index = test_data.get('templateIndex')
                    if template_index and str(template_index).isdigit():
                        try:
                            template = Template.objects.get(id=int(template_index))
                        except Template.DoesNotExist:
                            pass
                    
                    # Check if we have a date in the request data
                    test_date = None
                    date_str = test_data.get('date')
                    if date_str:
                        try:
                            # Assuming date format is YYYY-MM-DD
                            test_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                        except (ValueError, TypeError):
                            pass
                    
                    # Set is_final based on test_type
                    is_final = test_type == 'published'
                    
                    test, created = Test.objects.update_or_create(
                        id=int(test_id) if test_id and str(test_id).isdigit() else None,
                        defaults={
                            'course': course,
                            'title': test_data.get('name', 'Untitled Test'),
                            'template': template,
                            'date': test_date,
                            'filename': test_data.get('filename'),
                            'is_final': is_final,
                            'test_number': test_data.get('testNum'),
                            'cover_instructions': test_data.get('instructions')
                        }
                    )
                
                    # Handle attachments if needed
                    if 'attachments' in test_data and isinstance(test_data['attachments'], list):
                        attachment_ids = []
                        for attachment_data in test_data['attachments']:
                            if isinstance(attachment_data, dict):
                                attachment_id = attachment_data.get('id')
                                if attachment_id and str(attachment_id).isdigit():
                                    attachment_ids.append(int(attachment_id))
                        
                        attachments = Attachment.objects.filter(id__in=attachment_ids)
                        test.attachments.set(attachments)
                
                    # Process test structure (parts and sections)
                    if 'parts' in test_data and isinstance(test_data['parts'], list):
                        # First clear existing test questions to rebuild them
                        TestQuestion.objects.filter(test=test).delete()
                        
                        order_counter = 1
                        
                        for part_index, part_data in enumerate(test_data['parts']):
                            if not isinstance(part_data, dict) or 'sections' not in part_data:
                                continue
                                
                            if not isinstance(part_data['sections'], list):
                                continue
                                
                            for section_index, section_data in enumerate(part_data['sections']):
                                if not isinstance(section_data, dict) or 'questions' not in section_data:
                                    continue
                                    
                                question_type = section_data.get('questionType', '')
                                
                                if not isinstance(section_data['questions'], list):
                                    continue
                                    
                                for question_data in section_data['questions']:
                                    if not isinstance(question_data, dict):
                                        continue
                                        
                                    question_id = question_data.get('id')
                                    if not question_id or not str(question_id).isdigit():
                                        continue
                                    
                                    try:
                                        question = Question.objects.get(id=int(question_id))
                                    except Question.DoesNotExist:
                                        continue
                                    
                                    # Calculate part and section numbers for special instructions
                                    part_number = part_index + 1
                                    section_number = section_index + 1
                                    special_instructions = f"Part {part_number}, Section {section_number}"
                                    
                                    # Get points and ensure it's a valid float
                                    try:
                                        assigned_points = float(question_data.get('points', question.default_points))
                                    except (ValueError, TypeError):
                                        assigned_points = question.default_points
                                    
                                    TestQuestion.objects.create(
                                        test=test,
                                        question=question,
                                        assigned_points=assigned_points,
                                        order=order_counter,
                                        randomize=bool(question_data.get('randomize', False)),
                                        special_instructions=special_instructions
                                    )
                                    order_counter += 1
    
    elif role == 'publisher':
        # Parse publisher data
        master_question_list = json.loads(data.get('masterQuestionList', '{}'))
        master_test_list = json.loads(data.get('masterTestList', '{}'))
        master_template_list = json.loads(data.get('masterTemplateList', '{}'))
        master_attachment_list = json.loads(data.get('masterAttachmentList', '{}'))
        master_cover_page_list = json.loads(data.get('masterCoverPageList', '{}'))
        textbook_list = json.loads(data.get('masterTextbookList', '{}'))
        
        # Process publisher's books
        for isbn, book_data in textbook_list.items():
            if not isinstance(book_data, dict):
                continue
                
            book, created = Book.objects.update_or_create(
                isbn=isbn,
                defaults={
                    'title': book_data.get('title', 'Untitled Book'),
                    'author': book_data.get('author', ''),
                    'version': book_data.get('version', ''),
                    'link': book_data.get('link', ''),
                    'publisher': user
                }
            )
            
            # Process questions for this book
            if isbn in master_question_list and isinstance(master_question_list[isbn], dict):
                for q_type, questions in master_question_list[isbn].items():
                    if not isinstance(questions, list):
                        continue
                        
                    for question_data in questions:
                        if not isinstance(question_data, dict) or not question_data.get('text'):
                            continue
                            
                        question_id = question_data.get('id')
                        
                        # Create or update the question
                        question, created = Question.objects.update_or_create(
                            id=int(question_id) if question_id and str(question_id).isdigit() else None,
                            defaults={
                                'book': book,  # Associate with book instead of course for publisher
                                'question_type': question_data.get('qtype', 'SA'),
                                'question_text': question_data.get('text', 'Question text.'),
                                'default_points': float(question_data.get('score', 1.0)),
                                'estimated_time': int(question_data.get('eta', 1)),
                                'instructions_for_grading': question_data.get('directions'),
                                'references': question_data.get('reference'),
                                'instructor_comment': question_data.get('comments'),
                                'chapter': int(question_data.get('chapter', 1)),  # Ensure non-zero for publishers
                                'section': int(question_data.get('section', 0)),
                                'correct_answer': question_data.get('answer'),
                                'embedded_graphic': question_data.get('img'),
                                'correct_answer_graphic': question_data.get('ansimg'),
                                'include_formula': bool(question_data.get('include_formula', False)),
                                'owner': user,
                            }
                        )
                        
                        # Process answer options, matching options, and dynamic parameters
                        # (Similar to the teacher code but with book instead of course)
                        # These sections would follow the same pattern as above
            
            # Process templates for this book
            if isbn in master_template_list and isinstance(master_template_list[isbn], list):
                for template_data in master_template_list[isbn]:
                    if not isinstance(template_data, dict):
                        continue
                        
                    template_id = template_data.get('id')
                    Template.objects.update_or_create(
                        id=int(template_id) if template_id and str(template_id).isdigit() else None,
                        defaults={
                            'book': book,  # Associate with book instead of course
                            'name': template_data.get('name', 'Untitled Template'),
                            'font_name': template_data.get('bodyFont', 'Arial'),
                            'font_size': int(template_data.get('bodyFontSize', 12)),
                            'header_text': template_data.get('headerText', ''),
                            'footer_text': template_data.get('footerText', '')
                        }
                    )
            
            # Process tests for this book
            if isbn in master_test_list and isinstance(master_test_list[isbn], dict):
                for test_type, tests in master_test_list[isbn].items():
                    if not isinstance(tests, list):
                        continue
                        
                    for test_data in tests:
                        if not isinstance(test_data, dict):
                            continue
                            
                        # Similar pattern to teacher tests but with book association
                        # This would be similar to the test processing code above
    
    elif role == 'webmaster':
        # Process webmaster-specific data (if any)
        # Currently no specific handling for webmaster role
        pass
    
    return Response({"status": "success"})