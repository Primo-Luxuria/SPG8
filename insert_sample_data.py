# #!/usr/bin/env python
# import os
# import django

# # Set the Django settings module (replace with your actual settings module if different)
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "quizpress.settings")
# django.setup()

# from django.contrib.auth import get_user_model
# User = get_user_model()

# from welcome.models import (
#     Book,
#     UserProfile,
#     Course,
#     Question,
#     Test as QuizTest,  # Test model renamed to QuizTest in this script
# )

# def create_publisher_and_teachers():
#     # ----------------------
#     # Create a publisher and a book.
#     # ----------------------
#     publisher = User.objects.create_user(username="publisher1", password="password")
#     # Create a Book
#     shared_book = Book.objects.create(
#         title="Shared Book",
#         author="Publisher Author",
#         isbn="1234567890123"
#     )
#     # Create the publisher profile. Note: For publishers, a book is required.
#     publisher_profile = UserProfile.objects.create(
#         user=publisher,
#         role="publisher",
#         book=shared_book
#     )
#     print(f"Publisher created: {publisher.username} with book '{shared_book.title}'")
    
#     # ----------------------
#     # Create Publisher-created questions and test.
#     # These questions and test are linked directly to the Book.
#     # ----------------------
#     pub_question1 = Question.objects.create(
#         book=shared_book,
#         question_type="MC",
#         question_text="Publisher Q1: What is the capital of France?",
#         chapter=1,
#         owner=publisher
#     )
#     pub_question2 = Question.objects.create(
#         book=shared_book,
#         question_type="MC",
#         question_text="Publisher Q2: What is 5 x 7?",
#         chapter=2,
#         owner=publisher
#     )
#     pub_test = QuizTest.objects.create(
#         book=shared_book,
#         title="Publisher Test 1"
#     )
#     print("Publisher questions and test created.")

#     # ----------------------
#     # Create two teachers.
#     # ----------------------
#     teacher1 = User.objects.create_user(username="teacher1", password="password")
#     teacher2 = User.objects.create_user(username="teacher2", password="password")
#     # Create teacher profiles
#     teacher1_profile = UserProfile.objects.create(user=teacher1, role="teacher")
#     teacher2_profile = UserProfile.objects.create(user=teacher2, role="teacher")
#     print("Two teacher users created.")

#     # ----------------------
#     # For each teacher, create a Course that uses the same shared_book.
#     # ----------------------
#     course1 = Course.objects.create(
#         user=teacher1,
#         course_code="CS101",
#         course_name="Teacher1 Course",
#         course_crn="T1CRN",
#         course_semester="Fall 2022",
#         book=shared_book
#     )
#     course1.teachers.add(teacher1)
    
#     course2 = Course.objects.create(
#         user=teacher2,
#         course_code="CS102",
#         course_name="Teacher2 Course",
#         course_crn="T2CRN",
#         course_semester="Fall 2022",
#         book=shared_book
#     )
#     course2.teachers.add(teacher2)
#     print("Courses created for both teachers using the shared book.")

#     # ----------------------
#     # Create teacher-created questions (linked to their courses) and tests.
#     # ----------------------
#     # For teacher1
#     teacher1_question = Question.objects.create(
#         course=course1,
#         question_type="MC",
#         question_text="Teacher1 Q: What is 10 + 5?",
#         chapter=1,
#         owner=teacher1
#     )
#     teacher1_test = QuizTest.objects.create(
#         course=course1,
#         title="Teacher1 Test 1"
#     )
    
#     # For teacher2
#     teacher2_question = Question.objects.create(
#         course=course2,
#         question_type="MC",
#         question_text="Teacher2 Q: Who wrote 'Hamlet'?",
#         chapter=2,
#         owner=teacher2
#     )
#     teacher2_test = QuizTest.objects.create(
#         course=course2,
#         title="Teacher2 Test 1"
#     )
#     print("Teacher-created questions and tests created for both teachers.")

#     print("\nInsertion complete:")
#     print(f"- Publisher: {publisher.username}")
#     print(f"- Shared Book: {shared_book.title}")
#     print(f"- Publisher Questions: {pub_question1.id}, {pub_question2.id}")
#     print(f"- Publisher Test: {pub_test.id}")
#     print(f"- Teacher1: {teacher1.username} | Course: {course1.course_code} - {course1.course_name}")
#     print(f"  Teacher1 Question: {teacher1_question.id} | Test: {teacher1_test.id}")
#     print(f"- Teacher2: {teacher2.username} | Course: {course2.course_code} - {course2.course_name}")
#     print(f"  Teacher2 Question: {teacher2_question.id} | Test: {teacher2_test.id}")

# if __name__ == "__main__":
#     create_publisher_and_teachers()


#!/usr/bin/env python
import os
import django

# Set the Django settings module (replace with your actual settings module if different)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "quizpress.settings")
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

from welcome.models import (
    Book,
    UserProfile,
    Course,
    Question,
    Test as QuizTest,  # Test model renamed to QuizTest in this script
    Feedback,
    FeedbackResponse,
)

def create_publisher_and_teachers():
    # ----------------------
    # Create a publisher and a book.
    # ----------------------
    publisher = User.objects.create_user(username="publisher1", password="password")
    # Create a Book
    shared_book = Book.objects.create(
        title="Shared Book",
        author="Publisher Author",
        isbn="1234567890123"
    )
    # Create the publisher profile. Note: For publishers, a book is required.
    publisher_profile = UserProfile.objects.create(
        user=publisher,
        role="publisher",
        book=shared_book
    )
    print(f"Publisher created: {publisher.username} with book '{shared_book.title}'")
    
    # ----------------------
    # Create Publisher-created questions and test.
    # These questions and test are linked directly to the Book.
    # ----------------------
    pub_question1 = Question.objects.create(
        book=shared_book,
        question_type="MC",
        question_text="Publisher Q1: What is the capital of France?",
        chapter=1,
        owner=publisher
    )
    pub_question2 = Question.objects.create(
        book=shared_book,
        question_type="MC",
        question_text="Publisher Q2: What is 5 x 7?",
        chapter=2,
        owner=publisher
    )
    pub_test = QuizTest.objects.create(
        book=shared_book,
        title="Publisher Test 1"
    )
    print("Publisher questions and test created.")

    # ----------------------
    # Create two teachers.
    # ----------------------
    teacher1 = User.objects.create_user(username="teacher1", password="password")
    teacher2 = User.objects.create_user(username="teacher2", password="password")
    # Create teacher profiles
    teacher1_profile = UserProfile.objects.create(user=teacher1, role="teacher")
    teacher2_profile = UserProfile.objects.create(user=teacher2, role="teacher")
    print("Two teacher users created.")

    # ----------------------
    # For each teacher, create a Course that uses the same shared_book.
    # ----------------------
    course1 = Course.objects.create(
        user=teacher1,
        course_code="CS101",
        course_name="Teacher1 Course",
        course_crn="T1CRN",
        course_semester="Fall 2022",
        book=shared_book
    )
    course1.teachers.add(teacher1)
    
    course2 = Course.objects.create(
        user=teacher2,
        course_code="CS102",
        course_name="Teacher2 Course",
        course_crn="T2CRN",
        course_semester="Fall 2022",
        book=shared_book
    )
    course2.teachers.add(teacher2)
    print("Courses created for both teachers using the shared book.")

    # ----------------------
    # Create teacher-created questions (linked to their courses) and tests.
    # ----------------------
    # For teacher1
    teacher1_question = Question.objects.create(
        course=course1,
        question_type="MC",
        question_text="Teacher1 Q: What is 10 + 5?",
        chapter=1,
        owner=teacher1
    )
    teacher1_test = QuizTest.objects.create(
        course=course1,
        title="Teacher1 Test 1"
    )
    
    # For teacher2
    teacher2_question = Question.objects.create(
        course=course2,
        question_type="MC",
        question_text="Teacher2 Q: Who wrote 'Hamlet'?",
        chapter=2,
        owner=teacher2
    )
    teacher2_test = QuizTest.objects.create(
        course=course2,
        title="Teacher2 Test 1"
    )
    print("Teacher-created questions and tests created for both teachers.")

    # ----------------------
    # Demonstrate review and response:
    # A teacher provides feedback on a publisher-created question,
    # and then the publisher responds to that feedback.
    # ----------------------
    teacher_feedback = Feedback.objects.create(
        question=pub_question1,
        user=teacher1,
        rating=8,
        comments="The question is good but could use more context."
    )
    print(f"Teacher feedback created on Publisher Question {pub_question1.id}.")

    # Publisher responds to the teacher feedback.
    publisher_response = FeedbackResponse.objects.create(
        feedback=teacher_feedback,
        publisher=publisher,
        response_text="Thanks for the feedback! We'll add more context."
    )
    print(f"Publisher response created for Feedback {teacher_feedback.id}.")

    # ----------------------
    # Summary of inserted records.
    # ----------------------
    print("\nInsertion complete:")
    print(f"- Publisher: {publisher.username}")
    print(f"- Shared Book: {shared_book.title}")
    print(f"- Publisher Questions: {pub_question1.id}, {pub_question2.id}")
    print(f"- Publisher Test: {pub_test.id}")
    print(f"- Teacher1: {teacher1.username} | Course: {course1.course_code} - {course1.course_name}")
    print(f"  Teacher1 Question: {teacher1_question.id} | Test: {teacher1_test.id}")
    print(f"- Teacher2: {teacher2.username} | Course: {course2.course_code} - {course2.course_name}")
    print(f"  Teacher2 Question: {teacher2_question.id} | Test: {teacher2_test.id}")
    print(f"- Feedback on Publisher Q1: {teacher_feedback.id}")
    print(f"- Publisher Response: {publisher_response.id}")

if __name__ == "__main__":
    create_publisher_and_teachers()
