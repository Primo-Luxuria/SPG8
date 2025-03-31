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
from django.contrib.auth.decorators import login_required

from welcome.models import *

import json
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .models import Course#, AnswerOption  # Import additional models as needed


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
            elif role == "webmaster":
                return redirect("webmaster_dashboard")
            else:
                return redirect("home")  # Default fallback
        else:
            messages.error(request, "Invalid username or password")
            return redirect("login")
    
    return redirect("login")  # Redirect if not POST


import time
def parse_qti_xml(request):
    """
    Parses a QTI XML file and saves extracted data to the database.
    This supports QTI version 1.2 only.
    """
    start_time = time.perf_counter()
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
    def create_question(g_course, g_q_type, g_q_text, g_points):
        temp_question_instance = Question.objects.create(
            course=g_course, # this is because, logically, when questions/tests are uploaded to a course, are they not part of it?
            qtype=g_q_type,
            text=g_q_text,
            score=g_points,
            #general_feedback_text=g_g_f_t,
            #feedback_graphic=g_f_g,
            #feedback_type=g_f_t,
            # z
        )

        return temp_question_instance

    def check_embedded_graphic(text_q):
        if text_q is None:
            return None
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
        the_test_title = node.get("title") # test name
        test_identifier = node.get("ident")

        # Create a new Test record
        test_instance = Test.objects.create(
            course=the_course,
            textbook=the_course.textbook,
            name=the_test_title
        )
        test_part_instance = TestPart.objects.create(
            test=test_instance
        )
        number_of_sections = 0

        for section in root.findall(".//section"):
            number_of_sections = number_of_sections + 1
            test_section_instance = TestSection.objects.create(
                part=test_part_instance,
                section_number=number_of_sections
            )

            for item in section.findall(".//item"):

                # all useful metadata fields are found in the fieldentry elements under itemmetadata
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
                                                        max_points_for_question)
                    # this block of code checks for an embedded graphic in text, then saves it to field
                    # is there is a graphic. otherwise it does nothing.
                    image_data_pair = check_embedded_graphic(question_text_field)
                    if image_data_pair is not None:
                        # Save the image to the img field, then update the record/entry
                        question_instance.img.save(image_data_pair.actual_image_name,
                                                                ContentFile(image_data_pair.raw_image_data))
                        question_instance.save()
                        print(f"{question_instance.img.url}")
                    testquestion_instance = TestQuestion.objects.create(
                        test=test_instance,
                        question=question_instance,
                        assigned_points=max_points_for_question,
                        section=test_section_instance
                    )

                    for key, value in answer_choices_dict.items():
                        if key == correct_answer_ident:
                            question_instance.answer = value
                            temp_img_data_pair = check_embedded_graphic(value)
                            if temp_img_data_pair is not None:
                                question_instance.ansimg.save(temp_img_data_pair.actual_image_name, ContentFile(temp_img_data_pair.raw_image_data))

                            question_instance.save()
                        else:
                            options_instance = Options.objects.create(
                                question=question_instance,
                                text=value
                            )
                            temp_img_data_pair = check_embedded_graphic(value)
                            if temp_img_data_pair is not None:
                                options_instance.image.save(temp_img_data_pair.actual_image_name, ContentFile(temp_img_data_pair.raw_image_data))
                                options_instance.save()

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
                                                        max_points_for_question)
                    # this block of code checks for an embedded graphic in text, then saves it to field
                    # is there is a graphic. otherwise it does nothing.
                    image_data_pair = check_embedded_graphic(question_text_field)
                    if image_data_pair is not None:
                        # Save the image to the img field, then update the record/entry
                        question_instance.img.save(image_data_pair.actual_image_name,
                                                   ContentFile(image_data_pair.raw_image_data))
                        question_instance.save()
                        print(f"{question_instance.img.url}")
                    testquestion_instance = TestQuestion.objects.create(
                        test=test_instance,
                        question=question_instance,
                        assigned_points=max_points_for_question,
                        section=test_section_instance
                    )

                    for key, value in answer_choices_dict.items():
                        if key == correct_answer_ident:
                            question_instance.answer = value
                            temp_img_data_pair = check_embedded_graphic(value)
                            if temp_img_data_pair is not None:
                                question_instance.ansimg.save(temp_img_data_pair.actual_image_name,
                                                              ContentFile(temp_img_data_pair.raw_image_data))

                            question_instance.save()

                elif the_question_type == 'short_answer_question':  # fill-in-the-blank question (single)

                    the_question_type = "fill_in_the_blank"

                    question_instance = create_question(
                        the_course, the_question_type, question_text_field,
                        max_points_for_question
                    )
                    # this block of code checks for an embedded graphic in text, then saves it to field
                    # is there is a graphic. otherwise it does nothing.
                    image_data_pair = check_embedded_graphic(question_text_field)
                    if image_data_pair is not None:
                        # Save the image to the img field, then update the record/entry
                        question_instance.img.save(image_data_pair.actual_image_name,
                                                   ContentFile(image_data_pair.raw_image_data))
                        question_instance.save()
                        print(f"{question_instance.img.url}")
                    testquestion_instance = TestQuestion.objects.create(
                        test=test_instance,
                        question=question_instance,
                        assigned_points=max_points_for_question,
                        section=test_section_instance
                    )

                    node = item.find('resprocessing')
                    for respcondition_elem in node.findall('.//respcondition'):
                        if respcondition_elem.get('continue') == "No":
                            for varequal_elem in respcondition_elem.findall('.//varequal'):
                                answer_instance = Answers.objects.create(
                                    question=question_instance,
                                    text=varequal_elem.text
                                )
                                temp_img_data_pair = check_embedded_graphic(varequal_elem.text)
                                if temp_img_data_pair is not None:
                                    answer_instance.answer_graphic.save(temp_img_data_pair.actual_image_name, ContentFile(temp_img_data_pair.raw_image_data))
                                    answer_instance.save()

                elif the_question_type == 'multiple_answers_question':

                    the_question_type = "multiple_selection"

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
                                                        max_points_for_question)
                    # this block of code checks for an embedded graphic in text, then saves it to field
                    # is there is a graphic. otherwise it does nothing.
                    image_data_pair = check_embedded_graphic(question_text_field)
                    if image_data_pair is not None:
                        # Save the image to the img field, then update the record/entry
                        question_instance.img.save(image_data_pair.actual_image_name,
                                                   ContentFile(image_data_pair.raw_image_data))
                        question_instance.save()
                        print(f"{question_instance.img.url}")
                    testquestion_instance = TestQuestion.objects.create(
                        test=test_instance,
                        question=question_instance,
                        assigned_points=max_points_for_question,
                        section=test_section_instance
                    )

                    for key, value in answer_choices_dict.items():
                        if key in correct_answer_ident_list:
                            answer_instance = Answers.objects.create(
                                question=question_instance,
                                text=value
                            )
                            temp_img_data_pair = check_embedded_graphic(value)
                            if temp_img_data_pair is not None:
                                answer_instance.answer_graphic.save(temp_img_data_pair.actual_image_name,
                                                                    ContentFile(temp_img_data_pair.raw_image_data))
                                answer_instance.save()
                        else:
                            options_instance = Options.objects.create(
                                question=question_instance,
                                text=value
                            )
                            temp_img_data_pair = check_embedded_graphic(value)
                            if temp_img_data_pair is not None:
                                options_instance.image.save(temp_img_data_pair.actual_image_name, ContentFile(temp_img_data_pair.raw_image_data))
                                options_instance.save()

                elif the_question_type == 'matching_question': # this is explicitly stated in rubric to support
                    # Canvas requires you to add at least one answer
                    answer_choices_dict = {} # right side options and their ID's
                    left_side_dict = {}

                    question_instance = create_question(the_course, the_question_type, question_text_field,
                                                        max_points_for_question)
                    # this block of code checks for an embedded graphic in text, then saves it to field
                    # is there is a graphic. otherwise it does nothing.
                    image_data_pair = check_embedded_graphic(question_text_field)
                    if image_data_pair is not None:
                        # Save the image to the img field, then update the record/entry
                        question_instance.img.save(image_data_pair.actual_image_name,
                                                   ContentFile(image_data_pair.raw_image_data))
                        question_instance.save()
                        print(f"{question_instance.img.url}")
                    testquestion_instance = TestQuestion.objects.create(
                        test=test_instance,
                        question=question_instance,
                        assigned_points=max_points_for_question,
                        section=test_section_instance
                    )

                    # find left sides
                    for response_lid_elem in node.findall('response_lid'): # for all response_lid elements in list
                        side_key = response_lid_elem.get('ident')
                        side_text = response_lid_elem.find('material').find('mattext').text
                        left_side_dict[side_key] = side_text
                    # find right sides
                    for response_label_elem in node.find('response_lid').find('render_choice').findall('response_label'):
                        side_key = response_label_elem.get('ident')
                        side_text = response_label_elem.find('.//mattext').text
                        answer_choices_dict[side_key] = side_text
                    # now find out which ones are matching pairs
                    matching_pairs_dict = {}
                    node = item.find('resprocessing')
                    right_side_key_to_delete_list = []
                    for respcondition_elem in node.findall('respcondition'):
                        varequal_elem = respcondition_elem.find('conditionvar').find('varequal')
                        if varequal_elem is not None:
                            left_key = varequal_elem.get('respident')
                            right_key = varequal_elem.text
                            right_side_key_to_delete_list.append(right_key)
                            # this makes a dictionary of matching pairs
                            matching_pairs_dict[left_side_dict.get(left_key)] = answer_choices_dict.get(right_key)
                    unique_key_list_to_del = list(set(right_side_key_to_delete_list)) # this removes duplicate keys from list
                    for key_string in unique_key_list_to_del:
                        del answer_choices_dict[key_string]  # deletes a response option that was a correct right side
                    # now save matching pairs to database
                    for key, value in matching_pairs_dict.items():
                        matching_pair_string = ""
                        if key is not None:
                            matching_pair_string += key
                        matching_pair_string += "; "
                        if value is None:
                            matching_pair_string += ";"
                        else:
                            matching_pair_string += value

                        # multiple_answers questions CANNOT have embedded graphics in responses
                        answer_instance = Answers.objects.create(
                            question=question_instance,
                            text=matching_pair_string
                        )
                    # save distractors to database
                    for value in answer_choices_dict.values():
                        option_instance = Options.objects.create(
                            question=question_instance,
                            text=value
                        )

                elif the_question_type == 'essay_question':
                    # mostly done but may need to process feedbacks or comments

                    # this creates a question record in database
                    question_instance = create_question(the_course, the_question_type, question_text_field,
                                                        max_points_for_question)
                    # this block of code checks for an embedded graphic in text, then saves it to field
                    # is there is a graphic. otherwise it does nothing.
                    image_data_pair = check_embedded_graphic(question_text_field)
                    if image_data_pair is not None:
                        # Save the image to the img field, then update the record/entry
                        question_instance.img.save(image_data_pair.actual_image_name,
                                                   ContentFile(image_data_pair.raw_image_data))
                        question_instance.save()
                        print(f"{question_instance.img.url}")
                    testquestion_instance = TestQuestion.objects.create(
                        test=test_instance,
                        question=question_instance,
                        assigned_points=max_points_for_question,
                        section=test_section_instance
                    )

                # commented out because currently not supported
                """
                elif the_question_type == 'fill_in_multiple_blanks_question':
                    print('')  # this is placeholder for code to extract info from question for table
                elif the_question_type == 'multiple_dropdowns_question':
                    print('')  # this is placeholder for code to extract info from question for table
                elif the_question_type == 'numerical_question':
                    print('')  # this is placeholder for code to extract info from question for table
                elif the_question_type == 'calculated_question':
                    print('')  # this is placeholder for code to extract info from question for table

                elif the_question_type == 'file_upload_question':
                    # should be done but may need to process feedbacks or comments
                    print('')
                elif the_question_type == 'text_only_question':
                    # placeholder for any future changes, but 99.9% sure this is done
                    print('')
                """

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
    course_crn = request.POST.get("courseCRN")
    course_semester = request.POST.get("courseSemester")
    course_textbook_title = request.POST.get("courseTextbookTitle")
    course_textbook_author = request.POST.get("courseTextbookAuthor")
    course_textbook_version = request.POST.get("courseTextbookVersion")
    course_textbook_isbn = request.POST.get("courseTextbookISBN")
    course_textbook_link = request.POST.get("courseTextbookLink")

    textbook_instance, created = Textbook.objects.get_or_create(
        title=course_textbook_title,
        author=course_textbook_author,
        version=course_textbook_version,
        isbn=course_textbook_isbn,
        defaults={
            "link": course_textbook_link,
        }
    )

    course_instance, created = Course.objects.get_or_create(
        course_id=course_id,
        defaults={
            "name": course_name,
            "crn": course_crn,
            "sem": course_semester,
            "textbook": textbook_instance,
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
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    print(execution_time)
    # this is here because the javascript that calls the Parser depends on what it returns
    if file_info is None:
        print("Success! Created test record")
        return JsonResponse({"Success": "created Test record."}, status=555)
        
    else:
        print("File processed successfully!")
        return JsonResponse({"message": "File processed successfully!", "file_info": file_info})
        
#


# testing connecting the html files


#each of these functions renders a different html file

def login_view(request):
    return render(request, 'welcome/login.html')

def signup_view(request):
    return render(request, 'welcome/signup.html')

@login_required
def teacher_dashboard(request):
    context = {'username': request.user.username}
    return render(request, 'welcome/SBteacher.html', context)

@login_required
def publisher_dashboard(request):
    context = {'username': request.user.username}
    return render(request, 'welcome/SBpublisher.html', context)

@login_required
def webmaster_dashboard(request):
    context = {'username': request.user.username}
    return render(request, 'welcome/webmaster.html', context)


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
