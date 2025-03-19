"""
This module houses business logic functions for data access and updates.
"""

from django.db.models import Q, Sum
from django.db import transaction
from django.shortcuts import render
from welcome.models import (
    Course,
    Question,
    Test,
    Feedback,
    FeedbackResponse,
    Book,
)


def update_test_final_status(test_id, final_status=True):
    """
    Update the 'is_final' status of a test.
    """
    test = Test.objects.filter(id=test_id).first()  # Retrieve test by ID.
    if test:
        test.is_final = final_status
        test.save()
        return test
    return None


def add_feedback_response(feedback_id, publisher, response_text):
    """
    Create or update a FeedbackResponse for a given feedback using an atomic transaction.
    """
    with transaction.atomic():
        feedback = Feedback.objects.get(id=feedback_id)
        response, created = FeedbackResponse.objects.update_or_create(
            feedback=feedback,
            defaults={"publisher": publisher, "response_text": response_text}
        )
        return response

def total_estimated_time_for_test(test_id):
    """
    Calculate the total estimated time to complete a test by summing the estimated_time of all its questions.
    """
    test = Test.objects.get(id=test_id)
    total_time = test.test_questions.aggregate(
        total_time=Sum('question__estimated_time')
    )['total_time']
    return total_time

def update_course_book(course_id, new_book):
    """
    Update the Book associated with a course.
    """
    course = Course.objects.filter(id=course_id).first()
    if course:
        course.book = new_book
        course.save()
    return course

def get_visible_questions_for_teacher(teacher_username):
    """
    Retrieve questions visible to a teacher. This includes:
      - Questions created by the teacher that are linked to a course.
      - Publisher-created questions for courses where the teacher is associated (via shared book).
    """
    teacher_book_ids = Course.objects.filter(
        teachers__username=teacher_username
    ).values_list('book_id', flat=True).distinct()

    questions = Question.objects.filter(
        Q(owner__username=teacher_username, course__isnull=False) |
        Q(owner__userprofile__role='publisher', book_id__in=teacher_book_ids)
    )
    return questions

def teacher_dashboard(request):
    """
    Render a teacher's dashboard showing visible questions.
    """
    teacher_username = request.user.username
    questions = get_visible_questions_for_teacher(teacher_username)
    return render(request, 'teacher_dashboard.html', {'questions': questions})
