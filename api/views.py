from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import transaction
from django.contrib.auth.models import User
import json, os
from decimal import Decimal
from django.db.models.fields.files import FieldFile
from django.apps import apps
from datetime import date
from django.views.decorators.http import require_POST


from welcome.models import (
    Course, Textbook, Question, Test, Template, CoverPage, 
    Attachment, TestQuestion, Options, Answers, UserProfile,
    TestPart, TestSection, Feedback, FeedbackResponse
)

class ValidationError(Exception):
    """Exception for validation errors in the API views."""
    pass


from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction

@api_view(['POST'])
@transaction.atomic
def join_course(request):
    user = request.user
    course_id = request.data.get('id')

    if not course_id:
        return Response({"status": "error", "message": "Course ID is required"}, 
                        status=status.HTTP_400_BAD_REQUEST)

    try:
        user_profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        return Response({"status": "error", "message": "User profile not found"}, 
                        status=status.HTTP_404_NOT_FOUND)

    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return Response({"status": "error", "message": "Course not found"}, 
                        status=status.HTTP_404_NOT_FOUND)

    if user_profile.role != "teacher":
        return Response({"status": "error", "message": "Only teachers can join courses"}, 
                        status=status.HTTP_403_FORBIDDEN)

    try:
        course.teachers.add(user)
        return Response({"status": "success", "message": "Successfully added teacher to course"})
    except Exception as e:
        return Response({"status": "error", "message": f"An error occurred: {str(e)}"}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@transaction.atomic
def assign_books(request):
    user = request.user
    data = request.data
    course_id = data.get('id', '')
    textbook_ids = data.get('textbook_ids', [])

    print(course_id)
    print(textbook_ids)
    if not course_id or not isinstance(textbook_ids, list):
        return Response({"status": "error", "message": "Invalid data."},
                        status=status.HTTP_400_BAD_REQUEST)

    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return Response({"status": "error", "message": "Course not found."},
                        status=status.HTTP_404_NOT_FOUND)

    
    if not course.teachers.filter(id=user.id).exists():
        return Response({"status": "error", "message": "You are not a teacher for this course."},
                        status=status.HTTP_403_FORBIDDEN)

    # Get all textbook objects matching the provided IDs
    textbooks = Textbook.objects.filter(id__in=textbook_ids)

    if not textbooks.exists():
        return Response({"status": "error", "message": "No valid textbooks found."},
                        status=status.HTTP_400_BAD_REQUEST)

    # Add textbooks to the course
    course.textbooks.add(*textbooks)

    return Response({
        "status": "success",
        "message": f"{textbooks.count()} textbook(s) assigned to course {course.course_id}."
    })



@api_view(['POST'])
@transaction.atomic
def delete_item(request):
    data = request.data
    model_name = data.get("model_type", "")
    item_id = data.get("id")
    print("Request data:", request.data)
    # Validate input
    if not model_name:
        return Response({"status": "error", "message": "Missing model_type parameter"}, 
                      status=status.HTTP_400_BAD_REQUEST)
    
    if not item_id:
        return Response({"status": "error", "message": "Missing id parameter"}, 
                      status=status.HTTP_400_BAD_REQUEST)
    
    # Get the requesting user's profile
    try:
        requesting_user = request.user
        requesting_profile = UserProfile.objects.get(user=requesting_user)
        requesting_role = requesting_profile.role
    except UserProfile.DoesNotExist:
        return Response({"status": "error", "message": "User profile not found"}, 
                       status=status.HTTP_404_NOT_FOUND)
    
    # Get the model
    try:
        Model = apps.get_model('welcome', model_name)
    except LookupError:
        return Response({"status": "error", "message": f"Unknown model type: {model_name}"}, 
                      status=status.HTTP_400_BAD_REQUEST)
    
    # Get the item
    try:
        item = Model.objects.get(id=item_id)
    except Model.DoesNotExist:
        return Response({"status": "error", "message": f"{model_name} with id {item_id} not found"}, 
                      status=status.HTTP_404_NOT_FOUND)
    
    # If webmaster, they can delete any item
    if requesting_role == 'webmaster':
        # Webmaster can delete on behalf of any user
        pass  # No additional checks needed
    else:
        # For non-webmasters, they can only delete their own items
        has_permission = False
        
        if model_name == "Course":
            item.teachers.remove(requesting_user)
            return Response({"status": "success", "message": "Removed from Course!"})
        # Check if they are the author/owner
        if hasattr(item, 'author') and item.author == requesting_user:
            has_permission = True
        elif hasattr(item, 'user') and item.user == requesting_user:
            has_permission = True
        elif hasattr(item, 'teachers') and requesting_user in item.teachers.all():
            has_permission = True
        elif hasattr(item, 'publisher') and item.publisher == requesting_user:
            has_permission = True
        
        if not has_permission:
            return Response({"status": "error", "message": "You don't have permission to delete this item"}, 
                          status=status.HTTP_403_FORBIDDEN)
    
    # Special handling for file fields
    if hasattr(item, 'file') and item.file:
        if hasattr(item.file, 'path') and os.path.exists(item.file.path):
            try:
                os.remove(item.file.path)
            except OSError as e:
                # Log the error but continue with deletion
                print(f"Error removing file: {e}")
    
    # Delete the item
    item.delete()
    
    return Response({"status": "success", "message": f"{model_name} successfully deleted!"})

@api_view(['POST'])
@transaction.atomic
def update_user(request):
    data = request.data
    current_username = data.get('username')
    update_username = data.get('update_username', False)
    new_username = data.get('new_username')
    new_password = data.get('new_password')
    
    # Find the user
    try:
        user = User.objects.get(username=current_username)
    except User.DoesNotExist:
        return Response({"status": "error", "message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # Check permissions - only the user themselves or webmasters should be able to update
    try:
        requesting_profile = UserProfile.objects.get(user=request.user)
        requesting_role = requesting_profile.role
        
        if requesting_role != 'webmaster' and request.user.id != user.id:
            return Response({"status": "error", "message": "You don't have permission to update this user"}, 
                           status=status.HTTP_403_FORBIDDEN)
    except UserProfile.DoesNotExist:
        return Response({"status": "error", "message": "User profile not found"}, 
                       status=status.HTTP_404_NOT_FOUND)
    
    # Update username if requested
    if update_username and new_username:
        if User.objects.filter(username=new_username).exists():
            return Response({"status": "error", "message": "This username is already taken"}, 
                          status=status.HTTP_400_BAD_REQUEST)
        user.username = new_username
    
    # Update password if provided
    if new_password:
        user.set_password(new_password)
    
    user.save()
    
    # If password was changed, update the session to prevent logout
    if new_password and user.id == request.user.id:
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, user)
    
    return Response({"status": "success", "message": "User updated successfully"})


@api_view(['POST'])
@require_POST
def fetch_user_data(request):
    data = request.data
    request_type = data.get('type', '')
    value = data.get('value', '')

    # Step 1: Get user
    try:
        if request_type == "UN":
            user = User.objects.get(username=value)
        elif request_type == "ID":
            user = User.objects.get(id=value)
        else:
            return Response({"status": "INVALID REQUEST TYPE"}, status=400)
    except User.DoesNotExist:
        return Response({"status": "User not found"}, status=404)

    # Step 2: Get UserProfile
    try:
        userpf = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        return Response({"status": "UserProfile not found"}, status=404)

    role = userpf.role
    print("Role:", role)

    # Initialize shared vars
    master_question_list = {}
    master_test_list = {}
    master_template_list = {}
    master_cpage_list = {}
    master_attachment_list = {}
    container_list = {}

    course_list = {course.id: course.name for course in Course.objects.all()}
    textbook_list = {book.id: book.isbn for book in Textbook.objects.all()}

    try:
        if role == "teacher":
            # Get teacher's courses
            courses = Course.objects.filter(teachers=user)
            
            # Get content from courses directly
            course_question_list = get_question_list('course', courses)
            
            # Get all textbooks assigned to these courses
            course_textbooks = []
            for course in courses:
                course_textbooks.extend(list(course.textbooks.all()))
            
            # Remove duplicates by converting to set then back to list
            unique_textbooks = list({textbook.id: textbook for textbook in course_textbooks}.values())
            
            # Get textbook content
            if unique_textbooks:
                textbook_question_list = get_question_list('textbook', unique_textbooks)
                
                # Merge course and textbook question lists
                for textbook in unique_textbooks:
                    isbn = textbook.isbn
                    if isbn in textbook_question_list:
                        for qtype, questions in textbook_question_list[isbn].items():
                            # For each course that uses this textbook
                            for course in courses:
                                if textbook in course.textbooks.all():
                                    course_id = course.course_id
                                    # Initialize question type dict if needed
                                    if course_id not in master_question_list:
                                        master_question_list[course_id] = {}
                                    if qtype not in master_question_list[course_id]:
                                        master_question_list[course_id][qtype] = {}
                                    
                                    # Add textbook questions to course
                                    for q_id, q_data in questions.items():
                                        # Mark the source as a textbook
                                        q_data['source'] = 'textbook'
                                        q_data['textbook_id'] = isbn
                                        master_question_list[course_id][qtype][q_id] = q_data
            
            # Add direct course questions
            for course_id, qtypes in course_question_list.items():
                if course_id not in master_question_list:
                    master_question_list[course_id] = {}
                
                for qtype, questions in qtypes.items():
                    if qtype not in master_question_list[course_id]:
                        master_question_list[course_id][qtype] = {}
                    
                    for q_id, q_data in questions.items():
                        # Mark as direct course content
                        q_data['source'] = 'course'
                        master_question_list[course_id][qtype][q_id] = q_data

            # Do the same for tests, templates, cover pages, and attachments
            with transaction.atomic():
                # Get course content
                course_test_list = get_test_list('course', courses)
                course_template_list = get_template_list('course', courses)
                course_cpage_list = get_cpage_list('course', courses)
                course_attachment_list = get_attachment_list('course', courses)
                
                # Get textbook content
                if unique_textbooks:
                    textbook_test_list = get_test_list('textbook', unique_textbooks)
                    textbook_template_list = get_template_list('textbook', unique_textbooks)
                    textbook_cpage_list = get_cpage_list('textbook', unique_textbooks)
                    textbook_attachment_list = get_attachment_list('textbook', unique_textbooks)
                    
                    # Merge test lists
                    for textbook in unique_textbooks:
                        isbn = textbook.isbn
                        if isbn in textbook_test_list:
                            for course in courses:
                                if textbook in course.textbooks.all():
                                    course_id = course.course_id
                                    if course_id not in master_test_list:
                                        master_test_list[course_id] = {'drafts': {}, 'published': {}}
                                    
                                    # Add published and draft tests
                                    for status in ['drafts', 'published']:
                                        for test_id, test_data in textbook_test_list[isbn].get(status, {}).items():
                                            test_data['source'] = 'textbook'
                                            test_data['textbook_id'] = isbn
                                            master_test_list[course_id][status][test_id] = test_data
                
                # Add direct course tests
                for course_id, tests in course_test_list.items():
                    if course_id not in master_test_list:
                        master_test_list[course_id] = {'drafts': {}, 'published': {}}
                    
                    for status in ['drafts', 'published']:
                        for test_id, test_data in tests.get(status, {}).items():
                            test_data['source'] = 'course'
                            master_test_list[course_id][status][test_id] = test_data
                
                # Merge template lists
                master_template_list = course_template_list.copy()
                if unique_textbooks:
                    for textbook in unique_textbooks:
                        isbn = textbook.isbn
                        if isbn in textbook_template_list:
                            for course in courses:
                                if textbook in course.textbooks.all():
                                    course_id = course.course_id
                                    if course_id not in master_template_list:
                                        master_template_list[course_id] = {}
                                    
                                    for template_id, template_data in textbook_template_list[isbn].items():
                                        template_data['source'] = 'textbook'
                                        template_data['textbook_id'] = isbn
                                        master_template_list[course_id][template_id] = template_data
                
                # Merge cover page lists
                master_cpage_list = course_cpage_list.copy()
                if unique_textbooks:
                    for textbook in unique_textbooks:
                        isbn = textbook.isbn
                        if isbn in textbook_cpage_list:
                            for course in courses:
                                if textbook in course.textbooks.all():
                                    course_id = course.course_id
                                    if course_id not in master_cpage_list:
                                        master_cpage_list[course_id] = {}
                                    
                                    for cpage_id, cpage_data in textbook_cpage_list[isbn].items():
                                        cpage_data['source'] = 'textbook'
                                        cpage_data['textbook_id'] = isbn
                                        master_cpage_list[course_id][cpage_id] = cpage_data
                
                # Merge attachment lists
                master_attachment_list = course_attachment_list.copy()
                if unique_textbooks:
                    for textbook in unique_textbooks:
                        isbn = textbook.isbn
                        if isbn in textbook_attachment_list:
                            for course in courses:
                                if textbook in course.textbooks.all():
                                    course_id = course.course_id
                                    if course_id not in master_attachment_list:
                                        master_attachment_list[course_id] = {}
                                    
                                    for attachment_id, attachment_data in textbook_attachment_list[isbn].items():
                                        attachment_data['source'] = 'textbook'
                                        attachment_data['textbook_id'] = isbn
                                        master_attachment_list[course_id][attachment_id] = attachment_data

                # Populate container list with course info
                for course in courses:
                    container_list[course.course_id] = {
                        "courseID": course.course_id,
                        "crn": course.crn,
                        "name": course.name,
                        "sem": course.sem,
                        "textbooks": [textbook.id for textbook in course.textbooks.all()],
                        "id": course.id
                    }

        elif role == "publisher":
            textbooks = Textbook.objects.filter(publisher=user)
            if not textbooks.exists():
                raise Exception("No textbooks found for this publisher")

            print("Calling get_question_list for publisher...")
            master_question_list = get_question_list('textbook', textbooks)

            with transaction.atomic():
                master_test_list = get_test_list('textbook', textbooks)
                master_template_list = get_template_list('textbook', textbooks)
                master_cpage_list = get_cpage_list('textbook', textbooks)
                master_attachment_list = get_attachment_list('textbook', textbooks)

                for textbook in textbooks:
                    container_list[textbook.isbn] = {
                        'title': textbook.title,
                        'author': textbook.author,
                        'version': textbook.version,
                        'isbn': textbook.isbn,
                        'link': textbook.link,
                        "id": textbook.id
                    }

        elif role == "webmaster":
            # Allow login but return empty structures
            pass

        else:
            raise Exception("Invalid user role")

        response_data = {
            "status": "success",
            "username": user.username,
            "role": role,
            "question_list": master_question_list,
            "test_list": master_test_list,
            "template_list": master_template_list,
            "cpage_list": master_cpage_list,
            "attachment_list": master_attachment_list,
            "container_list": container_list,
            "course_list": course_list,
            "textbook_list": textbook_list
        }

    except Exception as e:
        print("Atomic block failed:", str(e))
        return Response({"status": f"An error occurred: {str(e)}"}, status=500)

    return Response(response_data)

@api_view(['POST'])
@transaction.atomic
def save_textbook(request):
    data = request.data
    datatext = data.get('textbook', {})
    newtextbook, created = Textbook.objects.update_or_create(
            id = datatext.get('id') if datatext.get('id') else None,
            defaults={
                'title': datatext.get('title'),
                'author': datatext.get('author'),
                'version':datatext.get('version'),
                'isbn':datatext.get('isbn'),
                'link':datatext.get('link'),
            }
        )
    newtextbook.save()
    if created:
        newtextbook.publisher = request.user
        newtextbook.save()
        coverPage = CoverPage.objects.create(
                name= "Default 1st Test",
                testNum= 1,
                date= date.today().isoformat(),
                file= "defaultpage",
                showFilename= True,
                blank= "TR",
                instructions= "Grade according to the rubric, giving partial credit where indicated",
                published= 1,
                textbook=newtextbook
            )
        newtemplate = Template.objects.create(
            
                name= 'System Default',
                titleFont= 'Arial',
                titleFontSize= 48,
                subtitleFont= 'Arial',
                subtitleFontSize= 24,
                bodyFont= 'Arial',
                bodyFontSize= 12,
                pageNumbersInHeader= False,
                pageNumbersInFooter= False,
                headerText= '',
                footerText= '',
                coverPageID= coverPage.id,
                nameTag= '',
                dateTag= '',
                courseTag= '',
                partStructure= {},
                bonusSection= False,
                bonusQuestions= [],
                published= 1,
                textbook= newtextbook
            )
    return Response({
            'status': 'success',
            'created': created,
            'isbn': newtextbook.isbn,
            'id': newtextbook.id
        })


@api_view(['POST'])
@transaction.atomic
def save_test(request):
    try:
        data = request.data
        test_data = data.get('test', {})
        parts_data = data.get('parts', [])
        owner_role = data.get('ownerRole')
    
        # Validate required fields
        if owner_role is None:
            return Response({'error': 'Owner role is required'}, status=400)
            
        # Determine ownership based on role
        course = None
        textbook = None
        
        if owner_role == 'teacher':
            course_id = data.get('courseID')
            if not course_id:
                return Response({'error': 'courseID is required for teacher role'}, status=400)
            try:
                course = Course.objects.get(course_id=course_id)
            except Course.DoesNotExist:
                return Response({'error': 'Course not found'}, status=400)
        elif owner_role == 'publisher':
            isbn = data.get('isbn')
            if not isbn:
                return Response({'error': 'ISBN is required for publisher role'}, status=400)
            try:
                textbook = Textbook.objects.get(isbn=isbn)
            except Textbook.DoesNotExist:
                return Response({'error': 'Textbook not found'}, status=400)
        
        # Get template if provided
        template = None
        template_id = test_data.get('templateID', 0)
        if template_id and template_id > 0:
            try:
                template = Template.objects.get(id=template_id)
            except Template.DoesNotExist:
                return Response({'error': 'Template not found'}, status=400)
        
        # Create or update test
        test_id = test_data.get('id')
        test, created = Test.objects.update_or_create(
            id=test_id if test_id else None,
            defaults={
                'name': test_data.get('name', 'Untitled Test'),
                'date': test_data.get('date'),
                'filename': test_data.get('filename'),
                'is_final': bool(test_data.get('is_final')),
                'refText': test_data.get('refText'),
                'templateID': template_id,
                'course': course,
                'textbook': textbook,
                'template': template
            }
        )

        attachment_list = test_data.get("attachments", [])
        test.attachments.clear()
        for attachment_id in attachment_list:
            try:
                attachment = Attachment.objects.get(id=attachment_id)
                test.attachments.add(attachment)
                attachment.published = 1 if test.is_final == True else attachment.published
                attachment.save()
            except Attachment.DoesNotExist:
                continue

        if created:
            test.author = request.user
        test.save()

        if test.is_final:
            if test.author == request.user:
                role = owner_role  
            else:
                author_profile = UserProfile.objects.get(user=test.author)
                role = author_profile.role

            if role == 'teacher':
                course.published = 1
                course.save()
            else:
                textbook.published = 1
                textbook.save()
            if template and template.coverPageID:
                template.published = 1
                template.save()
                try:
                    coverpage = CoverPage.objects.get(id=template.coverPageID)
                    coverpage.published = 1
                    coverpage.save()
                except CoverPage.DoesNotExist:
                    return Response({"status": "error", "message": "Missing cover page!"})
            
        # Process parts, sections, and questions
        if parts_data:
            # Delete existing parts (cascades to sections and questions)
            test.test_questions.all().delete()
            test.parts.all().delete()
            
            # Create new parts
            for part_data in parts_data:
                part = TestPart.objects.create(
                    test=test,
                    part_number=part_data.get('part_number')
                )
                
                # Create sections within this part
                sections_data = part_data.get('sections', [])
                for section_data in sections_data:
                    section = TestSection.objects.create(
                        part=part,
                        section_number=section_data.get('section_number'),
                        question_type=section_data.get('question_type')
                    )
                    
                    # Create questions within this section
                    questions_data = section_data.get('questions', [])
                    for question_data in questions_data:
                        question_id = question_data.get('id')
                        if question_id:
                            try:
                                question = Question.objects.get(id=question_id)
                                print(f"Creating TestQuestion: test={test.id}, question={question.id}")
                                TestQuestion.objects.create(
                                    test=test,
                                    question=question,
                                    assigned_points=question_data.get('assigned_points', 1),
                                    order=question_data.get('order', 0),
                                    section=section
                                )
                                question.tests.add(test)
                                if test.is_final:
                                    question.published = 1
                                    question.save()
                            except Question.DoesNotExist:
                                continue  # Skip invalid questions
        
        # Process feedback if provided
        fb_list = data.get('feedback', [])
        for fb_item in fb_list:
            fb_user = User.objects.get(username=fb_item.get('username'))
            feedback, created = Feedback.objects.update_or_create(
                    id=fb_item.get('id'),
                    defaults ={
                        'test':test,
                        'user':fb_user,
                        'rating':fb_item.get('rating'),
                        'averageScore':fb_item.get('averageScore'),
                        'comments':fb_item.get('comments'),
                        'time':fb_item.get('time')
                    }
                    
                )

            for resp in fb_item.get('responses', []):
                try:
                    resp_user = User.objects.get(username=resp.get('username')) if resp.get('username') else None
                except User.DoesNotExist:
                    resp_user = None
                FeedbackResponse.objects.update_or_create(
                    id=resp.get('id'),
                    defaults ={
                        'feedback':feedback,
                        'user':resp_user,
                        'text':resp.get('text'),
                        'date':resp.get('date')
                    })
        
        return Response({
            'status': 'success',
            'created': created,
            'test_id': test.id,
            'test_name': test.name
        })
    
    except Exception as e:
        return Response({'error': f'Error saving test: {str(e)}'}, status=500)

@api_view(['POST'])
@transaction.atomic
def save_course(request):
    try:
        data = request.data
        course_data = data.get('course', {})
        
        # Process course data
        course_id = course_data.get('id')
        if course_id and Course.objects.filter(id=course_id).exists():
            # Update existing course
            course = Course.objects.get(id=course_id)
            course.course_id = course_data.get('course_id', course.course_id)
            course.name = course_data.get('name', course.name)
            course.crn = course_data.get('crn', course.crn)
            course.sem = course_data.get('sem', course.sem)
            course.published = course_data.get('published', course.published)
            course.save()
            created = False
        else:
            # Create new course
            course = Course.objects.create(
                course_id=course_data.get('course_id', 'Untitled Course'),
                name=course_data.get('name', 'Untitled Course'),
                crn=course_data.get('crn', ''),
                sem=course_data.get('sem', ''),
                published=course_data.get('published', False),
                user=request.user
            )
            created = True
            coverPage = CoverPage.objects.create(
                name= "Default 1st Test",
                testNum= 1,
                date= date.today().isoformat(),
                file= "defaultpage",
                showFilename= True,
                blank= "TR",
                instructions= "Grade according to the rubric, giving partial credit where indicated",
                published= 1,
                course=course
            )
            newtemplate = Template.objects.create(
            
                name= 'System Default',
                titleFont= 'Arial',
                titleFontSize= 48,
                subtitleFont= 'Arial',
                subtitleFontSize= 24,
                bodyFont= 'Arial',
                bodyFontSize= 12,
                pageNumbersInHeader= False,
                pageNumbersInFooter= False,
                headerText= '',
                footerText= '',
                coverPageID= coverPage.id,
                nameTag= '',
                dateTag= '',
                courseTag= '',
                partStructure= {},
                bonusSection= False,
                bonusQuestions= [],
                published= 1,
                course= course
            )
        
        # Associate teacher with course through the teachers M2M field
        # Check if user is not already in teachers list
        if request.user not in course.teachers.all():
            course.teachers.add(request.user)
        
        return Response({
            'status': 'success',
            'created': created,
            'course_id': course.course_id,
            'id': course.id
        })
    except Exception as e:
        return Response({'error': str(e)}, status=400)

@api_view(['POST'])
@transaction.atomic
def save_cpage(request):
    try:
        data = request.data
        owner_role = data.get('ownerRole')
        cover_page_data = data.get('coverPage', {})
        
        # Determine ownership (course or textbook)
        course = None
        textbook = None
        
        if owner_role == 'teacher':
            try:
                course_id = data.get('courseID')
                course = Course.objects.get(course_id=course_id)
                textbook= None
            except Course.DoesNotExist:
                return Response({'error': 'Course not found'}, status=400)
        elif owner_role == 'publisher':
            try:
                isbn = data.get('isbn')
                textbook = Textbook.objects.get(isbn=isbn)
                course=None
            except Textbook.DoesNotExist:
                return Response({'error': 'Textbook not found'}, status=400)
        else:
            return Response({'error': 'Invalid owner role'}, status=400)
        
        # Check if the cover page is already published
        cover_page_id = cover_page_data.get('id')
        
        # Process cover page data
        if cover_page_id and CoverPage.objects.filter(id=cover_page_id,course=course,textbook=textbook).exists():
            # Update existing cover page
            cover_page = CoverPage.objects.get(id=cover_page_id)
            cover_page.name = cover_page_data.get('name', cover_page.name)
            cover_page.testNum = cover_page_data.get('testNum', cover_page.testNum)
            cover_page.date = cover_page_data.get('date', cover_page.date)
            cover_page.file = cover_page_data.get('file', cover_page.file)
            cover_page.showFilename = cover_page_data.get('showFilename', cover_page.showFilename)
            cover_page.blank = cover_page_data.get('blank', cover_page.blank)
            cover_page.instructions = cover_page_data.get('instructions', cover_page.instructions)
            cover_page.published = cover_page_data.get('published', cover_page.published)
            cover_page.save()
            created = False
        else:
            # Create new cover page
            cover_page = CoverPage.objects.create(
                name=cover_page_data.get('name', 'Untitled Cover Page'),
                testNum=cover_page_data.get('testNum', ''),
                date=cover_page_data.get('date', ''),
                file=cover_page_data.get('file', ''),
                showFilename=cover_page_data.get('showFilename', False),
                blank=cover_page_data.get('blank', 'TL'),
                instructions=cover_page_data.get('instructions'),
                published=cover_page_data.get('published', False),
                course=course,
                textbook=textbook
            )
            created = True
            cover_page.author = request.user
            cover_page.save()
        
        return Response({
            'status': 'success',
            'created': created,
            'cover_page_id': cover_page.id,
            'name': cover_page.name
        })
    except Exception as e:
        return Response({'error': str(e)}, status=400)



@api_view(['POST'])
@transaction.atomic
def save_template(request):
    try:
        data = request.data
        owner_role = data.get('ownerRole')
        template_data = data.get('template', {})
        
        # Determine ownership (course or textbook)
        course = None
        textbook = None
        
        if owner_role == 'teacher':
            try:
                course_id = data.get('courseID')
                course = Course.objects.get(course_id=course_id)
            except Course.DoesNotExist:
                return Response({'error': 'Course not found'}, status=400)
        elif owner_role == 'publisher':
            try:
                isbn = data.get('isbn')
                textbook = Textbook.objects.get(isbn=isbn)
            except Textbook.DoesNotExist:
                return Response({'error': 'Textbook not found'}, status=400)
        else:
            return Response({'error': 'Invalid owner role'}, status=400)
        
        if not course and not textbook:
            return Response({'error': 'Template must be associated with a course or textbook.'}, status=400)


        # Process template data
        template_id = template_data.get('id')
        newtemplate, created = Template.objects.update_or_create(
            id=template_id if template_id else None,
            defaults={
                "name": template_data.get('name'),
                "titleFont": template_data.get('titleFont', 'Arial'),
                "titleFontSize": int(template_data.get('titleFontSize', 48)),
                "subtitleFont": template_data.get('subtitleFont', 'Arial'),
                "subtitleFontSize": int(template_data.get('subtitleFontSize', 24)),
                "bodyFont": template_data.get('bodyFont', 'Arial'),
                "bodyFontSize": int(template_data.get('bodyFontSize', 12)),
                "pageNumbersInHeader": bool(template_data.get('pageNumbersInHeader', False)),
                "pageNumbersInFooter": bool(template_data.get('pageNumbersInFooter', False)),
                "headerText": template_data.get('headerText', ''),
                "footerText": template_data.get('footerText', ''),
                "coverPageID": int(template_data.get('coverPageID', 0)),
                "nameTag": template_data.get('nameTag', ''),
                "dateTag": template_data.get('dateTag', ''),
                "courseTag": template_data.get('courseTag', ''),
                "partStructure": template_data.get('partStructure') or {},
                "bonusSection": template_data.get('bonusSection', False),
                "bonusQuestions": template_data.get('bonusQuestions') or [],
                "published": template_data.get('published', False),
                "course": course,
                "textbook": textbook
            }
        )
            
        if created:
            newtemplate.author = request.user;
        else:
            if request.user != newtemplate.author:
                return Response({'error': "You are not the author of this template!"}, status=400)
        newtemplate.save()
        
        
        return Response({
            'status': 'success',
            'created': created,
            'template_id': newtemplate.id,
            'name': newtemplate.name
        })
    except Exception as e:
        return Response({'error': str(e)}, status=400)

from django.core.files.uploadedfile import InMemoryUploadedFile

@api_view(['POST'])
@transaction.atomic
def save_question(request):
    data = request.data
    print(data)
    question_data = data.get('question', {})
    answer_data = data.get('answer', {})
    options_data = data.get('options', {})
    feedback_data = data.get('feedback', [])
    owner_role = data.get('ownerRole')

    course = None
    textbook = None

    if owner_role == 'teacher':
        try:
            owner_id = data.get('courseID')
            course = Course.objects.get(course_id=owner_id)
        except Course.DoesNotExist:
            return Response({'error': 'Course not found'}, status=400)
    elif owner_role == 'publisher':
        try:
            owner_id = data.get('isbn')
            textbook = Textbook.objects.get(isbn=owner_id)
        except Textbook.DoesNotExist:
            return Response({'error': 'Textbook not found'}, status=400)

    try:
        # Handle create or update
        if question_data.get('id'):
            newQ = Question.objects.get(id=question_data['id'])
            created = False
        else:
            newQ = Question()
            created = True
            newQ.course = course
            newQ.textbook = textbook

        # Assign fields
        newQ.text = question_data.get('text', '')
        newQ.qtype = question_data.get('qtype', 'mc')
        newQ.score = question_data.get('score', 1.0)
        newQ.directions = question_data.get('directions')
        newQ.reference = question_data.get('reference')
        newQ.eta = question_data.get('eta', 1)
        newQ.comments = question_data.get('comments')
        newQ.chapter = question_data.get('chapter', 0)
        newQ.section = question_data.get('section', 0)
        newQ.published = question_data.get('published', False)
        newQ.requiredRefs = question_data.get('requiredRefs', '')

        # Safe image field handling
        img = question_data.get('img')
        ansimg = question_data.get('ansimg')
        newQ.imgID = img
        newQ.ansimgID = ansimg

        #newQ.img = img if isinstance(img, (InMemoryUploadedFile, type(None))) else None
        #newQ.ansimg = ansimg if isinstance(ansimg, (InMemoryUploadedFile, type(None))) else None

        


        if created:
            newQ.author = request.user
        newQ.save()

        # Save Answers
        if answer_data:
            Answers.objects.filter(question=newQ).delete()
            qtype = question_data.get('qtype')

            if qtype in ['tf', 'mc', 'sa', 'es']:
                Answers.objects.create(question=newQ, text=answer_data.get('value'))
            elif qtype in ['fb', 'ms']:
                for val in answer_data.values():
                    Answers.objects.create(question=newQ, text=val.get('value'))
            elif qtype == 'ma':
                for val in answer_data.values():
                    print("MA Answer Data:", answer_data)
                    Answers.objects.create(question=newQ, text=val.get('text'))

        # Save Options
        if options_data:
            Options.objects.filter(question=newQ).delete()
            qtype = question_data.get('qtype')

            if qtype == 'tf':
                Options.objects.create(question=newQ, text='True', order=1)
                Options.objects.create(question=newQ, text='False', order=2)
            elif qtype == 'mc':
                for key, val in options_data.items():
                    if key in ['A', 'B', 'C', 'D'] and val:
                        Options.objects.create(
                            question=newQ,
                            text=val.get('text'),
                            order=val.get('order', 0)
                        )
            elif qtype == 'ms':
                for key, val in options_data.items():
                    if key.startswith('option') and val:
                        Options.objects.create(
                            question=newQ,
                            text=val.get('text'),
                            order=val.get('order', 0)
                        )
            elif qtype == 'ma':
                for key, val in options_data.items():
                    if key.startswith('pair') and val:
                        Options.objects.create(
                            question=newQ,
                            text=None,
                            pair={
                                'left': val.get('left'),
                                'right': val.get('right'),
                                'pairNum': val.get('pairNum')
                            },
                            order=val.get('pairNum', 0)
                        )
                    elif key.startswith('distraction') and val:
                        Options.objects.create(
                            question=newQ,
                            text=val.get('text'),
                            order=val.get('order', 0)
                        )

        # Save Feedback
        if feedback_data:
            for fb_item in feedback_data:
                try:
                    fb_user = User.objects.get(username=fb_item.get('username')) if fb_item.get('username') else None
                except User.DoesNotExist:
                    fb_user = None

                feedback,created = Feedback.objects.update_or_create(
                    id=fb_item.get('id'),
                    defaults ={
                        'question':newQ,
                        'user':fb_user,
                        'rating':fb_item.get('rating'),
                        'averageScore':fb_item.get('averageScore'),
                        'comments':fb_item.get('comments'),
                        'time':fb_item.get('time')
                    }
                    
                )

                for resp in fb_item.get('responses', []):
                    try:
                        resp_user = User.objects.get(username=resp.get('username')) if resp.get('username') else None
                    except User.DoesNotExist:
                        resp_user = None
                    FeedbackResponse.objects.update_or_create(
                        id=resp.get('id'),
                        defaults ={
                            'feedback':feedback,
                            'user':resp_user,
                            'text':resp.get('text'),
                            'date':resp.get('date')
                        }
                        
                    )

        return Response({'status': 'success', 'created': created, 'question_id': newQ.id})

    except Exception as e:
        import traceback
        print("Error in save_question:", traceback.format_exc())
        return Response({'error': f'Error saving question: {str(e)}'}, status=500)



@api_view(['POST'])
@transaction.atomic
def save_attachment(request):
    attachment_name = request.POST.get('attachment_name')
    attachment_file = request.FILES.get('attachment_file')
    owner_role = request.POST.get('ownerRole')

    if not attachment_name or not attachment_file:
        return Response({'error': 'Missing attachment name or file.'}, status=400)

    course = None
    textbook = None

    if owner_role == 'teacher':
        course_id = request.POST.get('courseID')
        try:
            course = Course.objects.get(course_id=course_id)
        except Course.DoesNotExist:
            return Response({'error': 'Course not found'}, status=400)

    elif owner_role == 'publisher':
        isbn = request.POST.get('isbn')
        try:
            textbook = Textbook.objects.get(isbn=isbn)
        except Textbook.DoesNotExist:
            return Response({'error': 'Textbook not found'}, status=400)

    else:
        return Response({'error': 'Invalid owner role'}, status=400)

    new_attachment = Attachment.objects.create(
        name=attachment_name,
        file=attachment_file,
        course=course,
        textbook=textbook
    )

    new_attachment.author = request.user
    new_attachment.save()


    return Response({
        'status': 'success',
        'created': True,
        'name': new_attachment.name,
        'url': new_attachment.file.url
    })


def get_template_list(field, suite):
    master_template_list = {}
    for instance in suite:
        if field == "course":
            identity = instance.course_id
        else:
            identity = instance.isbn
        master_template_list[identity] = {}

        templates = Template.objects.filter(**{field: instance})
        for t in templates:
            template_data = {
                "id": t.id,
                "name": t.name,
                "titleFont": t.titleFont,
                "titleFontSize": t.titleFontSize,
                "subtitleFont": t.subtitleFont,
                "subtitleFontSize": t.subtitleFontSize,
                "bodyFont": t.bodyFont,
                "bodyFontSize": t.bodyFontSize,
                "pageNumbersInHeader": t.pageNumbersInHeader,
                "pageNumbersInFooter": t.pageNumbersInFooter,
                "headerText": t.headerText,
                "footerText": t.footerText,
                "coverPageID": t.coverPageID or 0,
                "nameTag": t.nameTag or '',
                "dateTag": t.dateTag or '',
                "courseTag": t.courseTag or '',
                "partStructure": t.partStructure,  # JSON field handled by Django automatically
                "bonusSection": t.bonusSection,
                "bonusQuestions": t.bonusQuestions,
                "published": t.published,
                "feedback": [],
                "author": t.author.username if t.author else None
            }
            master_template_list[identity][str(template_data["id"])] = template_data
    return master_template_list

def get_question_list(field, suite):
    master_question_list = {}

    for instance in suite:
        if not instance:
            print("[get_question_list] Skipping null instance")
            continue

        # Identify the object
        identity = instance.course_id if field == "course" else instance.isbn
        
        question_lists = {
            'tf': {},
            'mc': {},
            'sa': {},
            'es': {},
            'ma': {},
            'ms': {},
            'fb': {},
            'dy': {}
        }

        master_question_list[identity] = question_lists

        try:
            questions = Question.objects.filter(**{field: instance}).select_related(
                'author'
            ).prefetch_related(
                'question_answers',
                'question_options',
                'feedbacks__user',
                'feedbacks__responses__user'
            )
        except Exception as e:
            print(f"[get_question_list] Failed to fetch questions for {identity}: {str(e)}")
            continue  # Skip to next instance

        for q in questions:
            try:
                # === Answers ===
                if q.qtype in ['tf', 'mc', 'es', 'sa']:
                    answer_obj = q.question_answers.first()
                    answer = {'value': answer_obj.text if answer_obj else None}
                elif q.qtype == 'fb':
                    answer = {f'blank{i+1}': {'value': a.text} for i, a in enumerate(q.question_answers.all())}
                elif q.qtype == 'ms':
                    answer = {f'option{i+1}': {'value': a.text} for i, a in enumerate(q.question_answers.all())}
                elif q.qtype == 'ma':
                    answer = {f'pair{i+1}': {'text': a.text} for i, a in enumerate(q.question_answers.all())}
                else:
                    answer = {f'answer{i+1}': {'value': a.text} for i, a in enumerate(q.question_answers.all())}
                 
                # === Options ===
                options = {}
                if q.qtype == 'tf':
                    options = {
                        'true': {'text': 'True', 'order': 1},
                        'false': {'text': 'False', 'order': 2}
                    }
                elif q.qtype == 'mc':
                    mc_letters = ['A', 'B', 'C', 'D']
                    for i, opt in enumerate(q.question_options.all()):
                        if i < len(mc_letters):
                            letter = mc_letters[i]
                            options[letter] = {
                                'text': opt.text,
                                'order': i + 1,
                                'image': opt.image.url if opt.image and hasattr(opt.image, 'url') and opt.image.name else None
                            }
                elif q.qtype == 'ms':
                    for i, opt in enumerate(q.question_options.all()):
                        options[f'option{i+1}'] = {
                            'text': opt.text,
                            'order': i + 1,
                            'image': opt.image.url if opt.image and hasattr(opt.image, 'url') and opt.image.name else None
                        }
                elif q.qtype == 'ma':
                    pair_count, distraction_count = 0, 0
                    for opt in q.question_options.all():
                        if hasattr(opt, 'pair') and isinstance(opt.pair, dict):
                            pair_count += 1
                            options[f'pair{pair_count}'] = {
                                'left': opt.pair.get('left'),
                                'right': opt.pair.get('right'),
                                'pairNum': pair_count
                            }
                        else:
                            distraction_count += 1
                            options[f'distraction{distraction_count}'] = {
                                'text': opt.text,
                                'order': distraction_count
                            }
                    options['numPairs'] = pair_count
                    options['numDistractions'] = distraction_count

                # === Images ===
                img_url = q.img.url if q.img and hasattr(q.img, 'url') and q.img.name else None
                ansimg_url = q.ansimg.url if q.ansimg and hasattr(q.ansimg, 'url') and q.ansimg.name else None

                # === Feedback ===
                feedback_list = []
                for f in q.feedbacks.all():
                    feedback_data = {
                        "id": f.id,
                        "username": f.user.username if f.user else "Anonymous",
                        "rating": f.rating,
                        "averageScore": float(f.averageScore) if f.averageScore else None,
                        "comments": f.comments,
                        "time": float(f.time) if f.time else None,
                        "date": f.created_at.isoformat() if f.created_at else None,
                        "responses": [
                            {
                                "id": r.id,
                                "username": r.user.username if r.user else "Anonymous",
                                "text": r.text,
                                "date": r.date.isoformat() if r.date else None
                            } for r in f.responses.all()
                        ]
                    }
                    feedback_list.append(feedback_data)

                # === Final data ===
                question_data = {
                    'id': q.id,
                    'text': q.text,
                    'answer': answer,
                    'qtype': q.qtype,
                    'score': float(q.score) if q.score else 0.0,
                    'directions': q.directions,
                    'reference': q.reference,
                    'reqRefs': q.requiredRefs,
                    'eta': q.eta,
                    'img': q.imgID,
                    'ansimg': q.ansimgID,
                    'parsedImg': img_url,
                    'parsedAnsImg': ansimg_url,
                    'comments': q.comments,
                    'options': options,
                    'chapter': q.chapter,
                    'section': q.section,
                    'published': q.published,
                    'author': q.author.username if q.author else None,
                    'feedback': feedback_list,
                    'tests': list(q.tests.values_list('id', flat=True))
                }

                if q.qtype in question_lists:
                    master_question_list[identity][q.qtype][q.id] = question_data
                else:
                    if 'other' not in master_question_list[identity]:
                        master_question_list[identity]['other'] = {}
                    master_question_list[identity]['other'][q.id] = question_data

            except Exception as inner_error:
                if "has no file associated with it" not in str(inner_error):
                    print(f"[get_question_list] Error processing question {q.id}: {str(inner_error)}")
                continue

    return master_question_list

def get_attachment_list(field, suite):
    master_attachment_list = {}
    for instance in suite:
        if field == "course":
            identity = instance.course_id
        else:
            identity = instance.isbn
        master_attachment_list[identity] = {}
        attachments = Attachment.objects.filter(**{field: instance})
        for a in attachments:
            file_name = None
            file_url = None
            
            if a.file and a.file.name:
                file_name = a.file.name
                try:
                    file_url = a.file.url
                except:
                    file_url = None
                
            attachment_data = {
                "id": a.id,
                "name": a.name,
                "file": file_name,
                "url": file_url,
            }
            master_attachment_list[identity][str(attachment_data["id"])] = attachment_data
    return master_attachment_list

def get_test_list(field, suite):
    master_test_list = {}
    
    for instance in suite:
        # Initialize test dictionary with drafts and published sections
        test_list = {
            'drafts': {},
            'published': {}
        }
        
        # Get all tests for this instance with optimized queries
        tests = Test.objects.filter(**{field: instance}).select_related('template').prefetch_related(
            'attachments',
            'parts__sections__testquestion_set__question',
            'feedbacks__responses'
        )
        
        for test in tests:
            # Get template if exists
            template = test.template
            
            # Basic test data structure matching frontend format
            test_data = {
                'id': test.id,
                'name': test.name,
                'templateName': template.name if template else None,
                'templateID': test.templateID,
                'refText': test.refText,
                'date': test.date.isoformat() if test.date else None,
                'filename': test.filename,
                'parts': [],
                'attachments': [],
                'feedback': [],
                'published': test.is_final,
                'author': test.author.username if test.author else None
            }
            
            # Process attachments
            for attachment in test.attachments.all():
                test_data['attachments'].append(attachment.id)
            
            # Process parts, sections, and questions
            for part in test.parts.all().order_by('part_number'):
                part_data = {
                    'partNumber': part.part_number,
                    'sections': []
                }
                
                # Process sections
                for section in part.sections.all().order_by('section_number'):
                    section_data = {
                        'sectionNumber': section.section_number,
                        'questionType': section.question_type,
                        'questions': []
                    }
                    
                    # Process questions
                    test_questions = TestQuestion.objects.filter(
                        test=test, 
                        section=section
                    ).select_related('question').order_by('order')
                    
                    for index, tq in enumerate(test_questions):
                        question_data = {
                            'id': tq.question.id,
                            'qtype': tq.question.qtype,
                            'assigned_points': float(tq.assigned_points) if tq.assigned_points else 1.0,
                            'order': index
                        }
                        section_data['questions'].append(question_data)
                    
                    part_data['sections'].append(section_data)
                
                test_data['parts'].append(part_data)
            
            # Process feedback
            for feedback in test.feedbacks.all():
                feedback_data = {
                    'id': feedback.id,
                    'username': feedback.user.username if feedback.user else 'Anonymous',
                    'rating': feedback.rating,
                    'averageScore': float(feedback.averageScore) if feedback.averageScore else None,
                    'comments': feedback.comments,
                    'time': feedback.time if feedback.time else None,
                    'date': feedback.created_at.isoformat() if feedback.created_at else None,
                    'responses': []
                }
                
                # Process responses
                for response in feedback.responses.all():
                    response_data = {
                        'id': response.id,
                        'username': response.user.username if response.user else 'Anonymous',
                        'text': response.text,
                        'date': response.date.isoformat() if response.date else None
                    }
                    feedback_data['responses'].append(response_data)
                
                test_data['feedback'].append(feedback_data)
            
            # Add to appropriate section based on finalized status
            if test.is_final:
                test_list['published'][test.id] = test_data
            else:
                test_list['drafts'][test.id] = test_data
        
        # Add to master test list with appropriate key
        owner_key = instance.course_id if field == 'course' else instance.isbn
        master_test_list[str(owner_key)] = test_list
    
    return master_test_list

def get_cpage_list(field, suite):
    master_cpage_list = {}
    for instance in suite:
        if field == "course":
            identity = instance.course_id
        else:
            identity = instance.isbn
        master_cpage_list[identity] = {}
        cpages = CoverPage.objects.filter(**{field: instance})
        for c in cpages:
            cpage_data = {
                "id": c.id,
                "name": c.name,
                "testNum": c.testNum,
                "date": c.date.isoformat() if c.date else None,
                "file": c.file,
                "showFilename": c.showFilename,
                "blank": c.blank,
                "instructions": c.instructions,
                "published": c.published,
                "feedback": [],
                "author": c.author.username if c.author else None
            }
            master_cpage_list[identity][str(cpage_data["id"])]=cpage_data
    return master_cpage_list


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if obj is None:
            return None
        
        # Handle Decimal to float conversion
        if isinstance(obj, Decimal):
            return float(obj)
        
        # Handle ImageField or FileField objects safely
        if isinstance(obj, FieldFile):
            try:
                return obj.url if obj.name else None
            except:
                return None
        
        # Handle datetime and date objects
        elif hasattr(obj, 'isoformat'):
            return obj.isoformat()
            
        # Handle model instances - convert to dict of ID and str representation
        elif isinstance(obj, models.Model):
            return {"id": obj.id, "str": str(obj)}
        
        # For any other unhandled objects, call the default method of the superclass
        return super().default(obj)


