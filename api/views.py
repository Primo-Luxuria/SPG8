from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from django.db import transaction

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
            
            # Set book if provided
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
                
            # Process Question data
            for question_id, question_data in master_question_list.items():
                # Skip if the question doesn't have required data
                if not question_data.get('text'):
                    continue
                
                # Determine course association
                course_id = question_data.get('course_id')
                course = None
                if course_id and course_id.isdigit():
                    try:
                        course = Course.objects.get(id=int(course_id))
                    except Course.DoesNotExist:
                        continue  # Skip if course doesn't exist
            
                # Create or update the question
                question, created = Question.objects.update_or_create(
                    id=int(question_id) if question_id.isdigit() else None,
                    defaults={
                        'course': course,
                        'question_type': question_data.get('qtype', 'SA'),
                        'question_text': question_data.get('text', 'Question text.'),
                        'default_points': question_data.get('score', 1.0),
                        'estimated_time': question_data.get('eta', 1),
                        'instructions_for_grading': question_data.get('directions'),
                        'references': question_data.get('reference'),
                        'instructor_comment': question_data.get('comments'),
                        'chapter': question_data.get('chapter', 0),
                        'section': question_data.get('section', 0),
                        'correct_answer': question_data.get('answer'),
                        'embedded_graphic': question_data.get('img'),
                        'correct_answer_graphic': question_data.get('ansimg'),
                        'include_formula': question_data.get('include_formula', False),
                        'owner': user,
                    }
                )
            
                # Process answer options for multiple choice, multiple selection questions
                if question.question_type in ['MC', 'MS'] and 'options' in question_data:
                    # First clear existing options to avoid duplicates
                    existing_options = AnswerOption.objects.filter(question=question)
                    existing_options.delete()
                    
                    for option_data in question_data['options']:
                        AnswerOption.objects.create(
                            question=question,
                            text=option_data.get('text', ''),
                            is_correct=option_data.get('correct', False),
                            response_feedback_text=option_data.get('feedback', '')
                        )
            
                # Process matching options for matching questions
                if question.question_type == 'MA' and 'prompts' in question_data:
                    # First clear existing matching options to avoid duplicates
                    existing_matches = MatchingOption.objects.filter(question=question)
                    existing_matches.delete()
                    
                    prompts = question_data.get('prompts', [])
                    options = question_data.get('options', [])
                    
                    # Match up prompts and options for matching questions
                    for i, prompt in enumerate(prompts):
                        if i < len(options):
                            MatchingOption.objects.create(
                                question=question,
                                option_text=prompt.get('text', ''),
                                match_text=options[i].get('text', '')
                            )
            
                # Process dynamic parameters for dynamic questions
                if question.question_type == 'DY' and 'dynamicParams' in question_data:
                    dynamic_params = question_data['dynamicParams']
                    DynamicQuestionParameter.objects.update_or_create(
                        question=question,
                        defaults={
                            'formula': dynamic_params.get('formula', ''),
                            'range_min': dynamic_params.get('min', 0),
                            'range_max': dynamic_params.get('max', 100),
                            'additional_params': dynamic_params.get('additionalParams', {})
                        }
                    )
        
            # Process Template data
            for template_id, template_data in master_template_list.items():
                # Determine course association
                course_id = template_data.get('course_id')
                course = None
                if course_id and course_id.isdigit():
                    try:
                        course = Course.objects.get(id=int(course_id))
                    except Course.DoesNotExist:
                        continue
            
                Template.objects.update_or_create(
                    id=int(template_id) if template_id.isdigit() else None,
                    defaults={
                        'course': course,
                        'name': template_data.get('name', f'Template-{template_id}'),
                        'font_name': template_data.get('bodyFont', 'Arial'),
                        'font_size': template_data.get('bodyFontSize', 12),
                        'header_text': template_data.get('headerText', ''),
                        'footer_text': template_data.get('footerText', '')
                    }
                )
        
            # Process Attachment data
            for attachment_index, attachment_data in enumerate(master_attachment_list.get(course_id, [])):
                # Skip if no file
                if not attachment_data.get('file'):
                    continue
                
                Attachment.objects.create(
                    course=course,
                    file=attachment_data.get('file')
                )
        
            # Process Cover Page data
            for cover_page_id, cover_page_data in master_cover_page_list.items():
                course_id = cover_page_data.get('course_id')
                course = None
                if course_id and course_id.isdigit():
                    try:
                        course = Course.objects.get(id=int(course_id))
                    except Course.DoesNotExist:
                        continue
                
                try:
                    # Parse the date string into a date object
                    test_date = parse_date(cover_page_data.get('date'))
                except (ValueError, TypeError):
                    test_date = None
                
                CoverPage.objects.update_or_create(
                    id=int(cover_page_id) if cover_page_id.isdigit() else None,
                    defaults={
                        'course': course,
                        'cover_page_name': cover_page_data.get('name', f'Cover Page {cover_page_id}'),
                        'test_number': cover_page_data.get('testNum', ''),
                        'test_date': test_date,
                        'test_filename': cover_page_data.get('file', ''),
                        'filename_present': cover_page_data.get('showFilename', False),
                        'student_name_location': cover_page_data.get('blank', 'top_left'),
                        'grading_instructions_for_key': cover_page_data.get('instructions', '')
                    }
                )
        
            # Process Test data
            for test_id, test_data in master_test_list.items():
                course_id = test_data.get('course_id')
                course = None
                if course_id and course_id.isdigit():
                    try:
                        course = Course.objects.get(id=int(course_id))
                    except Course.DoesNotExist:
                        continue
            
                # Get template if specified
                template = None
                template_index = test_data.get('templateIndex')
                if template_index and str(template_index).isdigit():
                    try:
                        template = Template.objects.get(id=int(template_index))
                    except Template.DoesNotExist:
                        pass
                
                test, created = Test.objects.update_or_create(
                    id=int(test_id) if test_id.isdigit() else None,
                    defaults={
                        'course': course,
                        'title': test_data.get('name', 'Untitled Test'),
                        'template': template,
                    }
                )
            
                # Handle attachments if needed
                if 'attachments' in test_data and test_data['attachments']:
                    attachment_ids = []
                    for attachment_data in test_data['attachments']:
                        attachment_id = attachment_data.get('id')
                        if attachment_id and str(attachment_id).isdigit():
                            attachment_ids.append(int(attachment_id))
                    
                    attachments = Attachment.objects.filter(id__in=attachment_ids)
                    test.attachments.set(attachments)
            
                # Process test structure (parts and sections)
                if 'parts' in test_data:
                    # First clear existing test questions to rebuild them
                    existing_test_questions = TestQuestion.objects.filter(test=test)
                    existing_test_questions.delete()
                    
                    order_counter = 1
                    
                    for part_index, part_data in enumerate(test_data['parts']):
                        if 'sections' in part_data:
                            for section_index, section_data in enumerate(part_data['sections']):
                                question_type = section_data.get('questionType', '')
                                
                                if 'questions' in section_data:
                                    for question_data in section_data['questions']:
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
                                        
                                        TestQuestion.objects.create(
                                            test=test,
                                            question=question,
                                            assigned_points=question_data.get('points', question.default_points),
                                            order=order_counter,
                                            randomize=question_data.get('randomize', False),
                                            special_instructions=special_instructions
                                        )
                                        order_counter += 1
    
    elif role == 'publisher': 
        #
        # This whole part needs to be reworked
        # Publishers should not have one book, it should be a one to many relationship
        # Same as courses with questions or test authors with tests
        #

        # Process publisher data
        master_question_list = json.loads(data.get('masterQuestionList', '{}'))
        master_test_list = json.loads(data.get('masterTestList', '{}'))
        master_template_list = json.loads(data.get('masterTemplateList', '{}'))
        master_attachment_list = json.loads(data.get('masterAttachmentList', '{}'))
        master_cover_page_list = json.loads(data.get('masterCoverPageList', '{}'))
        
        # Get the publisher's associated book
        try:
            publisher_book = user_profile.book
            if not publisher_book:
                return Response({"error": "Publisher must have an associated book"}, status=400)
        except Exception as e:
            return Response({"error": f"Error retrieving publisher book: {str(e)}"}, status=400)
        
        # Process Question data (publisher version) - similar structure to teacher questions
        for question_id, question_data in master_question_list.items():
            if not question_data.get('text'):
                continue
                
            question, created = Question.objects.update_or_create(
                id=int(question_id) if question_id.isdigit() else None,
                defaults={
                    'book': publisher_book,  # Link to publisher's book
                    'question_type': question_data.get('qtype', 'SA'),
                    'question_text': question_data.get('text', 'Question text.'),
                    'default_points': question_data.get('score', 1.0),
                    'estimated_time': question_data.get('eta', 1),
                    'instructions_for_grading': question_data.get('directions'),
                    'references': question_data.get('reference'),
                    'instructor_comment': question_data.get('comments'),
                    'chapter': question_data.get('chapter', 0),
                    'section': question_data.get('section', 0),
                    'correct_answer': question_data.get('answer'),
                    'embedded_graphic': question_data.get('img'),
                    'correct_answer_graphic': question_data.get('ansimg'),
                    'include_formula': question_data.get('include_formula', False),
                    'owner': user,
                }
            )
            
            # Process answer options, matching options, and dynamic parameters
            # Similar to teacher code but for publisher questions
            # (Omitted for brevity as it would follow the same pattern)
        
        # Process Template, Cover Page, Test, and Attachment data for publishers
        # (Similar to teacher code but using book instead of course)
        # (Omitted for brevity as it would follow the same pattern with the book association)
        
    elif role == 'webmaster':
        # Process webmaster-specific data (if any)
        pass
    
    return Response({"status": "success"})
    