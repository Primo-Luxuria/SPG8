from rest_framework import serializers
from .models import (
    Course, Book, Question, Test, Template, CoverPage, 
    Attachment, TestQuestion, AnswerOption, MatchingOption
)

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'version', 'isbn', 'link']

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'course_code', 'course_name', 'course_crn', 
                  'course_semester', 'book']

class AnswerOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerOption
        fields = ['id', 'text', 'is_correct', 'response_feedback_text']

class MatchingOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchingOption
        fields = ['id', 'option_text', 'match_text']

class QuestionSerializer(serializers.ModelSerializer):
    answer_options = AnswerOptionSerializer(many=True, read_only=True)
    matching_options = MatchingOptionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Question
        fields = ['id', 'question_type', 'question_text', 'default_points', 
                  'estimated_time', 'correct_answer', 'chapter', 'section', 
                  'instructions_for_grading', 'include_formula', 'answer_options', 
                  'matching_options']

class TestQuestionSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(read_only=True)
    
    class Meta:
        model = TestQuestion
        fields = ['id', 'question', 'assigned_points', 'order', 'randomize', 
                  'special_instructions']

class TestSerializer(serializers.ModelSerializer):
    test_questions = TestQuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Test
        fields = ['id', 'title', 'date', 'is_final', 'template', 
                  'test_number', 'cover_instructions', 'test_questions']

class TemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        fields = ['id', 'name', 'font_name', 'font_size', 'header_text', 
                  'footer_text']

class CoverPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoverPage
        fields = ['id', 'cover_page_name', 'test_number', 'test_date', 
                  'test_filename', 'filename_present', 'student_name_location', 
                  'grading_instructions_for_key']

class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ['id', 'file']