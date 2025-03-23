from rest_framework import serializers
from django.contrib.auth.models import User
from welcome.models import (
    Textbook, UserProfile, Course, Question, Options, Answers, 
    DynamicQuestionParameter, Template, CoverPage, Attachment, 
    Test, TestQuestion, Feedback
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class TextbookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Textbook
        fields = ['id', 'title', 'author', 'version', 'isbn', 'link', 'publisher', 'published']

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'role']

class CourseSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    teachers = UserSerializer(many=True, read_only=True)
    textbook = TextbookSerializer(read_only=True)
    
    class Meta:
        model = Course
        fields = ['id', 'name', 'crn', 'sem', 'user', 'textbook', 'teachers', 'published']

class OptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Options
        fields = ['id', 'question', 'text']

class AnswersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answers
        fields = ['id', 'question', 'text', 'answer_graphic', 'response_feedback_text', 'response_feedback_graphic']

class DynamicQuestionParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = DynamicQuestionParameter
        fields = ['id', 'question', 'formula', 'range_min', 'range_max', 'additional_params']

class QuestionSerializer(serializers.ModelSerializer):
    options = OptionsSerializer(many=True, read_only=True, source='options')
    answers = AnswersSerializer(many=True, read_only=True, source='options')
    dynamic_parameters = DynamicQuestionParameterSerializer(read_only=True)
    author = UserSerializer(read_only=True)
    
    class Meta:
        model = Question
        fields = [
            'id', 'qtype', 'text', 'course', 'textbook', 'img', 'ansimg',
            'score', 'eta', 'directions', 'reference', 'comments',
            'chapter', 'section', 'answer', 'author', 'created_at', 'updated_at',
            'options', 'answers', 'dynamic_parameters', 'publisher_average_rating'
        ]

class TemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        fields = [
            'id', 'course', 'textbook', 'name', 'titleFont', 'titleFontSize',
            'subtitleFont', 'subtitleFontSize', 'bodyFont', 'bodyFontSize',
            'pageNumbersInHeader', 'pageNumbersInFooter', 'headerText', 'footerText',
            'coverPage'
        ]

class CoverPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoverPage
        fields = [
            'id', 'course', 'textbook', 'name', 'testNum', 'date',
            'file', 'showFilename', 'blank', 'instructions', 'published'
        ]

class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ['id', 'course', 'textbook', 'name', 'file', 'published']

class TestQuestionSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(read_only=True)
    
    class Meta:
        model = TestQuestion
        fields = ['id', 'test', 'question', 'assigned_points', 'order', 'randomize', 'special_instructions']

class TestSerializer(serializers.ModelSerializer):
    test_questions = TestQuestionSerializer(many=True, read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    template = TemplateSerializer(read_only=True)
    
    class Meta:
        model = Test
        fields = [
            'id', 'course', 'textbook', 'name', 'date', 'filename',
            'is_final', 'template', 'attachments', 'created_at', 'updated_at',
            'test_questions'
        ]

class FeedbackSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Feedback
        fields = ['id', 'question', 'test', 'user', 'rating', 'comments', 'created_at']

# Serializers with write operations

class TextbookWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Textbook
        fields = ['id', 'title', 'author', 'version', 'isbn', 'link', 'publisher', 'published']

class CourseWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'name', 'crn', 'sem', 'user', 'textbook', 'teachers', 'published']

class QuestionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = [
            'id', 'qtype', 'text', 'course', 'textbook', 'img', 'ansimg',
            'score', 'eta', 'directions', 'reference', 'comments',
            'chapter', 'section', 'answer', 'author'
        ]

class OptionsWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Options
        fields = ['id', 'question', 'text']

class AnswersWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answers
        fields = ['id', 'question', 'text', 'answer_graphic', 'response_feedback_text', 'response_feedback_graphic']

class TestWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Test
        fields = [
            'id', 'course', 'textbook', 'name', 'date', 'filename',
            'is_final', 'template'
        ]

class TestQuestionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestQuestion
        fields = ['id', 'test', 'question', 'assigned_points', 'order', 'randomize', 'special_instructions']

class FeedbackWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ['id', 'question', 'test', 'user', 'rating', 'comments']