# from django.db import models
# from django.contrib.auth.models import User  # Standard Django user model.
# from django.core.exceptions import ValidationError
# from django.conf import settings
# from django.db.models import Q, Avg

# """
# BOOK MODEL
# This model holds textbook/book details.
# It is used as a key connection point for publisher content,
# and for teacher courses (each course references a Book).
# """
# class Book(models.Model):
#     title = models.CharField(max_length=300)
#     author = models.CharField(max_length=300, blank=True, null=True)
#     version = models.CharField(max_length=300, blank=True, null=True)
#     isbn = models.CharField(max_length=300, blank=True, null=True)
#     link = models.URLField(blank=True, null=True)

#     def __str__(self):
#         return self.title

#     def get_feedback(self):
#         """
#         Retrieve all feedback related to this book. Feedback can come from:
#           - Questions directly linked to this book.
#           - Tests that belong to courses using this book.
#           - Tests directly created for a book (publisher tests).
#         The use of Q objects allows for combining these query conditions.
#         """
#         from .models import Feedback  # Local import to avoid circular dependency.
#         return Feedback.objects.filter(
#             Q(question__book=self) | Q(test__course__book=self) | Q(test__book=self)
#         ).distinct()


# """
# USER PROFILE MODEL
# Extends the built-in User with a role and an optional book association.
# For publishers, the clean() method enforces that a Book is set.
# """
# class UserProfile(models.Model):
#     role_choices = [
#         ('webmaster', 'Webmaster'),
#         ('publisher', 'Publisher'),
#         ('teacher', 'Teacher'),
#     ]
#     user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
#     role = models.CharField(max_length=20, choices=role_choices)
#     # For publishers, their content (questions, tests, etc.) is linked directly to this book.
#     book = models.ForeignKey(
#         Book,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         help_text="Book associated with the publisher (required for publishers)."
#     )

#     def clean(self):
#         # Enforce that publishers have an associated book.
#         if self.role == 'publisher' and not self.book:
#             raise ValidationError("Publishers must have an associated book.")

#     def __str__(self):
#         return f"{self.user.username} ({self.role})"


# """
# COURSE MODEL
# Represents a teacher-created course. Each course is linked to a textbook via a Book.
# Teacher content (questions, tests, etc.) is tied to a Course.
# """
# class Course(models.Model):
#     user = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.CASCADE,
#         null=True,
#         blank=True
#     )
#     course_code = models.CharField(
#         max_length=50,
#         help_text='e.g: CS499',
#         default='CS499'
#     )
#     course_name = models.CharField(
#         max_length=250,
#         help_text='e.g: SR PROJ:TEAM SOFTWARE DESIGN',
#         default='Untitled Course'
#     )
#     course_crn = models.CharField(
#         max_length=50,
#         help_text='e.g: 54352',
#         default='0000'
#     )
#     course_semester = models.CharField(
#         max_length=50,
#         help_text='e.g: Fall 2021',
#         default='Fall 2021'
#     )
#     # Each course is associated with a textbook.
#     book = models.ForeignKey(
#         Book,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         help_text='Textbook associated with this course.'
#     )
#     teachers = models.ManyToManyField(
#         User,
#         related_name='courses',
#         blank=True,
#         limit_choices_to={'userprofile__role': 'teacher'}
#     )

#     def __str__(self):
#         return f"{self.course_code} - {self.course_name}"

#     def get_publisher_questions(self):
#         """
#         For a given course, return publisher-created questions.
#         This works by matching the course's textbook with publisher questions.
#         """
#         if self.book:
#             return Question.objects.filter(
#                 book=self.book,
#                 owner__userprofile__role='publisher'
#             )
#         return Question.objects.none()


# class QuestionQuerySet(models.QuerySet):
#     def visible_to_teacher(self, teacher_username):
#         teacher_book_ids = self.model._default_manager.filter(
#             course__teachers__username=teacher_username
#         ).values_list('course__book_id', flat=True).distinct()
        
#         return self.filter(
#             Q(owner__username=teacher_username, course__isnull=False) |
#             Q(owner__userprofile__role='publisher', book_id__in=teacher_book_ids)
#         )


# def get_visible_questions_for_teacher(teacher_username):
#     teacher_book_ids = Course.objects.filter(
#         teachers__username=teacher_username
#     ).values_list('book_id', flat=True).distinct()

#     questions = Question.objects.filter(
#         Q(owner__username=teacher_username, course__isnull=False) |
#         Q(owner__userprofile__role='publisher', book_id__in=teacher_book_ids)
#     )
#     return questions

# def teacher_dashboard(request):
#     # assuming request.user is a teacher
#     teacher_username = request.user.username
#     questions = get_visible_questions_for_teacher(teacher_username)
#     return render(request, 'teacher_dashboard.html', {'questions': questions})


# """
# QUESTION MODEL
# This model stores various types of questions. It supports multiple question types:
# - True/False, Multiple Choice, Short Answer, Essay, Matching, Multiple Selection, Fill in the Blank, Dynamic.
# For publisher-created questions, set the 'book' field.
# For teacher-created questions, set the 'course' field.
# Common fields include text, graphics, point values, and grading instructions.
# Type-specific fields include chapter, section, and a correct_answer.
# The include_formula field is specific to fill in the blank questions.
# """
# class Question(models.Model):
#     question_type_options = [
#         ('TF', 'True/False'),
#         ('MC', 'Multiple Choice'),
#         ('SA', 'Short Answer'),
#         ('ES', 'Essay'),
#         ('MA', 'Matching'),
#         ('MS', 'Multiple Selection'),
#         ('FB', 'Fill in the Blank'),
#         ('DY', 'Dynamic')  # For questions with dynamic data.
#     ]
#     # Teacher-created question: linked to a course.
#     course = models.ForeignKey(
#         Course,
#         on_delete=models.CASCADE,
#         null=True,
#         blank=True
#     )
#     # Publisher-created question: directly linked to a book.
#     book = models.ForeignKey(
#         Book,
#         on_delete=models.CASCADE,
#         null=True,
#         blank=True,
#         help_text="For publisher-created questions, associate with a book."
#     )
#     question_type = models.CharField(max_length=50, choices=question_type_options)
#     question_text = models.TextField(help_text='Question prompt.', default='Question text.', null=True)
    
#     # Common fields for visual elements and grading.
#     embedded_graphic = models.ImageField(max_length=200, null=True, blank=True)
#     correct_answer_graphic = models.ImageField(upload_to='answer_graphics/', null=True, blank=True)
#     default_points = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
#     estimated_time = models.IntegerField(default=1, help_text='Estimated time (in minutes) to answer the question.')
#     instructions_for_grading = models.TextField(null=True, blank=True)
#     references = models.CharField(max_length=200, null=True, blank=True, help_text="Reference text (optional).")
#     instructor_comment = models.TextField(null=True, blank=True)
    
#     # Fields used across several types for categorization.
#     chapter = models.PositiveIntegerField(default=0, help_text="Chapter number. Default is 0.")
#     section = models.PositiveIntegerField(default=0, help_text="Section number. Default is 0.")
#     # Used to store a single correct answer (e.g., for true/false, short answer, essay, fill in the blank).
#     correct_answer = models.TextField(null=True, blank=True, help_text="Correct answer for types needing a single answer.")
#     # Specific to fill-in-the-blank questions: indicates if a formula should be used.
#     include_formula = models.BooleanField(default=False, help_text="For fill in the blank: include a formula (default is No).")
    
#     owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def clean(self):
#         """
#         Custom validation: For publisher-created questions, ensure that the chapter field
#         is set to a non-zero value (indicating that the question is categorized properly).
#         """
#         super().clean()
#         if self.owner and hasattr(self.owner, 'userprofile'):
#             if self.owner.userprofile.role == 'publisher' and self.chapter == 0:
#                 raise ValidationError("Publisher-created questions must include a chapter number (non-zero).")
            


#     def __str__(self):
#         return f"[{self.get_question_type_display()}] {self.question_text[:50]}"

#     @property
#     def publisher_average_rating(self):
#         """
#         Returns the average rating for a publisher-created question.
#         Teachers can use this property to assess the aggregated feedback for such questions.
#         """
#         if self.owner and hasattr(self.owner, 'userprofile') and self.owner.userprofile.role == 'publisher':
#             avg = self.feedbacks.aggregate(Avg('rating'))['rating__avg']
#             return avg
#         return None
#     objects = QuestionQuerySet.as_manager()


# """
# ANSWER OPTION MODEL
# Used for storing answer choices for questions such as Multiple Choice or Multiple Selection.
# Each answer option can also include optional graphics or feedback.
# """
# class AnswerOption(models.Model):
#     question = models.ForeignKey(
#         Question,
#         on_delete=models.CASCADE,
#         related_name="answer_options"
#     )
#     text = models.TextField(help_text="Answer option text", null=True)
#     is_correct = models.BooleanField(default=False, help_text="Designates if this option is the correct answer.")
#     answer_graphic = models.ImageField(upload_to='answer_graphics/', null=True, blank=True)
#     response_feedback_text = models.TextField(null=True, blank=True)
#     response_feedback_graphic = models.ImageField(null=True, blank=True)

#     def __str__(self):
#         return self.text


# """
# MATCHING OPTION MODEL
# Instead of using a JSON field, this model stores matching pairs for matching-type questions.
# Each record corresponds to one pairing: an option and its corresponding match.
# """
# class MatchingOption(models.Model):
#     question = models.ForeignKey(
#         Question,
#         on_delete=models.CASCADE,
#         related_name="matching_options"
#     )
#     option_text = models.TextField(help_text="Option text (left side).")
#     match_text = models.TextField(help_text="Matching answer text (right side).")

#     def __str__(self):
#         return f"{self.option_text} -> {self.match_text}"


# """
# DYNAMIC QUESTION PARAMETER MODEL
# Used for questions that generate answers dynamically.
# Holds a formula and acceptable range, plus any additional parameters.
# """
# class DynamicQuestionParameter(models.Model):
#     question = models.OneToOneField(
#         Question,
#         on_delete=models.CASCADE,
#         related_name="dynamic_parameters"
#     )
#     formula = models.TextField(help_text="Formula for generating or validating the answer.")
#     range_min = models.DecimalField(max_digits=10, decimal_places=2, help_text="Minimum acceptable value.")
#     range_max = models.DecimalField(max_digits=10, decimal_places=2, help_text="Maximum acceptable value.")
#     additional_params = models.JSONField(
#         null=True,
#         blank=True,
#         help_text="Additional parameters for dynamic generation."
#     )

#     def __str__(self):
#         return f"Dynamic Params for QID {self.question.id}"


# """
# TEMPLATE MODEL
# Stores templates for test formatting.
# For teacher content, the template is linked to a Course.
# For publisher content, the template is linked directly to a Book.
# """
# class Template(models.Model):
#     # Teacher-created template: linked to a course.
#     course = models.ForeignKey(
#         Course,
#         on_delete=models.CASCADE,
#         null=True,
#         blank=True,
#         help_text="Course associated with this template (teacher content)."
#     )
#     # Publisher-created template: linked directly to a book.
#     book = models.ForeignKey(
#         Book,
#         on_delete=models.CASCADE,
#         null=True,
#         blank=True,
#         help_text="Book associated with this template (publisher content)."
#     )
#     name = models.CharField(max_length=200, unique=True, help_text="Template name.")
#     font_name = models.CharField(max_length=100, default="Arial")
#     font_size = models.IntegerField(default=12)
#     header_text = models.TextField(null=True, blank=True)
#     footer_text = models.TextField(null=True, blank=True)

#     def __str__(self):
#         return self.name


# """
# COVER PAGE MODEL
# Stores cover page details.
# Teacher cover pages are linked to a Course; publisher cover pages are linked to a Book.
# """
# class CoverPage(models.Model):
#     # Teacher-created cover page.
#     course = models.ForeignKey(
#         Course,
#         on_delete=models.CASCADE,
#         null=True,
#         blank=True,
#         help_text="Course associated with this cover page (teacher content)."
#     )
#     # Publisher-created cover page.
#     book = models.ForeignKey(
#         Book,
#         on_delete=models.CASCADE,
#         null=True,
#         blank=True,
#         help_text="Book associated with this cover page (publisher content)."
#     )
#     cover_page_name = models.CharField(max_length=200, help_text="Name of the cover page.")
#     test_number = models.CharField(max_length=50, help_text="Test number displayed on the cover page.")
#     test_date = models.DateField(help_text="Date of the test.")
#     test_filename = models.CharField(max_length=200, help_text="Filename displayed on the cover page.")
#     filename_present = models.BooleanField(default=False, help_text="Is the filename present on the cover page?")
#     STUDENT_NAME_CHOICES = [
#         ('top_left', 'Top Left'),
#         ('top_right', 'Top Right'),
#         ('below_title', 'Below Title'),
#     ]
#     student_name_location = models.CharField(
#         max_length=20,
#         choices=STUDENT_NAME_CHOICES,
#         default='top_left',
#         help_text="Location for the student's name on the cover page."
#     )
#     grading_instructions_for_key = models.TextField(blank=True, null=True, help_text="Grading instructions for the answer key.")

#     def __str__(self):
#         return f"{self.cover_page_name} - {self.test_number}"


# """
# ATTACHMENT MODEL
# Stores a file attachment.
# Teacher attachments are linked to a Course; publisher attachments are linked to a Book.
# This model is designed for users to simply upload a file from their machine.
# """
# class Attachment(models.Model):
#     # Teacher-created attachment.
#     course = models.ForeignKey(
#         Course,
#         on_delete=models.CASCADE,
#         null=True,
#         blank=True,
#         help_text="Course associated with this attachment (teacher content)."
#     )
#     # Publisher-created attachment.
#     book = models.ForeignKey(
#         Book,
#         on_delete=models.CASCADE,
#         null=True,
#         blank=True,
#         help_text="Book associated with this attachment (publisher content)."
#     )
#     file = models.FileField(upload_to="attachments/")

#     def __str__(self):
#         return self.file.name


# """
# TEST MODEL
# Represents a test or quiz.
# For teacher tests, link to a Course; for publisher tests, link directly to a Book.
# Includes fields for title, date, finalization status, and instructions.
# """
# class Test(models.Model):
#     # Teacher test: linked to a course.
#     course = models.ForeignKey(
#         Course,
#         on_delete=models.CASCADE,
#         null=True,
#         blank=True,
#         related_name='tests',
#         help_text="Course associated with this test (teacher content)."
#     )
#     # Publisher test: linked directly to a book.
#     book = models.ForeignKey(
#         Book,
#         on_delete=models.CASCADE,
#         null=True,
#         blank=True,
#         help_text="Book associated with this test (publisher content)."
#     )
#     title = models.CharField(max_length=200, help_text="e.g: Quiz 1, Test 1", default="Untitled Test.")
#     date = models.DateField(null=True, blank=True)
#     filename = models.CharField(max_length=200, null=True, blank=True, help_text="Generated filename for this test.")
#     is_final = models.BooleanField(default=False, help_text="Mark as True when test is published/finalized.")
#     template = models.ForeignKey(
#         Template,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True
#     )
#     attachments = models.ManyToManyField(Attachment, blank=True)
#     cover_instructions = models.TextField(null=True, blank=True, help_text="Test instructions on cover page.")
#     test_number = models.CharField(max_length=50, null=True, blank=True, help_text="Identifier, e.g. 'Test #1'")
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         # Return a string based on the context: course for teacher tests or book for publisher tests.
#         if self.course:
#             return f"{self.title} - {self.course.course_code}"
#         elif self.book:
#             return f"{self.title} - {self.book.title}"
#         return self.title


# """
# TEST QUESTION MODEL
# Links a question to a test. Each question in a test is assigned points and order.
# """
# class TestQuestion(models.Model):
#     test = models.ForeignKey(
#         Test,
#         on_delete=models.CASCADE,
#         related_name="test_questions"
#     )
#     question = models.ForeignKey(
#         Question,
#         on_delete=models.CASCADE,
#         related_name="test_appearances"
#     )
#     assigned_points = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
#     order = models.IntegerField(default=1, help_text="Order of question in the test.")
#     randomize = models.BooleanField(default=False)
#     special_instructions = models.TextField(null=True, blank=True)

#     class Meta:
#         unique_together = ('test', 'question')
#         ordering = ['order']

#     def __str__(self):
#         return f"Q{self.order} in {self.test.title}"


# """
# FEEDBACK MODEL
# Stores feedback for questions and tests.
# The rating is on a scale from 1 to 10.
# """
# class Feedback(models.Model):
#     # Existing fields
#     question = models.ForeignKey(
#         'Question',
#         on_delete=models.CASCADE,
#         null=True,
#         blank=True,
#         related_name="feedbacks"
#     )
#     test = models.ForeignKey(
#         'Test',
#         on_delete=models.CASCADE,
#         null=True,
#         blank=True,
#         related_name="feedbacks"
#     )
#     user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
#     rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 11)], null=True, blank=True)
#     comments = models.TextField(null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         if self.question:
#             return f"Feedback on Question {self.question.id}"
#         elif self.test:
#             return f"Feedback on Test {self.test.title}"
#         return "General Feedback"

# class FeedbackResponse(models.Model):
#     # Each response is linked to one feedback instance.
#     feedback = models.OneToOneField(
#         Feedback,
#         on_delete=models.CASCADE,
#         related_name="response"
#     )
#     # The publisher responding; limit choices if desired.
#     publisher = models.ForeignKey(
#         User,
#         on_delete=models.CASCADE,
#         limit_choices_to={'userprofile__role': 'publisher'}
#     )
#     response_text = models.TextField(help_text="Publisher response to the feedback.")
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"Response to Feedback {self.feedback.id} by {self.publisher.username}"


from django.db import models
from django.contrib.auth.models import User  # Standard Django user model.
from django.core.exceptions import ValidationError
from django.conf import settings
from django.db.models import Q, Avg

"""
BOOK MODEL
This model holds textbook/book details.
"""
class Book(models.Model):
    title = models.CharField(max_length=300)
    author = models.CharField(max_length=300, blank=True, null=True)
    version = models.CharField(max_length=300, blank=True, null=True)
    isbn = models.CharField(max_length=300, blank=True, null=True)
    link = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.title

    def get_feedback(self):
        from .models import Feedback  # Local import to avoid circular dependency.
        return Feedback.objects.filter(
            Q(question__book=self) | Q(test__course__book=self) | Q(test__book=self)
        ).distinct()


"""
USER PROFILE MODEL
Extends the built-in User with a role and an optional book association.
"""
class UserProfile(models.Model):
    role_choices = [
        ('webmaster', 'Webmaster'),
        ('publisher', 'Publisher'),
        ('teacher', 'Teacher'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    role = models.CharField(max_length=20, choices=role_choices)
    book = models.ForeignKey(
        Book,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Book associated with the publisher (required for publishers)."
    )

    def clean(self):
        if self.role == 'publisher' and not self.book:
            raise ValidationError("Publishers must have an associated book.")

    def __str__(self):
        return f"{self.user.username} ({self.role})"


"""
COURSE MODEL
Represents a teacher-created course.
"""
class Course(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    course_code = models.CharField(max_length=50, help_text='e.g: CS499', default='CS499')
    course_name = models.CharField(max_length=250, help_text='e.g: SR PROJ:TEAM SOFTWARE DESIGN', default='Untitled Course')
    course_crn = models.CharField(max_length=50, help_text='e.g: 54352', default='0000')
    course_semester = models.CharField(max_length=50, help_text='e.g: Fall 2021', default='Fall 2021')
    book = models.ForeignKey(
        Book,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Textbook associated with this course.'
    )
    teachers = models.ManyToManyField(
        User,
        related_name='courses',
        blank=True,
        limit_choices_to={'userprofile__role': 'teacher'}
    )

    def __str__(self):
        return f"{self.course_code} - {self.course_name}"

    def get_publisher_questions(self):
        if self.book:
            return Question.objects.filter(
                book=self.book,
                owner__userprofile__role='publisher'
            )
        return Question.objects.none()


"""
QUESTION MODEL
Stores various types of questions.
"""
class Question(models.Model):
    question_type_options = [
        ('TF', 'True/False'),
        ('MC', 'Multiple Choice'),
        ('SA', 'Short Answer'),
        ('ES', 'Essay'),
        ('MA', 'Matching'),
        ('MS', 'Multiple Selection'),
        ('FB', 'Fill in the Blank'),
        ('DY', 'Dynamic')
    ]
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="For publisher-created questions, associate with a book."
    )
    question_type = models.CharField(max_length=50, choices=question_type_options)
    question_text = models.TextField(help_text='Question prompt.', default='Question text.', null=True)
    embedded_graphic = models.ImageField(max_length=200, null=True, blank=True)
    correct_answer_graphic = models.ImageField(upload_to='answer_graphics/', null=True, blank=True)
    default_points = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    estimated_time = models.IntegerField(default=1, help_text='Estimated time (in minutes) to answer the question.')
    instructions_for_grading = models.TextField(null=True, blank=True)
    references = models.CharField(max_length=200, null=True, blank=True, help_text="Reference text (optional).")
    instructor_comment = models.TextField(null=True, blank=True)
    chapter = models.PositiveIntegerField(default=0, help_text="Chapter number. Default is 0.")
    section = models.PositiveIntegerField(default=0, help_text="Section number. Default is 0.")
    correct_answer = models.TextField(null=True, blank=True, help_text="Correct answer for types needing a single answer.")
    include_formula = models.BooleanField(default=False, help_text="For fill in the blank: include a formula (default is No).")
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()
        if self.owner and hasattr(self.owner, 'userprofile'):
            if self.owner.userprofile.role == 'publisher' and self.chapter == 0:
                raise ValidationError("Publisher-created questions must include a chapter number (non-zero).")

    def __str__(self):
        return f"[{self.get_question_type_display()}] {self.question_text[:50]}"

    @property
    def publisher_average_rating(self):
        if self.owner and hasattr(self.owner, 'userprofile') and self.owner.userprofile.role == 'publisher':
            avg = self.feedbacks.aggregate(Avg('rating'))['rating__avg']
            return avg
        return None


"""
ANSWER OPTION MODEL
"""
class AnswerOption(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="answer_options"
    )
    text = models.TextField(help_text="Answer option text", null=True)
    is_correct = models.BooleanField(default=False, help_text="Designates if this option is the correct answer.")
    answer_graphic = models.ImageField(upload_to='answer_graphics/', null=True, blank=True)
    response_feedback_text = models.TextField(null=True, blank=True)
    response_feedback_graphic = models.ImageField(null=True, blank=True)

    def __str__(self):
        return self.text


"""
MATCHING OPTION MODEL
"""
class MatchingOption(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="matching_options"
    )
    option_text = models.TextField(help_text="Option text (left side).")
    match_text = models.TextField(help_text="Matching answer text (right side).")

    def __str__(self):
        return f"{self.option_text} -> {self.match_text}"


"""
DYNAMIC QUESTION PARAMETER MODEL
"""
class DynamicQuestionParameter(models.Model):
    question = models.OneToOneField(
        Question,
        on_delete=models.CASCADE,
        related_name="dynamic_parameters"
    )
    formula = models.TextField(help_text="Formula for generating or validating the answer.")
    range_min = models.DecimalField(max_digits=10, decimal_places=2, help_text="Minimum acceptable value.")
    range_max = models.DecimalField(max_digits=10, decimal_places=2, help_text="Maximum acceptable value.")
    additional_params = models.JSONField(null=True, blank=True, help_text="Additional parameters for dynamic generation.")

    def __str__(self):
        return f"Dynamic Params for QID {self.question.id}"


"""
TEMPLATE MODEL
"""
class Template(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Course associated with this template (teacher content)."
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Book associated with this template (publisher content)."
    )
    name = models.CharField(max_length=200, unique=True, help_text="Template name.")
    font_name = models.CharField(max_length=100, default="Arial")
    font_size = models.IntegerField(default=12)
    header_text = models.TextField(null=True, blank=True)
    footer_text = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


"""
COVER PAGE MODEL
"""
class CoverPage(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Course associated with this cover page (teacher content)."
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Book associated with this cover page (publisher content)."
    )
    cover_page_name = models.CharField(max_length=200, help_text="Name of the cover page.")
    test_number = models.CharField(max_length=50, help_text="Test number displayed on the cover page.")
    test_date = models.DateField(help_text="Date of the test.")
    test_filename = models.CharField(max_length=200, help_text="Filename displayed on the cover page.")
    filename_present = models.BooleanField(default=False, help_text="Is the filename present on the cover page?")
    STUDENT_NAME_CHOICES = [
        ('top_left', 'Top Left'),
        ('top_right', 'Top Right'),
        ('below_title', 'Below Title'),
    ]
    student_name_location = models.CharField(max_length=20, choices=STUDENT_NAME_CHOICES, default='top_left', help_text="Location for the student's name on the cover page.")
    grading_instructions_for_key = models.TextField(blank=True, null=True, help_text="Grading instructions for the answer key.")

    def __str__(self):
        return f"{self.cover_page_name} - {self.test_number}"


"""
ATTACHMENT MODEL
"""
class Attachment(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Course associated with this attachment (teacher content)."
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Book associated with this attachment (publisher content)."
    )
    file = models.FileField(upload_to="attachments/")

    def __str__(self):
        return self.file.name


"""
TEST MODEL
Represents a test or quiz.
"""
class Test(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='tests',
        help_text="Course associated with this test (teacher content)."
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Book associated with this test (publisher content)."
    )
    title = models.CharField(max_length=200, help_text="e.g: Quiz 1, Test 1", default="Untitled Test.")
    date = models.DateField(null=True, blank=True)
    filename = models.CharField(max_length=200, null=True, blank=True, help_text="Generated filename for this test.")
    is_final = models.BooleanField(default=False, help_text="Mark as True when test is published/finalized.")
    template = models.ForeignKey(
        Template,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    attachments = models.ManyToManyField(Attachment, blank=True)
    cover_instructions = models.TextField(null=True, blank=True, help_text="Test instructions on cover page.")
    test_number = models.CharField(max_length=50, null=True, blank=True, help_text="Identifier, e.g. 'Test #1'")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.course:
            return f"{self.title} - {self.course.course_code}"
        elif self.book:
            return f"{self.title} - {self.book.title}"
        return self.title


"""
TEST QUESTION MODEL
Links a question to a test.
"""
class TestQuestion(models.Model):
    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name="test_questions"
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="test_appearances"
    )
    assigned_points = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    order = models.IntegerField(default=1, help_text="Order of question in the test.")
    randomize = models.BooleanField(default=False)
    special_instructions = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ('test', 'question')
        ordering = ['order']

    def __str__(self):
        return f"Q{self.order} in {self.test.title}"


"""
FEEDBACK MODEL
Stores feedback for questions and tests.
"""
class Feedback(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 11)]
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="feedbacks"
    )
    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="feedbacks"
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.question:
            return f"Feedback on Question {self.question.id}"
        elif self.test:
            return f"Feedback on Test {self.test.title}"
        return "General Feedback"


"""
FEEDBACK RESPONSE MODEL
Allows a publisher to respond to a teacher's feedback.
"""
class FeedbackResponse(models.Model):
    feedback = models.OneToOneField(
        Feedback,
        on_delete=models.CASCADE,
        related_name="response"
    )
    publisher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'userprofile__role': 'publisher'}
    )
    response_text = models.TextField(help_text="Publisher response to the feedback.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Response to Feedback {self.feedback.id} by {self.publisher.username}"
