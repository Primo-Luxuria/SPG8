import json
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile

from bs4 import BeautifulSoup
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.http import HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from welcome.models import (
    Book,
    UserProfile,
    Course,
    Question,
    AnswerOption,
    Test,  # If you renamed it in your script, adjust here.
)
from django.db.models import Q, Value, CharField
from itertools import chain


def home(request):
    return render(request, 'welcome/home.html')


def signup_handler(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        passwordconfirm = request.POST.get("passwordconfirm")
        role = request.POST.get("role")

        if password != passwordconfirm:
            messages.error(request, "Passwords do not match.")
            return redirect("signup")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect("signup")

        user = User.objects.create_user(username=username, password=password)
        UserProfile.objects.create(user=user, role=role)
        messages.success(request, "Account created successfully!")

        if role == "teacher":
            return redirect("teacher_dashboard")
        elif role == "publisher":
            return redirect("publisher_dashboard")
        else:
            return redirect("webmaster_dashboard")
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
            login(request, user)
            try:
                role = user.userprofile.role
            except Exception:
                role = "user"
            if role == "teacher":
                return redirect("teacher_dashboard")
            elif role == "publisher":
                return redirect("publisher_dashboard")
            else:
                return redirect("home")
        else:
            messages.error(request, "Invalid username or password")
            return redirect("login")
    return redirect("login")


def parse_qti_xml(request):
    """
    Parses a QTI XML file and saves extracted data to the database.
    """
    class ImageDataPair:
        def __init__(self, raw_image_data, actual_image_name):
            self.raw_image_data = raw_image_data
            self.actual_image_name = actual_image_name

    def remove_namespace(tree):
        for elem in tree.iter():
            if "}" in elem.tag:
                elem.tag = elem.tag.split("}")[-1]

    def create_question(course, q_type, q_text, points, g_feedback_text, feedback_graphic, feedback_type):
        return Question.objects.create(
            course=course,
            question_type=q_type,
            question_text=q_text,
            default_points=points,
            general_feedback_text=g_feedback_text,
            feedback_graphic=feedback_graphic,
            feedback_type=feedback_type
        )

    def check_embedded_graphic(text_q, filename_list, zip_ref):
        soup = BeautifulSoup(text_q, 'html.parser')
        img_element = soup.find('img')
        if img_element:
            src_value = img_element.get('src')
            url_encoded_path = src_value[18:]  # remove "$IMS-CC-FILEBASE$/"
            decoded_path = urllib.parse.unquote(url_encoded_path)
            for potential_image_name in filename_list:
                if potential_image_name.endswith(decoded_path):
                    image_name = img_element.get('alt')
                    with zip_ref.open(potential_image_name) as img_file:
                        img_data = img_file.read()
                    return ImageDataPair(img_data, image_name)
            print('Desired image not found')
        return None

    def parse_just_xml(meta_file, questions_file, course):
        print("Processing metadata and questions files")
        meta_tree = ET.parse(meta_file)
        meta_root = meta_tree.getroot()
        remove_namespace(meta_root)
        cover_instructions_text = meta_root.find('.//description').text

        questions_tree = ET.parse(questions_file)
        questions_root = questions_tree.getroot()
        remove_namespace(questions_root)
        assessment = questions_root.find("assessment")
        if assessment is None:
            return JsonResponse({"error": "Element 'assessment' not found in XML!"}, status=400)

        test_title = assessment.get("title")
        test_identifier = assessment.get("ident")
        test_instance = Test.objects.create(
            course=course,
            title=test_title,
            test_number=test_identifier,
            cover_instructions=cover_instructions_text
        )

        for section in questions_root.findall(".//section"):
            for item in section.findall(".//item"):
                item_metadata = item.find('itemmetadata')
                metadata_fields = item_metadata.findall(".//fieldentry")
                presentation = item.find('presentation')
                mattext = presentation.find('.//material/mattext')
                question_text_field = mattext.text
                q_type = metadata_fields[0].text
                max_points = float(metadata_fields[1].text)
                correct_answer_ident = None

                if q_type == 'multiple_choice_question':
                    response_lid = presentation.find('.//response_lid')
                    answer_choices = {}
                    for label in response_lid.findall('.//response_label'):
                        ident = label.get('ident')
                        text = label.find('.//mattext').text
                        answer_choices[ident] = text

                    resprocessing = item.find('resprocessing')
                    for condition in resprocessing.findall('.//respcondition'):
                        if condition.get('continue') == "No":
                            correct_answer_ident = condition.find('.//varequal').text

                    question_instance = create_question(course, q_type, question_text_field,
                                                        max_points, None, None, None)
                    image_pair = check_embedded_graphic(question_text_field, zip_ref.namelist(), zip_ref)
                    if image_pair:
                        question_instance.embedded_graphic.save(image_pair.actual_image_name,
                                                                ContentFile(image_pair.raw_image_data))
                        question_instance.save()
                    for key, value in answer_choices.items():
                        AnswerOption.objects.create(
                            question=question_instance,
                            text=value,
                            is_correct=(key == correct_answer_ident)
                        )
                # Add other question types as needed...

    uploaded_file = request.FILES.get("file")
    if request.method == "POST" and uploaded_file:
        print("File uploaded:", uploaded_file.name)
        file_info = {"filename": uploaded_file.name, "size": uploaded_file.size}
    else:
        print("No file uploaded.")
        file_info = None

    if not uploaded_file:
        return JsonResponse({"message": "No file uploaded or it doesn't exist.", "file_info": file_info})

    course_id = request.POST.get("courseID")
    course_name = request.POST.get("courseName")
    course_crn = request.POST.get("courseCRN")
    course_semester = request.POST.get("courseSemester")
    textbook_title = request.POST.get("courseTextbookTitle")
    textbook_author = request.POST.get("courseTextbookAuthor")
    textbook_isbn = request.POST.get("courseTextbookISBN")
    textbook_link = request.POST.get("courseTextbookLink")

    course_instance, created = Course.objects.get_or_create(
        course_code=course_id,
        defaults={
            "course_name": course_name,
            "textbook_title": textbook_title,
            "textbook_author": textbook_author,
            "textbook_isbn": textbook_isbn,
            "textbook_link": textbook_link,
        }
    )
    print(f"Course: {course_instance}")

    # Use uploaded file or fallback for testing
    path_to_zip_file = uploaded_file if uploaded_file else 'qti_sample.zip'
    with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
        filename_list = zip_ref.namelist()
        for file_name in filename_list:
            if file_name.endswith('/') and len([fn for fn in filename_list if fn.startswith(file_name) and fn != file_name]) >= 2:
                temp_files = sorted([fn for fn in filename_list if fn.startswith(file_name) and fn != file_name])
                if temp_files[0].endswith('.xml') and temp_files[1].endswith('.xml'):
                    with zip_ref.open(temp_files[0]) as meta_file, zip_ref.open(temp_files[1]) as questions_file:
                        parse_just_xml(meta_file, questions_file, course_instance)

    return JsonResponse({"message": "File processed successfully!", "file_info": file_info})


def login_view(request):
    return render(request, 'welcome/login.html')


def signup_view(request):
    return render(request, 'welcome/signup.html')


def teacher_dashboard(request):
    return render(request, 'welcome/SBteacher.html')


def publisher_dashboard(request):
    return render(request, 'welcome/SBpublisher.html')


@login_required
@csrf_exempt
def teacher_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=405)

    try:
        data = json.loads(request.body)
        print("Received data:", data)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)

    current_user = request.user
    courses = data.get("courses", {})
    for course_id, course_info in courses.items():
        print(f"Processing course {course_id}: {course_info}")
        textbook_data = course_info.get("textbook", {})
        course, created = Course.objects.get_or_create(
            course_code=course_id,
            user=current_user,
            defaults={
                "course_name": course_info.get("name", "Untitled Course"),
                "course_crn": course_info.get("crn", ""),
                "textbook_title": textbook_data.get("title", ""),
                "textbook_author": textbook_data.get("author", ""),
                "textbook_version": textbook_data.get("version", ""),
                "textbook_isbn": textbook_data.get("isbn", ""),
                "textbook_link": textbook_data.get("link", ""),
            }
        )
        if created:
            print(f"Created course: {course.course_code}")
        else:
            updated = False
            for field, incoming in [
                ("textbook_title", textbook_data.get("title", "")),
                ("textbook_author", textbook_data.get("author", "")),
                ("textbook_version", textbook_data.get("version", "")),
                ("textbook_isbn", textbook_data.get("isbn", "")),
                ("textbook_link", textbook_data.get("link", ""))
            ]:
                if incoming and getattr(course, field) != incoming:
                    print(f"Updating {field}: '{getattr(course, field)}' -> '{incoming}'")
                    setattr(course, field, incoming)
                    updated = True
            if updated:
                course.save()
                print(f"Updated course: {course.course_code}")
            else:
                print(f"No update needed for course: {course.course_code}")

    return JsonResponse({"status": "Data inserted successfully"})






from welcome.query import get_visible_questions_for_teacher

def teacher_dashboard(request):
    teacher_username = request.user.username
    questions = get_visible_questions_for_teacher(teacher_username)
    return render(request, 'teacher_dashboard.html', {'questions': questions})
