from django.test import TestCase
from django.contrib.auth.models import User
from .models import UserProfile, Course, Question, Test, Feedback, Template

class ModelTests(TestCase):
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create(username="testuser", email="test@example.com")
        self.course = Course.objects.create(course_code="CS101", course_name="Intro to CS")
        self.template = Template.objects.create(name="Default Template")
        self.test = Test.objects.create(course=self.course, title="Midterm Exam", template=self.template)
        self.question = Question.objects.create(
            course=self.course, 
            question_type="MC", 
            question_text="What is Python?"
        )
    
    def test_user_profile_creation(self):
        """Test user profile creation with valid roles"""
        profile = UserProfile.objects.create(user=self.user, role="teacher")
        self.assertEqual(profile.user.username, "testuser")
        self.assertEqual(profile.role, "teacher")
    
    def test_course_creation(self):
        """Test course creation"""
        self.assertEqual(self.course.course_code, "CS101")
        self.assertEqual(self.course.course_name, "Intro to CS")

    def test_unique_course_code(self):
        """Test that course code is unique"""
        with self.assertRaises(Exception):
            Course.objects.create(course_code="CS101", course_name="Duplicate Course")
    
    def test_question_creation(self):
        """Test question creation and association with a course"""
        self.assertEqual(self.question.course, self.course)
        self.assertEqual(self.question.question_type, "MC")
        self.assertEqual(self.question.question_text, "What is Python?")
    
    def test_test_creation(self):
        """Test test creation"""
        self.assertEqual(self.test.course, self.course)
        self.assertEqual(self.test.title, "Midterm Exam")
        self.assertEqual(self.test.template, self.template)
    
    def test_feedback_creation_for_question(self):
        """Test feedback creation for a question"""
        feedback = Feedback.objects.create(question=self.question, user=self.user, rating=5, comments="Great question!")
        self.assertEqual(feedback.question, self.question)
        self.assertEqual(feedback.rating, 5)
        self.assertEqual(feedback.comments, "Great question!")

    def test_feedback_rating_within_range(self):
        """Test feedback rating within valid range (1-5)"""
        feedback = Feedback.objects.create(question=self.question, user=self.user, rating=3)
        self.assertTrue(1 <= feedback.rating <= 5)

    def test_feedback_creation_for_test(self):
        """Test feedback creation for a test"""
        feedback = Feedback.objects.create(test=self.test, user=self.user, rating=4, comments="Good test structure!")
        self.assertEqual(feedback.test, self.test)
        self.assertEqual(feedback.rating, 4)
        self.assertEqual(feedback.comments, "Good test structure!")

