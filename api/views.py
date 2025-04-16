from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import transaction
from django.contrib.auth.models import User
import json, os
from decimal import Decimal
from django.db.models.fields.files import FieldFile
from django.apps import apps
from datetime import datetime

from welcome.models import (
    Course, Textbook, Question, Test, Template, CoverPage, 
    Attachment, TestQuestion, Options, Answers, UserProfile,
    TestPart, TestSection, Feedback, FeedbackResponse
)

class ValidationError(Exception):
    """Exception for validation errors in the API views."""
    pass



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

    try:
        if role == "teacher":
            courses = Course.objects.filter(teachers=user).select_related('textbook')

            # Run this OUTSIDE the atomic block
            master_question_list = get_question_list('course', courses)

            with transaction.atomic():
                master_test_list = get_test_list('course', courses)
                master_template_list = get_template_list('course', courses)
                master_cpage_list = get_cpage_list('course', courses)
                master_attachment_list = get_attachment_list('course', courses)

                for course in courses:
                    textbook_data = None
                    if course.textbook:
                        textbook_data = {
                            "title": course.textbook.title,
                            "author": course.textbook.author,
                            "version": course.textbook.version,
                            "isbn": course.textbook.isbn,
                            "link": course.textbook.link
                        }

                    container_list[course.course_id] = {
                        "id": course.course_id,
                        "crn": course.crn,
                        "name": course.name,
                        "sem": course.sem,
                        "textbook": textbook_data,
                        "dbid": course.id
                    }

                    if course.textbook:
                        textbook = Textbook.objects.filter(isbn=course.textbook.isbn).first()
                        if textbook:
                            master_question_list = add_textbook_questions(
                                textbook, master_question_list, course.course_id
                            )

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
            "container_list": container_list
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
            title=datatext.get('title'),
            author=datatext.get('author'),
            version=datatext.get('version'),
            isbn=datatext.get('isbn'),
            link=datatext.get('link'),
            defaults={
                'title': datatext.get('title'),
                'author': datatext.get('author'),
                'version':datatext.get('version'),
                'isbn':datatext.get('isbn'),
                'link':datatext.get('link'),
            }
        )
    newtextbook.save()
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
        
        try:
            test_data = data.get('test', {})
        except Exception as e:
            return Response({'error': f'Error getting test data: {str(e)}. The "test" field might be None.'}, status=400)
        
        try:
            parts_data = data.get('parts', [])
        except Exception as e:
            return Response({'error': f'Error getting parts data: {str(e)}. The "parts" field might be None.'}, status=400)
        
        try:
            feedback_data = data.get('feedback', [])
        except Exception as e:
            return Response({'error': f'Error getting feedback data: {str(e)}. The "feedback" field might be None.'}, status=400)
        
        try:
            owner_role = data.get('ownerRole')
            if owner_role is None:
                return Response({'error': 'Owner role is None. Please provide an ownerRole.'}, status=400)
        except Exception as e:
            return Response({'error': f'Error getting owner role: {str(e)}. The "ownerRole" field might be None.'}, status=400)

        course = None
        textbook = None
        
        try:
            is_final = test_data.get("is_final")
            test_id = test_data.get("id")
            if is_final == True and test_id:
                return Response({'error': 'Test already finalized!'}, status=400)
        except Exception as e:
            return Response({'error': f'Error checking test finalization status: {str(e)}. The "is_final" or "id" field might be None.'}, status=400)

        # Determine ownership based on role
        if owner_role == 'teacher':
            try:
                owner_id = data.get('courseID')
                if owner_id is None:
                    return Response({'error': 'courseID is None for teacher role. Please provide a courseID.'}, status=400)
                try:
                    course = Course.objects.get(course_id=owner_id)
                except Course.DoesNotExist:
                    return Response({'error': 'Course not found'}, status=400)
            except Exception as e:
                return Response({'error': f'Error getting courseID: {str(e)}. The "courseID" field might be None.'}, status=400)
        elif owner_role == 'publisher':
            try:
                owner_id = data.get('isbn')
                if owner_id is None:
                    return Response({'error': 'isbn is None for publisher role. Please provide an isbn.'}, status=400)
                try:
                    textbook = Textbook.objects.get(isbn=owner_id)
                except Textbook.DoesNotExist:
                    return Response({'error': 'Textbook not found'}, status=400)
            except Exception as e:
                return Response({'error': f'Error getting isbn: {str(e)}. The "isbn" field might be None.'}, status=400)

        try:
            # Get template if templateIndex is provided
            template = None
            try:
                template_index = test_data.get('templateIndex', 0)
                if template_index > 0:
                    try:
                        template = Template.objects.get(id=template_index)
                    except Template.DoesNotExist:
                        return Response({'error': 'Template not found'}, status=400)
            except Exception as e:
                return Response({'error': f'Error getting templateIndex: {str(e)}. The "templateIndex" field might be None.'}, status=400)
            
            # Update or create the test
            try:
                test_id = test_data.get('id')
                test, created = Test.objects.update_or_create(
                    id=test_id if test_id else None,
                    defaults={
                        'name': test_data.get('name', 'Untitled Test'),
                        'date': test_data.get('date'),
                        'filename': test_data.get('filename'),
                        'is_final': test_data.get('is_final', False),
                        'templateIndex': test_data.get('templateIndex', 0),
                        'course': course,
                        'textbook': textbook,
                        'template': template
                    }
                )
            except Exception as e:
                return Response({'error': f'Error creating or updating test: {str(e)}. One of the test fields might be None.'}, status=400)

            if created:
                test.author = request.user
            test.save()
            
            # Process parts, sections, and questions
            if parts_data:
                # Keep track of processed parts to identify parts to delete
                processed_part_ids = []
                
                for part_data in parts_data:
                    try:
                        part_number = part_data.get('part_number')
                        if part_number is None:
                            return Response({'error': 'part_number is None. Please provide a part_number for each part.'}, status=400)
                    except Exception as e:
                        return Response({'error': f'Error getting part_number: {str(e)}. The "part_number" field might be None.'}, status=400)
                    
                    try:
                        sections_data = part_data.get('sections', [])
                    except Exception as e:
                        return Response({'error': f'Error getting sections: {str(e)}. The "sections" field might be None.'}, status=400)
                    
                    # Create or update part
                    try:
                        part, part_created = TestPart.objects.update_or_create(
                            test=test,
                            part_number=part_number,
                            defaults={}
                        )
                        processed_part_ids.append(part.id)
                    except Exception as e:
                        return Response({'error': f'Error creating or updating part: {str(e)}. The part data might be invalid.'}, status=400)
                    
                    # Process sections within the part
                    processed_section_ids = []
                    
                    for section_data in sections_data:
                        try:
                            section_number = section_data.get('section_number')
                            if section_number is None:
                                return Response({'error': 'section_number is None. Please provide a section_number for each section.'}, status=400)
                        except Exception as e:
                            return Response({'error': f'Error getting section_number: {str(e)}. The "section_number" field might be None.'}, status=400)
                        
                        try:
                            question_type = section_data.get('question_type')
                            if question_type is None:
                                return Response({'error': 'question_type is None. Please provide a question_type for each section.'}, status=400)
                        except Exception as e:
                            return Response({'error': f'Error getting question_type: {str(e)}. The "question_type" field might be None.'}, status=400)
                        
                        try:
                            questions_data = section_data.get('questions', [])
                        except Exception as e:
                            return Response({'error': f'Error getting questions: {str(e)}. The "questions" field might be None.'}, status=400)
                        
                        # Create or update section
                        try:
                            section, section_created = TestSection.objects.update_or_create(
                                part=part,
                                section_number=section_number,
                                defaults={
                                    'question_type': question_type
                                }
                            )
                            processed_section_ids.append(section.id)
                        except Exception as e:
                            return Response({'error': f'Error creating or updating section: {str(e)}. The section data might be invalid.'}, status=400)
                        
                        # Process questions within the section
                        processed_question_ids = []
                        
                        for question_data in questions_data:
                            if question_data is None:
                                continue
                            
                            try:
                                question_id = question_data.get('question_id')
                            except Exception as e:
                                return Response({'error': f'Error getting question_id: {str(e)}. The "question_id" field might be None.'}, status=400)
                            
                            # Handle existing question
                            if question_id:
                                try:
                                    try:
                                        question = Question.objects.get(id=question_id)
                                    except Question.DoesNotExist:
                                        return Response({'error': f'Question with id {question_id} not found'}, status=400)
                                    
                                    # Create or update test question link
                                    try:
                                        assigned_points = question_data.get('assigned_points', 1.0)
                                        order = question_data.get('order', 1)
                                        randomize = question_data.get('randomize', False)
                                        special_instructions = question_data.get('special_instructions')
                                        
                                        test_question, q_created = TestQuestion.objects.update_or_create(
                                            test=test,
                                            question=question,
                                            defaults={
                                                'assigned_points': assigned_points,
                                                'order': order,
                                                'randomize': randomize,
                                                'special_instructions': special_instructions,
                                                'section': section
                                            }
                                        )
                                        processed_question_ids.append(test_question.id)
                                    except Exception as e:
                                        return Response({'error': f'Error creating or updating test question: {str(e)}. The question data might be invalid.'}, status=400)
                                    
                                except Exception as e:
                                    return Response({'error': f'Error processing existing question: {str(e)}'}, status=400)
                            # Handle new question
                            elif question_data.get('text'):
                                try:
                                    # Create new question
                                    try:
                                        text = question_data.get('text', '')
                                        qtype = question_data.get('qtype', 'mc')
                                        score = question_data.get('assigned_points', 1.0)
                                        directions = question_data.get('directions')
                                        reference = question_data.get('reference')
                                        eta = question_data.get('eta', 1)
                                        comments = question_data.get('comments')
                                        chapter = question_data.get('chapter', 0)
                                        section_num = question_data.get('section', 0)
                                        published = question_data.get('published', False)
                                        
                                        question = Question.objects.create(
                                            text=text,
                                            qtype=qtype,
                                            score=score,
                                            directions=directions,
                                            reference=reference,
                                            eta=eta,
                                            comments=comments,
                                            chapter=chapter,
                                            section=section_num,
                                            published=published,
                                            course=course,
                                            textbook=textbook,
                                            author=request.user
                                        )
                                    except Exception as e:
                                        return Response({'error': f'Error creating new question: {str(e)}. The question data might be invalid.'}, status=400)
                                    
                                    # Create test question link
                                    try:
                                        assigned_points = question_data.get('assigned_points', 1.0)
                                        order = question_data.get('order', 1)
                                        randomize = question_data.get('randomize', False)
                                        special_instructions = question_data.get('special_instructions')
                                        
                                        test_question = TestQuestion.objects.create(
                                            test=test,
                                            question=question,
                                            assigned_points=assigned_points,
                                            order=order,
                                            randomize=randomize,
                                            special_instructions=special_instructions,
                                            section=section
                                        )
                                        processed_question_ids.append(test_question.id)
                                    except Exception as e:
                                        return Response({'error': f'Error creating test question link: {str(e)}. The test question data might be invalid.'}, status=400)
                                    
                                    # Handle answers based on question type
                                    try:
                                        answer_data = question_data.get('answer', {})
                                        if answer_data is None:
                                            return Response({'error': 'answer data is None. Please provide answer data.'}, status=400)
                                    except Exception as e:
                                        return Response({'error': f'Error getting answer data: {str(e)}. The "answer" field might be None.'}, status=400)
                                    
                                    try:
                                        qtype = question_data.get('qtype', 'mc')
                                    except Exception as e:
                                        return Response({'error': f'Error getting qtype: {str(e)}. The "qtype" field might be None.'}, status=400)
                                    
                                    if qtype in ['tf', 'mc', 'sa', 'es']:
                                        # These question types have a single answer
                                        try:
                                            if isinstance(answer_data, dict) and 'value' in answer_data:
                                                value = answer_data.get('value')
                                                Answers.objects.create(
                                                    question=question,
                                                    text=value
                                                )
                                        except Exception as e:
                                            return Response({'error': f'Error creating single answer: {str(e)}. The answer data might be invalid.'}, status=400)
                                    elif qtype == 'fb' or qtype == 'ms':
                                        # These can have multiple answers
                                        try:
                                            if isinstance(answer_data, dict):
                                                for key, value in answer_data.items():
                                                    if isinstance(value, dict) and 'value' in value:
                                                        answer_value = value.get('value')
                                                        Answers.objects.create(
                                                            question=question,
                                                            text=answer_value
                                                        )
                                        except Exception as e:
                                            return Response({'error': f'Error creating multiple answers: {str(e)}. The answer data might be invalid.'}, status=400)
                                    elif qtype == 'ma':
                                        # Matching has pairs
                                        try:
                                            if isinstance(answer_data, dict):
                                                for key, value in answer_data.items():
                                                    if isinstance(value, dict) and 'text' in value:
                                                        answer_text = value.get('text')
                                                        Answers.objects.create(
                                                            question=question,
                                                            text=answer_text
                                                        )
                                        except Exception as e:
                                            return Response({'error': f'Error creating matching answers: {str(e)}. The answer data might be invalid.'}, status=400)
                                    
                                    # Handle options based on question type
                                    try:
                                        options_data = question_data.get('options', {})
                                        if options_data is None:
                                            return Response({'error': 'options data is None. Please provide options data.'}, status=400)
                                    except Exception as e:
                                        return Response({'error': f'Error getting options data: {str(e)}. The "options" field might be None.'}, status=400)
                                    
                                    if qtype == 'tf':
                                        # True/False options
                                        try:
                                            Options.objects.create(
                                                question=question,
                                                text='True',
                                                order=1
                                            )
                                            Options.objects.create(
                                                question=question,
                                                text='False',
                                                order=2
                                            )
                                        except Exception as e:
                                            return Response({'error': f'Error creating True/False options: {str(e)}'}, status=400)
                                    elif qtype == 'mc':
                                        # Multiple choice options (A, B, C, D)
                                        try:
                                            mc_options = ['A', 'B', 'C', 'D']
                                            for letter in mc_options:
                                                if letter in options_data and isinstance(options_data[letter], dict):
                                                    option = options_data[letter]
                                                    option_text = option.get('text')
                                                    option_order = option.get('order', mc_options.index(letter) + 1)
                                                    Options.objects.create(
                                                        question=question,
                                                        text=option_text,
                                                        order=option_order
                                                    )
                                        except Exception as e:
                                            return Response({'error': f'Error creating multiple choice options: {str(e)}. The options data might be invalid.'}, status=400)
                                    elif qtype == 'ms':
                                        # Multiple selection options
                                        try:
                                            for key, value in options_data.items():
                                                if key.startswith('option') and isinstance(value, dict):
                                                    option_text = value.get('text')
                                                    option_order = value.get('order', 0)
                                                    Options.objects.create(
                                                        question=question,
                                                        text=option_text,
                                                        order=option_order
                                                    )
                                        except Exception as e:
                                            return Response({'error': f'Error creating multiple selection options: {str(e)}. The options data might be invalid.'}, status=400)
                                    elif qtype == 'ma':
                                        # Matching options (pairs and distractions)
                                        try:
                                            for key, value in options_data.items():
                                                if key.startswith('pair') and isinstance(value, dict):
                                                    pair_left = value.get('left')
                                                    pair_right = value.get('right')
                                                    pair_num = value.get('pairNum')
                                                    pair_data = {
                                                        'left': pair_left,
                                                        'right': pair_right,
                                                        'pairNum': pair_num
                                                    }
                                                    Options.objects.create(
                                                        question=question,
                                                        pair=pair_data,
                                                        order=pair_num if pair_num is not None else 0
                                                    )
                                                elif key.startswith('distraction') and isinstance(value, dict):
                                                    distraction_text = value.get('text')
                                                    distraction_order = value.get('order', 0)
                                                    Options.objects.create(
                                                        question=question,
                                                        text=distraction_text,
                                                        order=distraction_order
                                                    )
                                        except Exception as e:
                                            return Response({'error': f'Error creating matching options: {str(e)}. The options data might be invalid.'}, status=400)
                                except Exception as e:
                                    return Response({'error': f'Error processing new question: {str(e)}'}, status=400)
                        
                        # Remove questions that are no longer in the section
                        try:
                            TestQuestion.objects.filter(section=section).exclude(id__in=processed_question_ids).delete()
                        except Exception as e:
                            return Response({'error': f'Error cleaning up removed questions: {str(e)}'}, status=400)
                    
                    # Remove sections that are no longer in the part
                    try:
                        TestSection.objects.filter(part=part).exclude(id__in=processed_section_ids).delete()
                    except Exception as e:
                        return Response({'error': f'Error cleaning up removed sections: {str(e)}'}, status=400)
                
                # Remove parts that are no longer in the test
                try:
                    TestPart.objects.filter(test=test).exclude(id__in=processed_part_ids).delete()
                except Exception as e:
                    return Response({'error': f'Error cleaning up removed parts: {str(e)}'}, status=400)
            
            if feedback_data:
                for fb_item in feedback_data:
                    try:
                        if not fb_item or not isinstance(fb_item, dict):
                            continue
                    
                        # Get username safely
                        try:
                            username = fb_item.get('username')
                            feedback_user = None
                            if username:
                                try:
                                    feedback_user = User.objects.get(username=username)
                                except User.DoesNotExist:
                                    # User doesn't exist, continue with None
                                    pass
                        except Exception as e:
                            return Response({'error': f'Error getting username from feedback: {str(e)}. The "username" field might be None.'}, status=400)
                        
                        try:
                            rating = fb_item.get('rating')
                            avg_score = fb_item.get('averageScore')
                            comments = fb_item.get('comments')
                            time = fb_item.get('time')
                            
                            feedback = Feedback.objects.create(
                                test=test,
                                user=feedback_user,
                                rating=rating,
                                averageScore=avg_score,
                                comments=comments,
                                time=time
                            )
                        except Exception as e:
                            return Response({'error': f'Error creating feedback: {str(e)}. One of the feedback fields might be None.'}, status=400)
                    
                        # Handle responses to feedback - store responses list separately
                        try:
                            responses_list = fb_item.get('responses', [])
                            if responses_list is None:
                                return Response({'error': 'responses list is None. Please provide a valid responses list.'}, status=400)
                        except Exception as e:
                            return Response({'error': f'Error getting responses list: {str(e)}. The "responses" field might be None.'}, status=400)
                        
                        if responses_list and isinstance(responses_list, list):
                            for resp_item in responses_list:
                                try:
                                    if not resp_item or not isinstance(resp_item, dict):
                                        continue
                                
                                    # Get response username safely
                                    try:
                                        resp_username = resp_item.get('username')
                                        resp_user = None
                                        if resp_username:
                                            try:
                                                resp_user = User.objects.get(username=resp_username)
                                            except User.DoesNotExist:
                                                # User doesn't exist, continue with None
                                                pass
                                    except Exception as e:
                                        return Response({'error': f'Error getting username from response: {str(e)}. The "username" field might be None.'}, status=400)
                                    
                                    try:
                                        resp_text = resp_item.get('text')
                                        resp_date = resp_item.get('date')
                                        
                                        FeedbackResponse.objects.create(
                                            feedback=feedback,
                                            user=resp_user,
                                            text=resp_text,
                                            date=resp_date
                                        )
                                    except Exception as e:
                                        return Response({'error': f'Error creating feedback response: {str(e)}. One of the response fields might be None.'}, status=400)
                                except Exception as e:
                                    return Response({'error': f'Error processing feedback response: {str(e)}'}, status=400)
                    except Exception as e:
                        return Response({'error': f'Error processing feedback item: {str(e)}'}, status=400)
            
            return Response({
                'status': 'success',
                'created': created,
                'test_id': test.id,
                'test_name': test.name
            })
        
        except Exception as e:
            return Response({'error': f'Error processing test: {str(e)}'}, status=500)
        
    except Exception as e:
        return Response({'error': f'General error saving test: {str(e)}'}, status=500)


@api_view(['POST'])
@transaction.atomic
def save_course(request):
    try:
        data = request.data
        owner_role = data.get('ownerRole')
        course_data = data.get('course', {})
        textbook_data = data.get('textbook', {})
        
        # Process textbook data if available
        if textbook_data:
            textbook_id = textbook_data.get('id')
            if textbook_id and Textbook.objects.filter(id=textbook_id).exists():
                # Update existing textbook
                textbook = Textbook.objects.get(id=textbook_id)
                textbook.title = textbook_data.get('title', textbook.title)
                textbook.author = textbook_data.get('author', textbook.author)
                textbook.version = textbook_data.get('version', textbook.version)
                textbook.isbn = textbook_data.get('isbn', textbook.isbn)
                textbook.link = textbook_data.get('link', textbook.link)
                # Only update publisher if the user is a publisher
                if request.user.userprofile.role == 'publisher':
                    textbook.publisher = request.user
                textbook.published = textbook_data.get('published', textbook.published)
                textbook.save()
            else:
                # Create new textbook if textbook details provided
                isbn = textbook_data.get('isbn')
                title = textbook_data.get('title')
                author = textbook_data.get('author')
                version = textbook_data.get('version')
                link = textbook_data.get('link')
                published = textbook_data.get('published', False)
                
                # Try to find existing textbook by ISBN or create new one
                if isbn and Textbook.objects.filter(isbn=isbn).exists():
                    textbook = Textbook.objects.filter(isbn=isbn).first()
                elif title and author and Textbook.objects.filter(title=title, author=author).exists():
                    textbook = Textbook.objects.filter(title=title, author=author).first()
                else:
                    # Set publisher if user is a publisher, otherwise leave it null
                    publisher = request.user if request.user.userprofile.role == 'publisher' else None
                    textbook = Textbook.objects.create(
                        title=title or 'Untitled Textbook',
                        author=author,
                        version=version,
                        isbn=isbn,
                        link=link,
                        publisher=publisher,
                        published=published
                    )
        else:
            textbook = None
        
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
            if textbook:
                course.textbook = textbook
            course.save()
            created = False
        else:
            # Create new course
            course = Course.objects.create(
                course_id=course_data.get('course_id', 'Untitled Course'),
                name=course_data.get('name', 'Untitled Course'),
                crn=course_data.get('crn', ''),
                sem=course_data.get('sem', ''),
                textbook=textbook,
                published=course_data.get('published', False),
                user=request.user
            )
            created = True
        
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
                date=cover_page_data.get('date'),
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
        
        # Process template data
        template_id = template_data.get('id')
        if template_id and Template.objects.filter(id=template_id).exists():
            # Update existing template
            template = Template.objects.get(id=template_id)
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
            template.coverPageID = template_data.get('coverPageID', template.coverPageID)
            template.nameTag = template_data.get('nameTag', template.nameTag)
            template.dateTag = template_data.get('dateTag', template.dateTag)
            template.courseTag = template_data.get('courseTag', template.courseTag)
            template.partStructure = template_data.get('partStructure', template.partStructure)
            template.bonusSection = template_data.get('bonusSection', template.bonusSection)
            template.published = template_data.get('published', template.published)
            template.save()
            created = False
        else:
            # Create new template
            template = Template.objects.create(
                name=template_data.get('name', 'Untitled Template'),
                titleFont=template_data.get('titleFont', 'Arial'),
                titleFontSize=template_data.get('titleFontSize', 48),
                subtitleFont=template_data.get('subtitleFont', 'Arial'),
                subtitleFontSize=template_data.get('subtitleFontSize', 24),
                bodyFont=template_data.get('bodyFont', 'Arial'),
                bodyFontSize=template_data.get('bodyFontSize', 12),
                pageNumbersInHeader=template_data.get('pageNumbersInHeader', False),
                pageNumbersInFooter=template_data.get('pageNumbersInFooter', False),
                headerText=template_data.get('headerText'),
                footerText=template_data.get('footerText'),
                nameTag= template_data.get('nameTag', ''), 
                dateTag= template_data.get('dateTag', ''), 
                courseTag= template_data.get('courseTag', ''), 
                coverPageID= template_data.get('coverPageID'),
                partStructure=template_data.get('partStructure'),
                bonusSection=template_data.get('bonusSection', False),
                published=template_data.get('published', False),
                course=course,
                textbook=textbook
            )
            template.author = request.user;
            template.save()
            created = True
        
        return Response({
            'status': 'success',
            'created': created,
            'template_id': template.id,
            'name': template.name
        })
    except Exception as e:
        return Response({'error': str(e)}, status=400)

from django.core.files.uploadedfile import InMemoryUploadedFile

@api_view(['POST'])
@transaction.atomic
def save_question(request):
    data = request.data
    question_data = data.get('question', {})
    answer_data = data.get('answer', {})
    options_data = data.get('options', {})
    feedback_data = data.get('feedback', [])
    owner_role = data.get('ownerRole')

    course = None
    textbook = None

    if question_data.get("published") == True:
        return Response({'error': 'Already published!'}, status=400)

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
        newQ.course = course
        newQ.textbook = textbook

        # Safe image field handling
        img = question_data.get('img')
        newQ.img = img if isinstance(img, (InMemoryUploadedFile, type(None))) else None

        ansimg = question_data.get('ansimg')
        newQ.ansimg = ansimg if isinstance(ansimg, (InMemoryUploadedFile, type(None))) else None

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

                feedback = Feedback.objects.create(
                    question=newQ,
                    user=fb_user,
                    rating=fb_item.get('rating'),
                    averageScore=fb_item.get('averageScore'),
                    comments=fb_item.get('comments'),
                    time=fb_item.get('time')
                )

                for resp in fb_item.get('responses', []):
                    try:
                        resp_user = User.objects.get(username=resp.get('username')) if resp.get('username') else None
                    except User.DoesNotExist:
                        resp_user = None

                    FeedbackResponse.objects.create(
                        feedback=feedback,
                        user=resp_user,
                        text=resp.get('text'),
                        date=resp.get('date')
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
                "published": t.published,
                "feedback": []
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
                    'eta': q.eta,
                    'img': img_url,
                    'ansimg': ansimg_url,
                    'comments': q.comments,
                    'options': options,
                    'chapter': q.chapter,
                    'section': q.section,
                    'published': q.published,
                    'author': q.author.username if q.author else None,
                    'feedback': feedback_list
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
        # Optimize database queries with select_related and prefetch_related
        test_list = {}
        test_list = {
            'drafts': {},
            'published': {}
        }
        tests = Test.objects.filter(**{field: instance}).select_related('template').prefetch_related(
            'attachments',
            'parts__sections__testquestion_set__question__question_answers',
            'parts__sections__testquestion_set__question__question_options',
            'feedbacks__user',
            'feedbacks__responses__user'
        )
        
        for t in tests:
            test_data = {
                'id': t.id,
                'name': t.name,
                'template': t.template.id if t.template else None,
                'templateName': t.template.name if t.template else None,
                'templateIndex': t.templateIndex,
                'date': t.date.isoformat() if t.date else None,
                'filename': t.filename,
                'attachments': [],
                'parts': [],
                'published': t.is_final,
                'feedback': [],
                # Include ownerData for consistency with front-end
                'ownerData': {
                    'courseID': instance.course_id if field == 'course' else None,
                    'isbn': instance.isbn if field == 'textbook' else None
                }
            }
            
            # Process attachments
            for a in t.attachments.all():
                file_name = None
                file_url = None
                
                if a.file and a.file.name:
                    file_name = a.file.name
                    try:
                        file_url = a.file.url
                    except:
                        file_url = None
                        
                test_data['attachments'].append({
                    'id': a.id,
                    'name': a.name,
                    'file': file_name,
                    'url': file_url
                })
            
            
            # Get parts - using the prefetched data
            for p in t.parts.all().order_by('part_number'):
                part_data = {
                    'id': p.id,
                    'partNumber': p.part_number,
                    'part_number': p.part_number,  # Include both formats for compatibility
                    'sections': []
                }
                
                # Get sections for each part - using the prefetched data
                for s in p.sections.all().order_by('section_number'):
                    section_data = {
                        'id': s.id,
                        'sectionNumber': s.section_number,
                        'section_number': s.section_number,  # Include both formats for compatibility
                        'questionType': s.question_type,
                        'question_type': s.question_type,  # Include both formats for compatibility
                        'questions': []
                    }
                    
                    # Get questions for this section
                    test_questions = TestQuestion.objects.filter(test=t, section=s).select_related('question').order_by('order')
                    for tq in test_questions:
                        question = tq.question
                        
                        # Format answers based on question type
                        answers_list = list(question.question_answers.all())
                        answer_data = {}
                        
                        # Format answer based on question type
                        if question.qtype in ['tf', 'mc', 'sa', 'es']:
                            # These have a single answer
                            answer_data = {'value': answers_list[0].text if answers_list else None}
                        elif question.qtype in ['fb', 'ms']:
                            # These can have multiple answers
                            for i, ans in enumerate(answers_list):
                                answer_data[f'answer{i+1}'] = {'value': ans.text}
                        elif question.qtype == 'ma':
                            # Matching has pairs
                            for i, ans in enumerate(answers_list):
                                answer_data[f'pair{i+1}'] = {'text': ans.text}
                        
                        # Format options based on question type
                        options_list = list(question.question_options.all())
                        options_data = {}
                        
                        if question.qtype == 'tf':
                            # True/False options
                            options_data = {
                                'true': {'text': 'True', 'order': 1},
                                'false': {'text': 'False', 'order': 2}
                            }
                        elif question.qtype == 'mc':
                            # Multiple choice options (A, B, C, D)
                            mc_options = ['A', 'B', 'C', 'D']
                            for i, opt in enumerate(options_list[:4]):
                                letter = mc_options[i]
                                options_data[letter] = {
                                    'text': opt.text,
                                    'order': i + 1
                                }
                                if opt.image and opt.image.name:
                                    try:
                                        options_data[letter]['image'] = opt.image.url
                                    except:
                                        options_data[letter]['image'] = None
                        elif question.qtype == 'ms':
                            # Multiple selection options
                            for i, opt in enumerate(options_list):
                                options_data[f'option{i+1}'] = {
                                    'text': opt.text,
                                    'order': opt.order or i+1
                                }
                        elif question.qtype == 'ma':
                            # Matching options (pairs and distractions)
                            pair_count = 0
                            distraction_count = 0
                            
                            for opt in options_list:
                                if hasattr(opt, 'pair') and opt.pair:
                                    pair_count += 1
                                    options_data[f'pair{pair_count}'] = {
                                        'left': opt.pair.get('left'),
                                        'right': opt.pair.get('right'),
                                        'pairNum': opt.pair.get('pairNum') or pair_count
                                    }
                                else:
                                    distraction_count += 1
                                    options_data[f'distraction{distraction_count}'] = {
                                        'text': opt.text,
                                        'order': opt.order or distraction_count
                                    }
                            
                            options_data['numPairs'] = pair_count
                            options_data['numDistractions'] = distraction_count
                        
                        # Safe handling of image fields
                        img_url = None
                        if question.img and question.img.name:
                            try:
                                img_url = question.img.url
                            except:
                                img_url = None
                                
                        ansimg_url = None
                        if question.ansimg and question.ansimg.name:
                            try:
                                ansimg_url = question.ansimg.url
                            except:
                                ansimg_url = None
                
                        # Format question with the structure expected by the front-end
                        question_data = {
                            'id': question.id,
                            'test_question_id': tq.id,
                            'text': question.text,
                            'answer': answer_data,
                            'qtype': question.qtype,
                            'score': float(tq.assigned_points) if tq.assigned_points else float(question.score),
                            'assigned_points': float(tq.assigned_points) if tq.assigned_points else float(question.score),
                            'directions': question.directions,
                            'reference': question.reference,
                            'eta': question.eta,
                            'img': img_url,
                            'ansimg': ansimg_url,
                            'comments': question.comments,
                            'prompts': [],
                            'options': options_data,
                            'chapter': question.chapter,
                            'section': question.section,
                            'published': question.published,
                            'order': tq.order,
                            'randomize': tq.randomize,
                            'special_instructions': tq.special_instructions
                        }
                        
                        section_data['questions'].append(question_data)
                    
                    part_data['sections'].append(section_data)
                
                test_data['parts'].append(part_data)
            
            # Get feedback for test
            for f in t.feedbacks.all():
                feedback_data = {
                    "id": f.id,
                    "username": f.user.username if f.user else "Anonymous",
                    "rating": f.rating,
                    "averageScore": float(f.averageScore) if f.averageScore else None,
                    "comments": f.comments,
                    "date": f.created_at.isoformat() if f.created_at else None,
                    "time": f.created_at.isoformat() if f.created_at else None,  # Include both for compatibility
                    "responses": []
                }
                
                # Get responses to feedback
                for r in f.responses.all():
                    response_data = {
                        "id": r.id,
                        "username": r.user.username if r.user else "Anonymous",
                        "text": r.text,
                        "date": r.date.isoformat() if r.date else None
                    }
                    feedback_data["responses"].append(response_data)
                
                test_data['feedback'].append(feedback_data)
            
            # Add test to proper list based on its publication status
            if t.is_final:
                test_list['published'][t.id] = test_data
            else:
                test_list['drafts'][t.id] = test_data
        if field == 'course':
            owner = instance.course_id
        else:
            owner = instance.isbn
        master_test_list[str(owner)] = test_list

    
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
                "feedback": []
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



def add_textbook_questions(textbook, master_question_list, course_id):
    """
    Add questions from a textbook to the master question list for a course
    that is associated with that textbook.
    
    Args:
        textbook: Textbook object
        master_question_list: Dictionary containing all questions
        course_id: ID of the course to associate questions with
    
    Returns:
        Updated master_question_list with textbook questions
    """
    # Get all published questions from the textbook
    textbook_questions = Question.objects.filter(
        textbook=textbook,
        published=True
    ).select_related('author')
    
    # Process each question
    for question in textbook_questions:
        # Check if the question is already in the master list
        if str(question.id) not in master_question_list:
            # Get answers for this question
            answers = Answers.objects.filter(question=question)
            answers_data = {}
            
            # Process answers based on question type
            if question.qtype in ['tf', 'mc', 'sa', 'es']:
                # These question types have a single answer
                if answers.exists():
                    answers_data = {'value': answers.first().text}
            elif question.qtype == 'fb':
                # Fill in the blank can have multiple answers
                for i, answer in enumerate(answers):
                    answers_data[f'blank{i+1}'] = {'value': answer.text}
            elif question.qtype == 'ma':
                # Matching has pairs
                for i, answer in enumerate(answers):
                    answers_data[f'pair{i+1}'] = {
                        'text': answer.text,
                        'pair': answer.pair
                    }
            elif question.qtype == 'ms':
                # Multiple selection can have multiple correct answers
                for i, answer in enumerate(answers):
                    answers_data[f'option{i+1}'] = {'value': answer.text}
            
            # Get options for this question
            options = Options.objects.filter(question=question)
            options_data = {}
            
            # Process options based on question type
            if question.qtype == 'tf':
                # True/False options are standard
                pass
            elif question.qtype == 'mc':
                # Multiple choice options - map order to letters without assuming all exist
                # Define the mapping from order to option letter
                order_to_letter = {
                    1: 'A', 2: 'B', 3: 'C', 4: 'D'
                }
                
                for option in options:
                    if option.order in order_to_letter:
                        letter = order_to_letter[option.order]
                        options_data[letter] = {
                            'text': option.text, 
                            'order': option.order
                        }
            elif question.qtype == 'ms':
                # Multiple selection options
                for i, option in enumerate(options):
                    options_data[f'option{i+1}'] = {
                        'text': option.text,
                        'order': option.order
                    }
            elif question.qtype == 'ma':
                # Matching options
                pair_count = 0
                distraction_count = 0
                
                for option in options:
                    if option.pair:
                        pair_count += 1
                        options_data[f'pair{pair_count}'] = {
                            'left': option.pair.get('left', ''),
                            'right': option.pair.get('right', ''),
                            'pairNum': option.pair.get('pairNum', pair_count)
                        }
                    else:
                        distraction_count += 1
                        options_data[f'distraction{distraction_count}'] = {
                            'text': option.text,
                            'order': option.order
                        }
            
            # Add the question to the master list with the course_id as a reference
            qtype = str(question.qtype)
            qid = str(question.id)
            if qtype not in master_question_list:
                master_question_list[qtype] = {}

            master_question_list[qtype][qid]= {
                'id': str(question.id),
                'text': question.text,
                'qtype': question.qtype,
                'score': float(question.score),
                'directions': question.directions,
                'reference': question.reference,
                'eta': question.eta,
                'img': question.img,
                'ansimg': question.ansimg,
                'comments': question.comments,
                'chapter': question.chapter,
                'section': question.section,
                'published': question.published,
                'author': question.author.username if question.author else None,
                'owner_type': 'textbook',
                'owner_id': textbook.isbn,
                'course_id': course_id,  
                'answers': answers_data,
                'options': options_data
            }
    
    return master_question_list
