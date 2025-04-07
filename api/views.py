from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import transaction
from django.contrib.auth.models import User
from django.db.models import Prefetch
import json, os
import traceback
from decimal import Decimal
from django.db.models.fields.files import FieldFile

from welcome.models import (
    Course, Textbook, Question, Test, Template, CoverPage, 
    Attachment, TestQuestion, Options, Answers, UserProfile, Feedback,
    TestPart, TestSection, FeedbackResponse
)

@api_view(['POST'])
@transaction.atomic
def delete_item(request):
    data = request.data
    type = data.get("type", "")
    if type == "":
        return Response({"status": "error", "message": "Invalid type"}, status=status.HTTP_400_BAD_REQUEST)
    
    item = data.get("item", "")
    if item == "":
        return Response({"status": "error", "message": "Invalid item"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(username=data.get("username", ""))
    except User.DoesNotExist:
        return Response({"status": "error", "message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # Check user permissions based on role
    try:
        user_profile = UserProfile.objects.get(user=user)
        role = user_profile.role
    except UserProfile.DoesNotExist:
        return Response({"status": "error", "message": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # Only webmaster can delete any item, teachers and publishers can only delete their own items
    if role not in ['webmaster', 'teacher', 'publisher']:
        return Response({"status": "error", "message": "Insufficient permissions"}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        # Handle different item types
        if type == "test":
            test_id = item.get('id') if isinstance(item, dict) else None
            if not test_id:
                # Try to find test by name and other attributes
                name = item.get('name')
                if name:
                    # For teacher
                    if role == 'teacher':
                        tests = Test.objects.filter(name=name, course__teachers=user)
                    # For publisher
                    elif role == 'publisher':
                        tests = Test.objects.filter(name=name, textbook__publisher=user)
                    # For webmaster
                    else:
                        tests = Test.objects.filter(name=name)
                    
                    if tests.exists():
                        tests.delete()
                        return Response({"status": "success", "message": "Test successfully deleted!"})
                    else:
                        return Response({"status": "error", "message": "Test not found"}, status=status.HTTP_404_NOT_FOUND)
            else:
                test = Test.objects.get(id=test_id)
                # Check permissions
                if role != 'webmaster':
                    if role == 'teacher' and test.course and test.course.teachers.filter(id=user.id).exists():
                        pass  # Teacher owns this test
                    elif role == 'publisher' and test.textbook and test.textbook.publisher == user:
                        pass  # Publisher owns this test
                    else:
                        return Response({"status": "error", "message": "You don't have permission to delete this test"}, 
                                       status=status.HTTP_403_FORBIDDEN)
                test.delete()
                return Response({"status": "success", "message": "Test successfully deleted!"})
        
        elif type == "attachment":
            attachment_id = item.get('id') if isinstance(item, dict) else None
            if not attachment_id:
                # Try to find attachment by name
                name = item.get('name')
                if name:
                    # For teacher
                    if role == 'teacher':
                        attachments = Attachment.objects.filter(name=name, course__teachers=user)
                    # For publisher
                    elif role == 'publisher':
                        attachments = Attachment.objects.filter(name=name, textbook__publisher=user)
                    # For webmaster
                    else:
                        attachments = Attachment.objects.filter(name=name)
                    
                    if attachments.exists():
                        for attachment in attachments:
                            # Delete the actual file too
                            if attachment.file:
                                if hasattr(attachment.file, 'path') and os.path.exists(attachment.file.path):
                                    os.remove(attachment.file.path)
                        attachments.delete()
                        return Response({"status": "success", "message": "Attachment successfully deleted!"})
                    else:
                        return Response({"status": "error", "message": "Attachment not found"}, status=status.HTTP_404_NOT_FOUND)
            else:
                attachment = Attachment.objects.get(id=attachment_id)
                # Check permissions
                if role != 'webmaster':
                    if role == 'teacher' and attachment.course and attachment.course.teachers.filter(id=user.id).exists():
                        pass  # Teacher owns this attachment
                    elif role == 'publisher' and attachment.textbook and attachment.textbook.publisher == user:
                        pass  # Publisher owns this attachment
                    else:
                        return Response({"status": "error", "message": "You don't have permission to delete this attachment"}, 
                                       status=status.HTTP_403_FORBIDDEN)
                # Delete the actual file too
                if attachment.file:
                    if hasattr(attachment.file, 'path') and os.path.exists(attachment.file.path):
                        os.remove(attachment.file.path)
                attachment.delete()
                return Response({"status": "success", "message": "Attachment successfully deleted!"})
        
        elif type == "question":
            question_id = item.get('id') if isinstance(item, dict) else None
            if not question_id:
                # Try to find question by text
                text = item.get('text')
                if text:
                    # For teacher/publisher, only delete their own questions
                    if role in ['teacher', 'publisher']:
                        questions = Question.objects.filter(text=text, author=user)
                    # For webmaster
                    else:
                        questions = Question.objects.filter(text=text)
                    
                    if questions.exists():
                        questions.delete()
                        return Response({"status": "success", "message": "Question successfully deleted!"})
                    else:
                        return Response({"status": "error", "message": "Question not found"}, status=status.HTTP_404_NOT_FOUND)
            else:
                question = Question.objects.get(id=question_id)
                # Check permissions
                if role != 'webmaster' and question.author != user:
                    return Response({"status": "error", "message": "You don't have permission to delete this question"}, 
                                   status=status.HTTP_403_FORBIDDEN)
                question.delete()
                return Response({"status": "success", "message": "Question successfully deleted!"})
        
        elif type == "coverpage":
            coverpage_id = item.get('id') if isinstance(item, dict) else None
            if not coverpage_id:
                # Try to find coverpage by name
                name = item.get('name')
                if name:
                    # For teacher
                    if role == 'teacher':
                        coverpages = CoverPage.objects.filter(name=name, course__teachers=user)
                    # For publisher
                    elif role == 'publisher':
                        coverpages = CoverPage.objects.filter(name=name, textbook__publisher=user)
                    # For webmaster
                    else:
                        coverpages = CoverPage.objects.filter(name=name)
                    
                    if coverpages.exists():
                        coverpages.delete()
                        return Response({"status": "success", "message": "Cover page successfully deleted!"})
                    else:
                        return Response({"status": "error", "message": "Cover page not found"}, status=status.HTTP_404_NOT_FOUND)
            else:
                coverpage = CoverPage.objects.get(id=coverpage_id)
                # Check permissions
                if role != 'webmaster':
                    if role == 'teacher' and coverpage.course and coverpage.course.teachers.filter(id=user.id).exists():
                        pass  # Teacher owns this coverpage
                    elif role == 'publisher' and coverpage.textbook and coverpage.textbook.publisher == user:
                        pass  # Publisher owns this coverpage
                    else:
                        return Response({"status": "error", "message": "You don't have permission to delete this cover page"}, 
                                       status=status.HTTP_403_FORBIDDEN)
                coverpage.delete()
                return Response({"status": "success", "message": "Cover page successfully deleted!"})
        
        elif type == "template":
            template_id = item.get('id') if isinstance(item, dict) else None
            if not template_id:
                # Try to find template by name
                name = item.get('name')
                if name:
                    # For teacher
                    if role == 'teacher':
                        templates = Template.objects.filter(name=name, course__teachers=user)
                    # For publisher
                    elif role == 'publisher':
                        templates = Template.objects.filter(name=name, textbook__publisher=user)
                    # For webmaster
                    else:
                        templates = Template.objects.filter(name=name)
                    
                    if templates.exists():
                        templates.delete()
                        return Response({"status": "success", "message": "Template successfully deleted!"})
                    else:
                        return Response({"status": "error", "message": "Template not found"}, status=status.HTTP_404_NOT_FOUND)
            else:
                template = Template.objects.get(id=template_id)
                # Check permissions
                if role != 'webmaster':
                    if role == 'teacher' and template.course and template.course.teachers.filter(id=user.id).exists():
                        pass  # Teacher owns this template
                    elif role == 'publisher' and template.textbook and template.textbook.publisher == user:
                        pass  # Publisher owns this template
                    else:
                        return Response({"status": "error", "message": "You don't have permission to delete this template"}, 
                                       status=status.HTTP_403_FORBIDDEN)
                template.delete()
                return Response({"status": "success", "message": "Template successfully deleted!"})
        
        else:
            return Response({"status": "error", "message": f"Unknown item type: {type}"}, 
                          status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        
        print(traceback.format_exc())
        return Response({"status": "error", "message": f"Error deleting item: {str(e)}"}, 
                      status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({"status": "error", "message": "Failed to delete item"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@transaction.atomic
def update_user(request):
    data = request.data
    currentUN = data.get('username')
    print("New UN: " + data.get('new_username'))
    print("New PW: " + data.get('new_password'))
    # Check if the new username already exists
    if data.get('update_username') & User.objects.filter(username=data.get('new_username')).exists():
        print("This username is taken!")
        return Response({"status": "This username is taken!"})

    try:
        # Try to find the current user
        user = User.objects.get(username=currentUN)
        print("OLD UN: " + user.username)
        print("OLD PW: " + user.password)
    except User.DoesNotExist:
        return Response({"status": "User not found"})

    # Update user details
    user.username = data.get('new_username')
    user.set_password(data.get('new_password'))
    user.save()
    print("FINAL UN: " + user.username)
    print("FINAL PW: " + user.password)
    return Response({"status": "success"})


@api_view(['POST'])
@transaction.atomic
def fetch_user_data(request):
    data = request.data
    request_type = data.get('type', '')  # Fixed typo
    value = data.get('value', '')  # Fixed typo

    if request_type == "UN":
        try:
            user = User.objects.get(username=value)
        except User.DoesNotExist:
            return Response({"status": "User not found"})

    elif request_type == "ID":
        try:
            user = User.objects.get(id=value)
        except User.DoesNotExist:
            return Response({"status": "User not found"})
    else:
        return Response({"status": "INVALID REQUEST TYPE"})
    
    try:
        userpf = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        return Response({"status": "UserProfile not found"})
    
    role = userpf.role
    master_question_list = []

    if role == "teacher":
        courses = Course.objects.filter(teachers=user)
        master_question_list = get_question_list('course', courses)
        master_test_list = get_test_list('course', courses)
        master_template_list = get_template_list('course', courses)
        master_cpage_list = get_cpage_list('course', courses)
        master_attachment_list = get_attachment_list('course', courses)
        container_list = {}
        for course in courses:
            container_list[course.course_id] = {
                "id": course.course_id,
                "crn": course.crn,
                "name": course.name,
                "sem": course.sem,
                "textbook": {
                    "title": course.textbook.title,
                    "author":course.textbook.author,
                    "version":course.textbook.version,
                    "isbn":course.textbook.isbn,
                    "link": course.textbook.link,
                    "questions": []
                }
            }
            textbook = []
            textbook.append(course.textbook)
            questions = get_question_list('textbook', textbook)
            container_list[course.course_id]['textbook']['questions'] = questions
    elif role == "publisher":
        textbooks = Textbook.objects.filter(publisher=user)
        master_question_list = get_question_list('textbook', textbooks)
        master_test_list = get_test_list('textbook', textbooks)
        master_template_list = get_template_list('textbook', textbooks)
        master_cpage_list = get_cpage_list('textbook', textbooks)
        master_attachment_list = get_attachment_list('textbook', textbooks)
        container_list = []
        for textbook in textbooks:
            container_list[textbook.isbn] = {
                'title': textbook.title,
                'author': textbook.author,
                'version': textbook.version,
                'isbn': textbook.isbn,
                'link': textbook.link
            }
    elif role == "webmaster":
        master_question_list = [] #Dummy values
        master_test_list = []
        master_template_list = []
        master_attachment_list = []
        master_cpage_list = []
    else:
        return Response({"status": "Failed due to invalid user role"}, status=400)
    
    return Response({
        "status": "success",
        "username": user.username,
        "password": user.password,
        "role": role,
        "question_list": json.dumps(master_question_list, cls=CustomJSONEncoder),
        "test_list": json.dumps(master_test_list, cls=CustomJSONEncoder),
        "template_list": json.dumps(master_template_list, cls=CustomJSONEncoder),
        "cpage_list": json.dumps(master_cpage_list, cls=CustomJSONEncoder),
        "attachment_list": json.dumps(master_attachment_list, cls=CustomJSONEncoder),
        "container_list": json.dumps(container_list, cls=CustomJSONEncoder)
    })

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if obj is None:
            return None
        
        # Handle Decimal to float conversion
        if isinstance(obj, Decimal):
            return float(obj)
        
        # Handle ImageField or FileField objects safely
        # Check if it's a FileField or ImageField without directly accessing .url
        if isinstance(obj, FieldFile):
            return obj.url if obj.name else None
        
        # Handle datetime and date objects
        elif hasattr(obj, 'isoformat'):
            return obj.isoformat()
        
        # For any other unhandled objects, call the default method of the superclass
        return super().default(obj)

@api_view(['POST'])
@transaction.atomic
def save_textbook(request):
    data = request.data
    datatext = data.get('textbook', {})
    newtextbook = Textbook.objects.update_or_create(
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


@api_view(['POST'])
@transaction.atomic
def save_course(request):
    data = request.data
    course = data.get('course', {})

    datatext= course.get('textbook')
    if Textbook.objects.filter(author=datatext.get('author'), title=datatext.get('title'), version=datatext.get('version'), isbn=datatext.get('isbn')):
        newtextbook = Textbook.objects.filter(author=datatext.get('author'), title=datatext.get('title'), version=datatext.get('version')).first()
    else:
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
        
    newCourse, created = Course.objects.update_or_create(
        course_id=course.get('course_id'),
        crn=course.get('crn'),
        sem=course.get('sem'),
        name=course.get('name'),
        defaults={
            'course_id': course.get('course_id'),
            'crn': course.get('crn'),
            'name': course.get('name'),
            'textbook': newtextbook,
            'sem': course.get('sem')
        }
    )

    if created:
        newCourse.user = request.user;

    teacher = request.user
    newCourse.teachers.add(teacher)
    newCourse.save()

    return Response({'status': 'success', 'created': created})

def get_cpage_list(field, suite):
    master_cpage_list = {}
    for instance in suite:
        if (field=="course"):
            identity = instance.course_id
        else:
            identity = instance.isbn
        master_cpage_list[identity] = []
        cpages = CoverPage.objects.filter(**{field: instance})
        for c in cpages:
            cpage_data = {
            "name": c.name,
            "testNum": c.testNum,
            "date": c.date,
            "file": c.file,
            "showFilename": c.showFilename,
            "blank": c.blank,
            "instructions": c.instructions,
            "published": c.published,
            "feedback": []
            }
            master_cpage_list[identity].append(cpage_data)
    return master_cpage_list

@api_view(['POST'])
@transaction.atomic
def save_cpage(request):
    data = request.data
    cpage = data.get('coverPage', {})
    owner_role = data.get('ownerRole')
    course = None
    textbook = None


    if(cpage.get('published')=="1"):
        return Response({'error': 'Already published!'}, status=400)

    if owner_role == 'teacher':
        try:
            owner_id = data.get('courseID')
            print("made it here")
            course = Course.objects.get(course_id=owner_id)
            print("made it here")
        except Course.DoesNotExist:
            return Response({'error': 'Course not found'}, status=400)
    elif owner_role == 'publisher':
        try:
            owner_id = data.get('isbn')
            textbook = Textbook.objects.get(isbn=owner_id)
        except Textbook.DoesNotExist:
            return Response({'error': 'Textbook not found'}, status=400)

    print("made it to here");
    newpage, created = CoverPage.objects.update_or_create(
        name=cpage.get('name'),
        testNum=cpage.get('testNum'),
        date=cpage.get('date'),
        file=cpage.get('file'),
        showFilename=cpage.get('showFilename'),
        blank=cpage.get('blank'),
        instructions=cpage.get('instructions'),
        published= cpage.get('published'),
        course=course,
        textbook= textbook,
        defaults={
            'date': cpage.get('date'),
            'file': cpage.get('file'),
            'showFilename': cpage.get('showFilename'),
            'blank': cpage.get('blank'),
            'instructions': cpage.get('instructions'),
            'published': cpage.get('published'),
            'course': course,
            'textbook': textbook
        }
    )
    newpage.save()

    return Response({'status': 'success', 'created': created})


def get_template_list(field, suite):
    master_template_list = {}
    for instance in suite:
        if (field=="course"):
            identity = instance.course_id
        else:
            identity = instance.isbn
        master_template_list[identity] = []

        templates = Template.objects.filter(**{field: instance})
        for t in templates:
            template_data = {
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
            "coverPage": t.coverPageData,
            "partStructure": t.partStructure,
            "bonusSection": t.bonusSection,
            "published": t.published,
            "feedback": []
            }
            master_template_list[identity].append(template_data)
    return master_template_list

@api_view(['POST'])
@transaction.atomic
def save_template(request):
    data = request.data
    template = data.get('template', {})
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


    print(template)
    newtemplate, created = Template.objects.update_or_create(
        name=template.get('name'),
        course=course,
        textbook= textbook,
        defaults= {
            'name': template.get('name'),
            'titleFont': template.get('titleFont'),
            'titleFontSize': template.get('titleFontSize'),
            'subtitleFont': template.get('subtitleFont'),
            'subtitleFontSize': template.get('subtitleFontSize'),
            'bodyFont': template.get('bodyFont'),
            'bodyFontSize': template.get('bodyFontSize'),
            'pageNumbersInHeader': template.get('pageNumbersInHeader'),
            'pageNumbersInFooter': template.get('pageNumbersInFooter'),
            'headerText': template.get('headerText'),
            'footerText': template.get('footerText'),
            'coverPageData': template.get('coverPage'),
            'partStructure': template.get('partStructure'),
            'bonusSection': template.get('bonusSection'),
            'published': template.get('published'),
            'course': course,
            'textbook': textbook
        }
    )
    newtemplate.save()
    return Response({'status': 'success', 'created': created})

@transaction.atomic
def get_question_list(field, suite): # needs to retrieve the questions from related publisher too
    master_question_list = {}
    for instance in suite:
        if (field=="course"):
            identity = instance.course_id
        else:
            identity = instance.isbn
        
        question_lists = {
            'tf': [],
            'mc': [],
            'sa': [],
            'es': [],
            'ma': [],
            'ms': [],
            'fb': []
        }

        master_question_list[identity] = question_lists
        questions = Question.objects.filter(**{field: instance}).prefetch_related(
                        Prefetch('question_answers',queryset=Answers.objects.all(),to_attr="answers"),
                        Prefetch('feedbacks', queryset=Feedback.objects.all(),to_attr="feedback"))
        for q in questions:
            
            question_data = {
            'text': q.text,
            'answer': q.answers,
            'qtype': q.qtype,
            'score': q.score,
            'directions': q.directions,
            'reference': q.reference,
            'eta': q.eta,
            'img': q.img,
            'ansimg': q.ansimg,
            'comments': q.comments,
            'prompts': [],
            'options': list(Options.objects.filter(question=q).values()),
            'tests': [],
            'chapter': q.chapter,
            'section': q.section,
            'published': q.published,
            } 
            question_data['feedback'] = []
            feedback = q.feedback
            for f in feedback:
                feedback_data = {
                    "username": f.user.username,
                    "rating": f.rating,
                    "averageScore": f.averageScore,
                    "comments": f.comments,
                    "date": f.created_at,
                    "responses": [{"username": r.user.username, "text":r.text,"date":r.date}for r in FeedbackResponse.objects.filter(feedback=f)]
                }
                question_data['feedback'].append(feedback_data)
            master_question_list[identity][q.qtype].append(question_data)
    return master_question_list

@api_view(['POST'])
@transaction.atomic
def save_question(request):
    data = request.data
    question = data.get('question', {})
    owner_role = data.get('ownerRole')

    course = None
    textbook = None
    
    if(question.get("published")=="1"):
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

    newQ, created = Question.objects.update_or_create(
        text=question.get('text'),
        qtype= question.get('qtype'),
        score= question.get('score'),
        directions= question.get('directions'),
        reference= question.get('reference'),
        eta= question.get('eta'),
        img= question.get('img'),
        ansimg= question.get('ansimg'),
        comments= question.get('comments'),
        chapter= question.get('chapter'),
        section= question.get('section'),
        published= question.get('published'),
        course=course,
        textbook=textbook,
        defaults= {
            'text': question.get('text'),
            'qtype': question.get('qtype'),
            'score': question.get('score'),
            'directions': question.get('directions'),
            'reference': question.get('reference'),
            'eta': question.get('eta'),
            'img': question.get('img'),
            'ansimg': question.get('ansimg'),
            'comments': question.get('comments'),
            'chapter': question.get('chapter'),
            'section': question.get('section'),
            'published': question.get('published'),
            'course': course,
            'textbook': textbook
        }
    )

    if created:
        newQ.author = request.user
    newQ.save()

    feedback = question.get('feedback', [])
    for f in feedback:
        user = User.objects.filter(username=f['username']) or "UNKNOWN USER"
        newF, created = Feedback.objects.update_or_create(
            user=user,
            comments= f['comments'],
            defaults={
                'user': user,
                'question': newQ,
                'rating': f.get('rating'),
                'averageScore': f.get('averageScore'),
                'comments': f.get('comments'),
            }
        )
        newF.save()
        responses = f['responses']
        for r in responses:
            user = User.objects.filter(username=r['username']) or "UNKNOWN USER"
            newR, created = Response.objects.update_or_create(
                user = user,
                text = r['text'],
                defaults={
                    'user': user,
                    'text': r.get('text'),
                    'date': r.get('date'),
                    'feedback': newF
                }
            )
            newR.save()

    options = question.get('options')
    for o in options:
        newOption, created = Options.objects.update_or_create(
            question=newQ,
            text=o,
            defaults={
                'question':newQ,
                'text':o
            }
        )
        newOption.save()

    return Response({'status': 'success', 'created': created})


def get_attachment_list(field, suite):
    master_attachment_list = {}
    for instance in suite:
        if (field=="course"):
            identity = instance.course_id
        else:
            identity = instance.isbn
        master_attachment_list[identity] = []
        attachments = Attachment.objects.filter(**{field: instance})
        for a in attachments:
            attachment_data = {
                "name": a.name,
                "file": a.file.url if a.file else None,
            }
            master_attachment_list[identity].append(attachment_data)
    return master_attachment_list

@api_view(['POST'])
@transaction.atomic
def save_attachment(request):
    attachment_name = request.POST.get('attachment_name')
    attachment_file = request.FILES.get('attachment_file')
    owner_role = request.POST.get('ownerRole')

    course = None
    textbook = None


    if owner_role == 'teacher':
        try:
            owner_id = request.POST.get('courseID')
            course = Course.objects.get(course_id=owner_id)
        except Course.DoesNotExist:
            return Response({'error': 'Course not found'}, status=400)
    elif owner_role == 'publisher':
        try:
            owner_id = request.POST.get('isbn')
            textbook = Textbook.objects.get(isbn=owner_id)
        except Textbook.DoesNotExist:
            return Response({'error': 'Textbook not found'}, status=400)

    newattachment, created = Attachment.objects.update_or_create(
        file=attachment_file,
        course=course,
        textbook=textbook,
        defaults={
            'name': attachment_name,
            'file': attachment_file,
            'course': course,
            'textbook': textbook
        }
    )
    newattachment.save()

    return Response({'status': 'success', 'created': created})
 


def get_test_list(field, suite):
    master_test_list = {}
    for instance in suite:
        if(field == 'textbook'):
            identity = instance.isbn
        else:
            identity = instance.course_id
        test_list = {
            'published': [],
            'drafts': []
        }
        master_test_list[identity] = test_list
        tests = Test.objects.filter(**{field: instance}).select_related('template').prefetch_related(
            'attachments',
            Prefetch('feedbacks', queryset=Feedback.objects.select_related('user'), to_attr="feedback_list"),
            Prefetch('parts', queryset=TestPart.objects.prefetch_related(
                Prefetch('sections', queryset=TestSection.objects.all(), to_attr='section_list')
            ), to_attr='part_list'),
            Prefetch('test_questions', queryset=TestQuestion.objects.select_related('question', 'section')
                .prefetch_related(
                    Prefetch('question__question_answers', queryset=Answers.objects.all(), to_attr='answer_list'),
                    Prefetch('question__question_options', queryset=Options.objects.all(), to_attr='option_list')
                ).order_by('order'), to_attr='test_question_list')
        )
        
        for t in tests:
            test_data = {
                'name': t.name,
                'template': t.template.id if t.template else None,
                'templateName': t.template.name if t.template else None,
                'templateIndex': t.templateIndex,
                'attachments': [{'name': a.name, 'file': str(a.file)} for a in t.attachments.all()],
                'parts': [],
                'published': t.is_final
            }

            # Create a map of test_questions by section for easy access
            section_question_map = {}
            for tq in getattr(t, 'test_question_list', []):
                if tq.section:
                    if tq.section.id not in section_question_map:
                        section_question_map[tq.section.id] = []
                    section_question_map[tq.section.id].append(tq)

            for p in getattr(t, 'part_list', []):
                part_data = {
                    'partNum': p.part_number,
                    'sections': []
                }

                for s in getattr(p, 'section_list', []):
                    section_data = {
                        'sectionNum': s.section_number,
                        'questionType': s.question_type,
                        'questions': []
                    }

                    # Get questions for this section from our map
                    for tq in section_question_map.get(s.id, []):
                        question = tq.question
                        section_data['questions'].append({
                            'text': question.text,
                            'answer': [ans.text for ans in getattr(question, 'answer_list', [])],
                            'qtype': question.qtype,
                            'score': tq.assigned_points,
                            'directions': question.directions,
                            'reference': question.reference,
                            'eta': question.eta,
                            'img': question.img.url if question.img else None,
                            'ansimg': question.ansimg.url if question.ansimg else None,
                            'comments': question.comments,
                            'prompts': [],
                            'options': [{'text': opt.text, 'image': opt.image.url if opt.image else None} 
                                      for opt in getattr(question, 'option_list', [])],
                            'chapter': question.chapter,
                            'section': question.section,
                            'published': question.published,
                        })

                    part_data['sections'].append(section_data)
                
                test_data['parts'].append(part_data)
            
            test_data['feedback'] = []
            for f in getattr(t, 'feedback_list', []):
                feedback_data = {
                    "username": f.user.username if f.user else "Anonymous",
                    "rating": f.rating,
                    "averageScore": f.averageScore,
                    "comments": f.comments,
                    "date": f.created_at,
                    "responses": [{"username": r.user.username if r.user else "Anonymous", 
                                 "text": r.text, 
                                 "date": r.date} 
                                 for r in FeedbackResponse.objects.filter(feedback=f).select_related('user')]
                }
                test_data['feedback'].append(feedback_data)
            if(t.is_final):
                test_list['published'].append(test_data)
            else:
                test_list['published'].append(test_data)
    
    return master_test_list

@api_view(['POST'])
@transaction.atomic
def save_test(request):
    data = request.data
    test = data.get('test', {})
    cpage = data.get('coverPage', {})

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

    print(test.get('template'))
    print(test.get('template').get('coverPage'))
    newtest, created = Test.objects.update_or_create(
        name=test.get('name'),
        course=course,
        textbook=textbook,
        date=test.get('date'),
        defaults={
            'name': test.get('name'),
            'date': test.get('date'),
            'filename': cpage.get('file'),
            'is_final': test.get('published'),
            'course': course,
            'textbook': textbook
        }
    )
    newtest.save()

    parts = test.get('parts', [])
    for p in parts:
        newpart,created = TestPart.objects.update_or_create(
            test=newtest,
            defaults={
                'test': newtest,
                'part_number': p['partNumber']
            }
        )
        newpart.save()
        sections = p.get('sections')
        for s in sections:
            newsection,created = TestSection.objects.update_or_create(
                part=newpart,
                section_number = s.get('sectionNumber'),
                question_type = s.get('questionType'),
                defaults={
                    'part': newpart,
                    'section_number': s.get('sectionNumber'),
                    'question_type': s.get('questionType')
                }
            )
            newsection.save()
            testquestions = s.get('questions')
            for tq in testquestions:
                newQ, created = Question.objects.update_or_create(
                    text=tq.get('text'),
                    qtype=tq.get('qtype'),
                    course=course,
                    textbook=textbook,
                    section=tq.get('section'),
                    eta=tq.get('eta'),
                    directions=tq.get('directions'),
                    reference=tq.get('reference'),
                    defaults= {
                        'text': tq.get('text'),
                        'qtype': tq.get('qtype'),
                        'directions': tq.get('directions'),
                        'reference': tq.get('reference'),
                        'eta': tq.get('eta'),
                        'img': tq.get('img'),
                        'ansimg': tq.get('ansimg'),
                        'comments': tq.get('comments'),
                        'chapter': tq.get('chapter'),
                        'section': tq.get('section'),
                        'published': tq.get('published'),
                        'course': course,
                        'textbook': textbook
                    }
                )
                newQ.save()

                options = tq.get('options')
                for o in options:
                    newOption, created = Options.objects.update_or_create(
                        question=newQ,
                        text=o,
                        defaults={
                            'question':newQ,
                            'text':o
                        }
                    )
                    newOption.save()
                
                newtq, created = TestQuestion.objects.update_or_create(
                    test=newtest,
                    section=newsection,
                    question=newQ,
                    defaults={
                        'test':newtest,
                        'section':newsection,
                        'question':newQ,
                        'assigned_points': newQ.score
                    }
                )
                newtq.save()


    return Response({'status': 'success', 'created': created})

