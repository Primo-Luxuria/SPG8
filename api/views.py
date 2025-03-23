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
        books = Textbook.objects.filter(publisher=user)
        data = {"textbookList": []}
        for book in books:
            book_data = {
                "book": TextbookSerializer(book).data,
                "questionList": get_resource_list('question', book, 'publisher'),
                "testList": get_resource_list('test', book, 'publisher'),
                "templateList": get_resource_list('template', book, 'publisher'),
                "attachmentList": get_resource_list('attachment', book, 'publisher'),
                "coverpageList": get_resource_list('coverpage', book, 'publisher'),
            }
        data["textbookList"].append(book_data)

    return Response(data) 


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
        # Handle data that might be either already parsed or still JSON strings
        master_question_list = data.get('masterQuestionList', {})
        if isinstance(master_question_list, str):
            master_question_list = json.loads(master_question_list)
            
        master_test_list = data.get('masterTestList', {})
        if isinstance(master_test_list, str):
            master_test_list = json.loads(master_test_list)
            
        master_template_list = data.get('masterTemplateList', {})
        if isinstance(master_template_list, str):
            master_template_list = json.loads(master_template_list)
            
        master_attachment_list = data.get('masterAttachmentList', {})
        if isinstance(master_attachment_list, str):
            master_attachment_list = json.loads(master_attachment_list)
            
        course_list = data.get('courseList', {})
        if isinstance(course_list, str):
            course_list = json.loads(course_list)
            
        master_cover_page_list = data.get('masterCoverPageList', {})
        if isinstance(master_cover_page_list, str):
            master_cover_page_list = json.loads(master_cover_page_list)
        
        # Process Course data
        for course_id, course_data in course_list.items():
            # Get or create the course
            try:
                course = Course.objects.get(id=course_id) if course_id.isdigit() else None
            except Course.DoesNotExist:
                course = None
                
            if not course:
                # Create new course
                course = Course(
                    user=user,
                    course_id=course_data.get('id', ''),
                    name=course_data.get('name', 'Untitled Course'),
                    crn=course_data.get('crn', '0000'),
                    sem=course_data.get('sem', 'Fall 2021'),
                    published=course_data.get('published', False)
                )
                
                # Handle textbook association
                textbook_data = course_data.get('textbook')
                if textbook_data:
                    # Try to find existing textbook by ISBN or create a new one
                    textbook_isbn = textbook_data.get('isbn')
                    if textbook_isbn:
                        textbook, created = Textbook.objects.get_or_create(
                            isbn=textbook_isbn,
                            defaults={
                                'title': textbook_data.get('title', ''),
                                'author': textbook_data.get('author', ''),
                                'version': textbook_data.get('version', ''),
                                'link': textbook_data.get('link', '')
                            }
                        )
                        course.textbook = textbook
                
                course.save()
                
                # Add the current user as a teacher
                course.teachers.add(user)
            else:
                # Update existing course
                course.course_id = course_data.get('id', course.course_id)
                course.name = course_data.get('name', course.name)
                course.crn = course_data.get('crn', course.crn)
                course.sem = course_data.get('sem', course.sem)
                course.published = course_data.get('published', course.published)
                
                # Update textbook if provided
                textbook_data = course_data.get('textbook')
                if textbook_data:
                    textbook_isbn = textbook_data.get('isbn')
                    if textbook_isbn:
                        textbook, created = Textbook.objects.get_or_create(
                            isbn=textbook_isbn,
                            defaults={
                                'title': textbook_data.get('title', ''),
                                'author': textbook_data.get('author', ''),
                                'version': textbook_data.get('version', ''),
                                'link': textbook_data.get('link', '')
                            }
                        )
                        course.textbook = textbook
                
                course.save()
            
            # Process questions for this course
            for question_id, question_data in master_question_list.items():
                if question_data.get('courseID') == course_id:
                    # Get or create the question
                    try:
                        question = Question.objects.get(id=question_id) if question_id.isdigit() else None
                    except Question.DoesNotExist:
                        question = None
                    
                    if not question:
                        # Create new question
                        question = Question(
                            course=course,
                            author=user,
                            qtype=question_data.get('qtype', 'mc'),
                            text=question_data.get('text', ''),
                            score=question_data.get('score', 1.0),
                            directions=question_data.get('directions', ''),
                            reference=question_data.get('reference', ''),
                            eta=question_data.get('eta', 1),
                            comments=question_data.get('comments', ''),
                            answer=question_data.get('answer', ''),
                            chapter=question_data.get('chapter', 0),
                            section=question_data.get('section', 0)
                        )
                        question.save()
                        
                        # Process options if this is a multiple choice or similar question
                        options_data = question_data.get('options', [])
                        if options_data and isinstance(options_data, list):
                            for option_text in options_data:
                                Options.objects.create(
                                    question=question,
                                    text=option_text
                                )
                        
                        # Create a dynamic question parameter if needed
                        if question.qtype == 'dy' and question_data.get('dynamicParams'):
                            dynamic_params = question_data.get('dynamicParams', {})
                            DynamicQuestionParameter.objects.create(
                                question=question,
                                formula=dynamic_params.get('formula', ''),
                                range_min=dynamic_params.get('range_min', 0),
                                range_max=dynamic_params.get('range_max', 100),
                                additional_params=dynamic_params.get('additional_params', {})
                            )
                    else:
                        # Update existing question
                        question.text = question_data.get('text', question.text)
                        question.qtype = question_data.get('qtype', question.qtype)
                        question.score = question_data.get('score', question.score)
                        question.directions = question_data.get('directions', question.directions)
                        question.reference = question_data.get('reference', question.reference)
                        question.eta = question_data.get('eta', question.eta)
                        question.comments = question_data.get('comments', question.comments)
                        question.answer = question_data.get('answer', question.answer)
                        question.chapter = question_data.get('chapter', question.chapter)
                        question.section = question_data.get('section', question.section)
                        question.save()
                        
                        # Update options
                        options_data = question_data.get('options', [])
                        if options_data and isinstance(options_data, list):
                            # Delete old options and create new ones
                            Options.objects.filter(question=question).delete()
                            for option_text in options_data:
                                Options.objects.create(
                                    question=question,
                                    text=option_text
                                )
                        
                        # Update dynamic parameters if needed
                        if question.qtype == 'dy' and question_data.get('dynamicParams'):
                            dynamic_params = question_data.get('dynamicParams', {})
                            DynamicQuestionParameter.objects.update_or_create(
                                question=question,
                                defaults={
                                    'formula': dynamic_params.get('formula', ''),
                                    'range_min': dynamic_params.get('range_min', 0),
                                    'range_max': dynamic_params.get('range_max', 100),
                                    'additional_params': dynamic_params.get('additional_params', {})
                                }
                            )
            
            # Process tests for this course
            for test_id, test_data in master_test_list.items():
                if test_data.get('courseID') == course_id:
                    # Get or create the test
                    try:
                        test = Test.objects.get(id=test_id) if test_id.isdigit() else None
                    except Test.DoesNotExist:
                        test = None
                    
                    if not test:
                        # Create new test
                        test = Test(
                            course=course,
                            name=test_data.get('name', 'Untitled Test'),
                            date=test_data.get('date'),
                            filename=test_data.get('filename', ''),
                            is_final=test_data.get('is_final', False)
                        )
                        
                        # Associate template if available
                        template_name = test_data.get('templateName')
                        if template_name:
                            template = Template.objects.filter(name=template_name, course=course).first()
                            if template:
                                test.template = template
                        
                        test.save()
                        
                        # Process test parts and questions
                        parts = test_data.get('parts', [])
                        if parts and isinstance(parts, list):
                            order_counter = 1
                            for part in parts:
                                sections = part.get('sections', [])
                                if sections and isinstance(sections, list):
                                    for section in sections:
                                        questions = section.get('questions', [])
                                        if questions and isinstance(questions, list):
                                            for question_ref in questions:
                                                # Try to find the question by ID
                                                try:
                                                    q_id = question_ref.get('id')
                                                    question = Question.objects.get(id=q_id)
                                                    # Create test question relationship
                                                    TestQuestion.objects.create(
                                                        test=test,
                                                        question=question,
                                                        assigned_points=question_ref.get('points', question.score),
                                                        order=order_counter,
                                                        randomize=question_ref.get('randomize', False),
                                                        special_instructions=question_ref.get('special_instructions', '')
                                                    )
                                                    order_counter += 1
                                                except Question.DoesNotExist:
                                                    pass  # Skip questions that don't exist
                    else:
                        # Update existing test
                        test.name = test_data.get('name', test.name)
                        test.date = test_data.get('date', test.date)
                        test.filename = test_data.get('filename', test.filename)
                        test.is_final = test_data.get('is_final', test.is_final)
                        
                        # Update template association
                        template_name = test_data.get('templateName')
                        if template_name:
                            template = Template.objects.filter(name=template_name, course=course).first()
                            if template:
                                test.template = template
                        
                        test.save()
                        
                        # Update test questions
                        # First remove all existing questions
                        TestQuestion.objects.filter(test=test).delete()
                        
                        # Add questions from parts and sections
                        parts = test_data.get('parts', [])
                        if parts and isinstance(parts, list):
                            order_counter = 1
                            for part in parts:
                                sections = part.get('sections', [])
                                if sections and isinstance(sections, list):
                                    for section in sections:
                                        questions = section.get('questions', [])
                                        if questions and isinstance(questions, list):
                                            for question_ref in questions:
                                                # Try to find the question by ID
                                                try:
                                                    q_id = question_ref.get('id')
                                                    question = Question.objects.get(id=q_id)
                                                    # Create test question relationship
                                                    TestQuestion.objects.create(
                                                        test=test,
                                                        question=question,
                                                        assigned_points=question_ref.get('points', question.score),
                                                        order=order_counter,
                                                        randomize=question_ref.get('randomize', False),
                                                        special_instructions=question_ref.get('special_instructions', '')
                                                    )
                                                    order_counter += 1
                                                except Question.DoesNotExist:
                                                    pass  # Skip questions that don't exist
            
            # Process templates for this course
            for template_id, template_data in master_template_list.items():
                if template_data.get('courseID') == course_id:
                    # Get or create the template
                    try:
                        template = Template.objects.get(id=template_id) if template_id.isdigit() else None
                    except Template.DoesNotExist:
                        template = None
                    
                    if not template:
                        # Create new template
                        template = Template(
                            course=course,
                            name=template_data.get('name', 'Untitled Template'),
                            titleFont=template_data.get('titleFont', 'Arial'),
                            titleFontSize=template_data.get('titleFontSize', 48),
                            subtitleFont=template_data.get('subtitleFont', 'Arial'),
                            subtitleFontSize=template_data.get('subtitleFontSize', 24),
                            bodyFont=template_data.get('bodyFont', 'Arial'),
                            bodyFontSize=template_data.get('bodyFontSize', 12),
                            pageNumbersInHeader=template_data.get('pageNumbersInHeader', False),
                            pageNumbersInFooter=template_data.get('pageNumbersInFooter', False),
                            headerText=template_data.get('headerText', ''),
                            footerText=template_data.get('footerText', ''),
                            coverPage=template_data.get('coverPageType', 0)
                        )
                        template.save()
                    else:
                        # Update existing template
                        template.name = template_data.get('name', template.name)
                        template.titleFont = template_data.get('titleFont', template.titleFont)
                        template.titleFontSize = template_data.get('titleFontSize', template.titleFontSize)
                        template.subtitleFont = template_data.get('subtitleFont', template.subtitleFont)
                        template.subtitleFontSize = template_data.get('subtitleFontSize', template.subtitleFontSize)
                        template.bodyFont = template_data.get('bodyFont', template.bodyFont)
                        template.bodyFontSize = template_data.get('bodyFontSize', template.bodyFontSize)
                        template.pageNumbersInHeader = template_data.get('pageNumbersInHeader', template.pageNumbersInHeader)
                        template.pageNumbersInFooter = template_data.get('pageNumbersInFooter', template.pageNumbersInFooter)
                        template.headerText = template_data.get('headerText', template.headerText)
                        template.footerText = template_data.get('footerText', template.footerText)
                        template.coverPage = template_data.get('coverPageType', template.coverPage)
                        template.save()
            
            # Process cover pages for this course
            for coverpage_id, coverpage_data in master_cover_page_list.items():
                if coverpage_data.get('courseID') == course_id:
                    # Get or create the cover page
                    try:
                        coverpage = CoverPage.objects.get(id=coverpage_id) if coverpage_id.isdigit() else None
                    except CoverPage.DoesNotExist:
                        coverpage = None
                    
                    if not coverpage:
                        # Create new cover page
                        coverpage = CoverPage(
                            course=course,
                            name=coverpage_data.get('name', 'Untitled Cover Page'),
                            testNum=coverpage_data.get('testNum', ''),
                            date=datetime.strptime(coverpage_data.get('date', '2021-01-01'), '%Y-%m-%d').date(),
                            file=coverpage_data.get('file', ''),
                            showFilename=coverpage_data.get('showFilename', False),
                            blank=coverpage_data.get('blank', 'TL'),
                            instructions=coverpage_data.get('instructions', ''),
                            published=coverpage_data.get('published', False)
                        )
                        coverpage.save()
                    else:
                        # Update existing cover page
                        coverpage.name = coverpage_data.get('name', coverpage.name)
                        coverpage.testNum = coverpage_data.get('testNum', coverpage.testNum)
                        if coverpage_data.get('date'):
                            coverpage.date = datetime.strptime(coverpage_data.get('date'), '%Y-%m-%d').date()
                        coverpage.file = coverpage_data.get('file', coverpage.file)
                        coverpage.showFilename = coverpage_data.get('showFilename', coverpage.showFilename)
                        coverpage.blank = coverpage_data.get('blank', coverpage.blank)
                        coverpage.instructions = coverpage_data.get('instructions', coverpage.instructions)
                        coverpage.published = coverpage_data.get('published', coverpage.published)
                        coverpage.save()
            
            # Process attachments
            for attachment_id, attachment_data in master_attachment_list.items():
                if attachment_data.get('courseID') == course_id:
                    # Note: File handling would typically require more work with file uploads
                    # For now, we just create/update the attachment record
                    
                    try:
                        attachment = Attachment.objects.get(id=attachment_id) if attachment_id.isdigit() else None
                    except Attachment.DoesNotExist:
                        attachment = None
                    
                    if not attachment and 'file' in attachment_data:
                        # Create new attachment
                        attachment = Attachment(
                            course=course,
                            name=attachment_data.get('name', 'Untitled Attachment'),
                            published=attachment_data.get('published', False)
                            # file field would be handled in a file upload view
                        )
                        attachment.save()
                    elif attachment:
                        # Update existing attachment
                        attachment.name = attachment_data.get('name', attachment.name)
                        attachment.published = attachment_data.get('published', attachment.published)
                        attachment.save()
        
    elif role == 'publisher':
        # Similar logic for publisher, but using textbooks instead of courses
        master_question_list = data.get('masterQuestionList', {})
        if isinstance(master_question_list, str):
            master_question_list = json.loads(master_question_list)
            
        master_test_list = data.get('masterTestList', {})
        if isinstance(master_test_list, str):
            master_test_list = json.loads(master_test_list)
            
        master_template_list = data.get('masterTemplateList', {})
        if isinstance(master_template_list, str):
            master_template_list = json.loads(master_template_list)
            
        master_attachment_list = data.get('masterAttachmentList', {})
        if isinstance(master_attachment_list, str):
            master_attachment_list = json.loads(master_attachment_list)
            
        textbook_list = data.get('textbookList', {})
        if isinstance(textbook_list, str):
            textbook_list = json.loads(textbook_list)
            
        master_cover_page_list = data.get('masterCoverPageList', {})
        if isinstance(master_cover_page_list, str):
            master_cover_page_list = json.loads(master_cover_page_list)
        
        # Process Textbook data
        for textbook_id, textbook_data in textbook_list.items():
            # Similar logic as with courses, but for textbooks
            try:
                textbook = Textbook.objects.get(id=textbook_id) if textbook_id.isdigit() else None
            except Textbook.DoesNotExist:
                textbook = None
                
            if not textbook:
                # Create new textbook
                textbook = Textbook(
                    title=textbook_data.get('title', 'Untitled Textbook'),
                    author=textbook_data.get('author', ''),
                    version=textbook_data.get('version', ''),
                    isbn=textbook_data.get('isbn', ''),
                    link=textbook_data.get('link', ''),
                    publisher=user,
                    published=textbook_data.get('published', False)
                )
                textbook.save()
            else:
                # Update existing textbook
                textbook.title = textbook_data.get('title', textbook.title)
                textbook.author = textbook_data.get('author', textbook.author)
                textbook.version = textbook_data.get('version', textbook.version)
                textbook.isbn = textbook_data.get('isbn', textbook.isbn)
                textbook.link = textbook_data.get('link', textbook.link)
                textbook.published = textbook_data.get('published', textbook.published)
                textbook.save()
            
            # Process questions for this textbook (similar to the course logic)
            for question_id, question_data in master_question_list.items():
                if question_data.get('textbookID') == textbook_id:
                    # Same structure as the teacher questions, but linked to textbook instead of course
                    try:
                        question = Question.objects.get(id=question_id) if question_id.isdigit() else None
                    except Question.DoesNotExist:
                        question = None
                    
                    if not question:
                        # Create new question
                        question = Question(
                            textbook=textbook,
                            author=user,
                            qtype=question_data.get('qtype', 'mc'),
                            text=question_data.get('text', ''),
                            score=question_data.get('score', 1.0),
                            directions=question_data.get('directions', ''),
                            reference=question_data.get('reference', ''),
                            eta=question_data.get('eta', 1),
                            comments=question_data.get('comments', ''),
                            answer=question_data.get('answer', ''),
                            chapter=question_data.get('chapter', 0),
                            section=question_data.get('section', 0)
                        )
                        question.save()
                        
                        # Process options and other question data as before...
                    else:
                        # Update existing question
                        # Same logic as above...
                        pass
            
            # Process tests, templates, cover pages, and attachments for this textbook
            # (similar structure to the course logic but associated with textbook)
    
    return Response({"status": "success"})