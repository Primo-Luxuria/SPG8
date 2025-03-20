import urllib.parse
import xml.etree.ElementTree as ET
import zipfile

from bs4 import BeautifulSoup
from django.core.files.base import ContentFile
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.middleware.csrf import get_token
from django.contrib.auth.models import User
from django.contrib import messages

from welcome.models import *

import json
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .models import Course  # Import additional models as needed


def home(request):
    return render(request, 'welcome/home.html')

def signup_handler(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        passwordconfirm = request.POST.get("passwordconfirm")
        role = request.POST.get("role")

        # Check if passwords match
        if password != passwordconfirm:
            messages.error(request, "Passwords do not match.")
            return redirect("signup")  # Changed to redirect to view, not handler

        # Check if the username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect("signup")  # Changed to redirect to view, not handler

        # Create new user
        user = User.objects.create_user(username=username, password=password)

        # Create and save user profile with the selected role
        user_profile = UserProfile(user=user, role=role)
        user_profile.save()  # Save the profile after setting the role

        messages.success(request, "Account created successfully!")

        # Redirect based on role
        if role == "teacher":
            return redirect("teacher_dashboard")
        elif role == "publisher":
            return redirect("publisher_dashboard")
        else:
            return redirect("webmaster_dashboard")  # Add a case for 'webmaster' if needed

    return render(request, "welcome/signup.html")



def login_handler(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        if not username or not password:
            messages.error(request, "Username and password are required.")
            return redirect("login")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)  # Log the user in
            
            # Get role from UserProfile
            try:
                role = user.userprofile.role
            except:
                role = "user"  # Default fallback
            
            # Redirect based on role
            if role == "teacher":
                return redirect("teacher_dashboard")
            elif role == "publisher":
                return redirect("publisher_dashboard")
            else:
                return redirect("home")  # Default fallback
        else:
            messages.error(request, "Invalid username or password")
            return redirect("login")
    
    return redirect("login")  # Redirect if not POST


def parse_qti_xml(request):
    """
    Parses a QTI XML file and saves extracted data to the database.
    """

    class ImageDataPair:
        def __init__(self, raw_image_data, actual_image_name):
            self.raw_image_data = raw_image_data
            self.actual_image_name = actual_image_name

    # Function to remove namespaces
    def remove_namespace(given_tree):
        for elem in given_tree.iter():
            if "}" in elem.tag:
                elem.tag = elem.tag.split("}")[-1]

    # creates a new question record/entry
    def create_question(g_course, g_q_type, g_q_text, g_points, g_g_f_t, g_f_g, g_f_t):
        temp_question_instance = Question.objects.create(
            course=g_course,
            question_type=g_q_type,
            question_text=g_q_text,
            default_points=g_points,
            general_feedback_text=g_g_f_t,
            feedback_graphic=g_f_g,
            feedback_type=g_f_t,
            # z
        )

        return temp_question_instance

    def check_embedded_graphic(text_q):
        # Parse the HTML using BeautifulSoup4 library
        soup = BeautifulSoup(text_q, 'html.parser')
        # Find the <img> tag
        img_element = soup.find('img')
        found_the_image = False
        if img_element:  # if we find an embedded image
            temp_file_path1 = img_element.get('src')  # gets the src attribute of img element
            url_encoded_path = temp_file_path1[18:]  # length of "$IMS-CC-FILEBASE$/" is 18
            decoded_path = urllib.parse.unquote(url_encoded_path)  # this decodes URL-encoded path

            for potential_image_name in filename_list:  # this assumes an outer function has: filename_list = zip_ref.namelist()
                if potential_image_name.endswith(decoded_path):
                    found_the_image = True
                    my_image_name = img_element.get('alt')
                    with zip_ref.open(potential_image_name) as desired_img_file:  # open the image file
                        img_data = desired_img_file.read()  # this is the raw image data
                        data_to_return = ImageDataPair(img_data, my_image_name)
            if not found_the_image:
                print('Desired image not found')  # used for debugging
        if img_element is None or found_the_image == False:
            return None
        else:
            return data_to_return

    def parse_just_xml(meta_path, non_meta_path, the_course):

        print(f"processing file: {meta_path}")
        # path to metadata file
        xml_file_path = meta_path
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        remove_namespace(root)

        cover_instructions_text = root.find('.//description').text

        print(f"processing file: {non_meta_path}")
        # Path to the questions file
        xml_file_path = non_meta_path
        tree = ET.parse(xml_file_path)
        root = tree.getroot()

        namespace = {"ns": "http://www.imsglobal.org/xsd/ims_qtiasiv1p2"}

        # Remove namespaces
        remove_namespace(root)
        # Find the 'assessment' element
        my_tag = "assessment"
        node = root.find(my_tag)

        if node is None:
            return JsonResponse({"error": f"Element '{my_tag}' not found in XML!"}, status=400)

        # Extract 'ident' and 'title' attribute from the element that node represents
        the_test_title = node.get("title")
        test_identifier = node.get("ident")

        # Create a new Test record
        test_instance = Test.objects.create(
            course=the_course,
            title=the_test_title,
            test_number=test_identifier,
            cover_instructions=cover_instructions_text
        )

        for section in root.findall(".//section"):
            for item in section.findall(".//item"):

                # all useful metadata fiels are found in the fieldentry elements under itemmetadata
                node = item.find('itemmetadata')
                qti_metadata_fields = node.findall(".//fieldentry")

                node = item.find('presentation')

                temp_node = node.find('material')  # possibly redundant statement
                temp_node = temp_node.find(".//mattext")
                # question_text_field contains the question prompt text
                question_text_field = temp_node.text

                # each response has an ID represented as "ident" in the XML
                # the ID is used to know what the correct response is
                correct_answer_ident = None

                the_question_type = qti_metadata_fields[0].text
                max_points_for_question = float(qti_metadata_fields[1].text)

                # node should currently be already = element w 'presentation' tag
                # MultiChoice & TF might be able to be combined. For now, they are separate
                if the_question_type == 'multiple_choice_question':
                    #
                    node = node.find('.//response_lid')
                    answer_choices_dict = {}
                    for response_label_elem in node.findall('.//response_label'):
                        response_ident = response_label_elem.get('ident')
                        response_text = response_label_elem.find('.//mattext').text
                        answer_choices_dict[response_ident] = response_text

                    node = item.find('resprocessing')
                    for respcondition_elem in node.findall('.//respcondition'):
                        if respcondition_elem.get('continue') == "No":
                            temp_node = respcondition_elem.find('.//varequal')
                            correct_answer_ident = temp_node.text

                    # this creates a question record in database
                    question_instance = create_question(the_course, the_question_type, question_text_field,
                                                        max_points_for_question, None, None, None)

                    image_data_pair = check_embedded_graphic(question_text_field)
                    if image_data_pair is not None:
                        # Save the image to the embedded_graphic field, then update the record/entry
                        question_instance.embedded_graphic.save(image_data_pair.actual_image_name,
                                                                ContentFile(image_data_pair.raw_image_data))
                        question_instance.save()
                        print(f"{question_instance.embedded_graphic.url}")

                    for key, value in answer_choices_dict.items():
                        answeroption_instance = AnswerOption.objects.create(
                            question=question_instance,
                            text=value,
                            is_correct=True if key == correct_answer_ident else False  # Inline conditional check
                        )

                elif the_question_type == 'true_false_question':
                    node = node.find('.//response_lid')
                    answer_choices_dict = {}
                    for response_label_elem in node.findall('.//response_label'):
                        response_ident = response_label_elem.get('ident')
                        response_text = response_label_elem.find('.//mattext').text
                        answer_choices_dict[response_ident] = response_text

                    node = item.find('resprocessing')
                    for respcondition_elem in node.findall('.//respcondition'):
                        if respcondition_elem.get('continue') == "No":
                            temp_node = respcondition_elem.find('.//varequal')
                            correct_answer_ident = temp_node.text

                    question_instance = create_question(the_course, the_question_type, question_text_field,
                                                        max_points_for_question, None, None, None)

                    for key, value in answer_choices_dict.items():
                        answeroption_instance = AnswerOption.objects.create(
                            question=question_instance,
                            text=value,
                            is_correct=True if key == correct_answer_ident else False  # Inline conditional check
                        )
                elif the_question_type == 'short_answer_question':  # Fill-in-the-blank question

                    question_instance = create_question(
                        the_course, the_question_type, question_text_field,
                        max_points_for_question, None, None, None
                    )

                    node = item.find('resprocessing')
                    for respcondition_elem in node.findall('.//respcondition'):
                        if respcondition_elem.get('continue') == "No":
                            for varequal_elem in respcondition_elem.findall('.//varequal'):
                                answeroption_instance = AnswerOption.objects.create(
                                    question=question_instance,
                                    text=varequal_elem.text,
                                    is_correct=True
                                )

                elif the_question_type == 'fill_in_multiple_blanks_question':
                    print('')  # this is placeholder for code to extract info from question for table
                elif the_question_type == 'multiple_answers_question':
                    correct_answer_ident_list = []
                    node = node.find('.//response_lid')
                    answer_choices_dict = {}
                    for response_label_elem in node.findall('.//response_label'):
                        response_ident = response_label_elem.get('ident')
                        response_text = response_label_elem.find('.//mattext').text
                        answer_choices_dict[response_ident] = response_text

                    node = item.find('resprocessing')
                    for respcondition_elem in node.findall('.//respcondition'):
                        if respcondition_elem.get('continue') == "No":
                            for varequal_elem in respcondition_elem.find('conditionvar').find('and').findall(
                                    'varequal'):
                                correct_answer_ident_list.append(varequal_elem.text)

                    question_instance = create_question(the_course, the_question_type, question_text_field,
                                                        max_points_for_question, None, None, None)

                    for key, value in answer_choices_dict.items():
                        answeroption_instance = AnswerOption.objects.create(
                            question=question_instance,
                            text=value,
                            is_correct=True if key in correct_answer_ident_list else False  # Check if key is in list
                        )

                elif the_question_type == 'multiple_dropdowns_question':
                    print('')  # this is placeholder for code to extract info from question for table
                elif the_question_type == 'matching_question':
                    print('')  # this is placeholder for code to extract info from question for table
                elif the_question_type == 'numerical_question':
                    print('')  # this is placeholder for code to extract info from question for table
                elif the_question_type == 'calculated_question':
                    print('')  # this is placeholder for code to extract info from question for table
                elif the_question_type == 'essay_question':
                    # mostly done but may need to process feedbacks or comments

                    print('')
                elif the_question_type == 'file_upload_question':
                    # should be done but may need to process feedbacks or comments

                    print('')
                elif the_question_type == 'text_only_question':
                    # placeholder for any future changes, but 99.9% sure this is done

                    print('')

                #

    # file_info is just used for testing. remove after (probably)
    # for now, what the Parser returns depends on this
    file_info = None

    uploaded_file = None

    # """
    # 00 Begin
    # Code in triple quotes is used for when merged with frontend
    # "file" in request.FILES.get("file") changes or depends on something in the HTML/javascript form
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_file = request.FILES["file"]  # Get the uploaded file
        print("File uploaded:", uploaded_file.name)

        file_info = {
            "filename": uploaded_file.name,
            "size": uploaded_file.size
        }
    else:
        print("No file uploaded to website.")

    if uploaded_file is None:
        return JsonResponse({"message": "No file uploaded or it doesn't exist.", "file_info": file_info})

    course_id = request.POST.get("courseID")
    course_name = request.POST.get("courseName")
    course_crn = request.POST.get("courseCRN")  # not in database
    course_semester = request.POST.get("courseSemester")  # not in database
    course_textbook_title = request.POST.get("courseTextbookTitle")
    course_textbook_author = request.POST.get("courseTextbookAuthor")
    course_textbook_version = request.POST.get("courseTextbookVersion")  # not in database
    course_textbook_isbn = request.POST.get("courseTextbookISBN")
    course_textbook_link = request.POST.get("courseTextbookLink")

    course_instance, created = Course.objects.get_or_create(
        course_code=course_id,
        defaults={
            "course_name": course_name,
            "textbook_title": course_textbook_title,
            "textbook_author": course_textbook_author,
            "textbook_isbn": course_textbook_isbn,
            "textbook_link": course_textbook_link,
        }
    )

    print(course_id)
    print(course_name)
    print(course_instance)

    # 00 End
    # """

    # this is used to stop removing and adding "#" when switching between tests
    if uploaded_file is None:
        path_to_zip_file = 'qti sample w one quiz-slash-test w all typesofquestions.zip'
        # path_to_zip_file = 'added response feedback.zip'

        # Get the first available course (REMOVE AFTER TESTING)
        course_instance = Course.objects.first()

        # Used for testing. Remove after
        if course_instance is None:
            course_instance = Course.objects.create(
                course_code='CS123',
                course_name='placeholder_course',
                textbook_title='placeholder Tb title',
                textbook_author='placeholder author',
                textbook_isbn='placeholder isbn',
                textbook_link='placeholder Tb link'
            )
    else:
        path_to_zip_file = uploaded_file

    with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
        # List all files inside the zip file
        filename_list = zip_ref.namelist()

        for file_name in filename_list:

            # looks for folders that are direct children of the zipfile
            if file_name.endswith('/'):

                temp_file_list = []

                # looks for files that are children of the found folder, then adds them to a list
                for temp_filename in filename_list:
                    if temp_filename.startswith(f'{file_name}') and (temp_filename != file_name):
                        temp_file_list.append(temp_filename)

                # if a folder is not empty, process the files in it with the parser
                if temp_file_list and len(temp_file_list) >= 2 and temp_file_list[0].endswith('.xml') and \
                        temp_file_list[1].endswith('.xml'):
                    # sort the files in the list because the metadata file for assessments is always
                    # named assessment_meta.xml, but the file with questions seems to always
                    # start with the letter "g"
                    temp_file_list = sorted(temp_file_list)
                    assessment_meta_path = temp_file_list[0]
                    questions_file_path = temp_file_list[1]

                    with zip_ref.open(assessment_meta_path) as outer_file:
                        with zip_ref.open(questions_file_path) as inner_file:
                            outer_file.seek(0)  # Reset file pointer
                            inner_file.seek(0)

                            # this calls the function that actually handles the parsing
                            parse_just_xml(outer_file, inner_file, course_instance)
                            #

    #

    # this is here because the javascript that calls the Parser depends on what it returns
    if file_info is None:
        return JsonResponse({"Success": "created Test record."}, status=555)
    else:
        return JsonResponse({"message": "File processed successfully!", "file_info": file_info})
#


# testing connecting the html files


#each of these functions renders a different html file

def login_view(request):
    return render(request, 'welcome/login.html')

def signup_view(request):
    return render(request, 'welcome/signup.html')

def teacher_dashboard(request):
    return render(request, 'welcome/SBteacher.html')

def publisher_dashboard(request):
    return render(request, 'welcome/SBpublisher.html')




"""
Beginning to test the frontend to the backend connection
"""

# function to handle the signup form
def signup_handler(request):

    # 
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        passwordconfirm = request.POST.get('passwordconfirm')
        role = request.POST.get('role')
        
        # Check if passwords match
        if password != passwordconfirm:
            messages.error(request, "Passwords do not match.")
            return redirect('signup')  # Assumes you have a URL named 'signup' for the signup page

        try:
            # Create the new user
            user = User.objects.create_user(username=username, password=password)
            user.save()
            
            # Create the user profile with the role chosen
            profile = UserProfile.objects.create(user=user, role=role)
            profile.save()
            return redirect('home')  # Redirect to the home page or another page of your choice
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            return redirect('signup')
    else:
        # For a GET request, simply render the signup form
        return render(request, 'signup.html')




"""
The teacher view
"""
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from .models import (
    Course, Book, Question, Test, Template, CoverPage, 
    Attachment, TestQuestion, AnswerOption, MatchingOption
)
from .serializers import (
    CourseSerializer, BookSerializer, QuestionSerializer, 
    TestSerializer, TemplateSerializer, CoverPageSerializer, 
    AttachmentSerializer
)

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    
    @action(detail=True, methods=['get'])
    def full_data(self, request, pk=None):
        """Get all data related to a course in one request."""
        course = self.get_object()
        data = {
            'course': CourseSerializer(course).data,
            'book': BookSerializer(course.book).data if course.book else None,
            'questions': QuestionSerializer(course.question_set.all(), many=True).data,
            'tests': TestSerializer(course.tests.all(), many=True).data,
            'templates': TemplateSerializer(course.template_set.all(), many=True).data,
            'cover_pages': CoverPageSerializer(course.coverpage_set.all(), many=True).data,
            'attachments': AttachmentSerializer(course.attachment_set.all(), many=True).data
        }
        return Response(data)

@api_view(['POST'])
def sync_course_data(request):
    """Synchronize frontend data with the database."""
    course_id = request.data.get('course_id')
    
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Update course and related objects
    course_data = request.data.get('course', {})
    if course_data:
        course_serializer = CourseSerializer(course, data=course_data, partial=True)
        if course_serializer.is_valid():
            course_serializer.save()
    
    # Handle questions
    question_data = request.data.get('questions', [])
    for q_data in question_data:
        q_id = q_data.get('id')
        if q_id:
            try:
                question = Question.objects.get(id=q_id)
                serializer = QuestionSerializer(question, data=q_data, partial=True)
            except Question.DoesNotExist:
                serializer = QuestionSerializer(data=q_data)
            
            if serializer.is_valid():
                question = serializer.save(course=course)
                
                # Handle answer options
                if 'answer_options' in q_data:
                    # Delete existing options and create new ones
                    AnswerOption.objects.filter(question=question).delete()
                    for option in q_data['answer_options']:
                        AnswerOption.objects.create(question=question, **option)
                
                # Handle matching options
                if 'matching_options' in q_data:
                    MatchingOption.objects.filter(question=question).delete()
                    for option in q_data['matching_options']:
                        MatchingOption.objects.create(question=question, **option)
    
    # Handle tests and test questions
    test_data = request.data.get('tests', [])
    for t_data in test_data:
        t_id = t_data.get('id')
        test_questions = t_data.pop('test_questions', []) if 'test_questions' in t_data else []
        
        if t_id:
            try:
                test = Test.objects.get(id=t_id)
                serializer = TestSerializer(test, data=t_data, partial=True)
            except Test.DoesNotExist:
                serializer = TestSerializer(data=t_data)
            
            if serializer.is_valid():
                test = serializer.save(course=course)
                
                # Handle test questions
                TestQuestion.objects.filter(test=test).delete()
                for i, tq in enumerate(test_questions):
                    question_id = tq.get('question_id')
                    try:
                        question = Question.objects.get(id=question_id)
                        TestQuestion.objects.create(
                            test=test,
                            question=question,
                            assigned_points=tq.get('assigned_points'),
                            order=i+1,
                            randomize=tq.get('randomize', False),
                            special_instructions=tq.get('special_instructions')
                        )
                    except Question.DoesNotExist:
                        pass
    
    # Handle templates
    template_data = request.data.get('templates', [])
    for t_data in template_data:
        t_id = t_data.get('id')
        if t_id:
            try:
                template = Template.objects.get(id=t_id)
                serializer = TemplateSerializer(template, data=t_data, partial=True)
            except Template.DoesNotExist:
                serializer = TemplateSerializer(data=t_data)
            
            if serializer.is_valid():
                serializer.save(course=course)
    
    # Handle cover pages
    cover_page_data = request.data.get('cover_pages', [])
    for cp_data in cover_page_data:
        cp_id = cp_data.get('id')
        if cp_id:
            try:
                cover_page = CoverPage.objects.get(id=cp_id)
                serializer = CoverPageSerializer(cover_page, data=cp_data, partial=True)
            except CoverPage.DoesNotExist:
                serializer = CoverPageSerializer(data=cp_data)
            
            if serializer.is_valid():
                serializer.save(course=course)
    
    # Handle attachments
    attachment_data = request.data.get('attachments', [])
    for a_data in attachment_data:
        a_id = a_data.get('id')
        if a_id:
            try:
                attachment = Attachment.objects.get(id=a_id)
                serializer = AttachmentSerializer(attachment, data=a_data, partial=True)
            except Attachment.DoesNotExist:
                serializer = AttachmentSerializer(data=a_data)
            
            if serializer.is_valid():
                serializer.save(course=course)
    
    return Response({'status': 'success'})