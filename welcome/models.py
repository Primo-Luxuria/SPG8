from django.db import models
from django.contrib.auth.models import User  # Standard Django user model.
from django.core.exceptions import ValidationError
from django.conf import settings
from django.db.models import Q, Avg

"""
BOOK MODEL
This model holds textbook/book details.
It is used as a key connection point for publisher content,
and for teacher courses (each course references a Book).
"""
class Textbook(models.Model):
    title = models.CharField(max_length=300)
    author = models.CharField(max_length=300, blank=True, null=True)
    version = models.CharField(max_length=300, blank=True, null=True)
    isbn = models.CharField(max_length=300, blank=True, null=True)
    link = models.URLField(blank=True, null=True)
    publisher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    published = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title

    def get_feedback(self):
        """
        Retrieve all feedback related to this book. Feedback can come from:
          - Questions directly linked to this book.
          - Tests that belong to courses using this book.
          - Tests directly created for a book (publisher tests).
        The use of Q objects allows for combining these query conditions.
        """
        from .models import Feedback  # Local import to avoid circular dependency.
        return Feedback.objects.filter(
            Q(question__book=self) | Q(test__course__book=self) | Q(test__book=self)
        ).distinct()


"""
USER PROFILE MODEL
Extends the built-in User with a role and an optional book association.
For publishers, the clean() method enforces that a Book is set.
"""
class UserProfile(models.Model):
    role_choices = [
        ('webmaster', 'Webmaster'),
        ('publisher', 'Publisher'),
        ('teacher', 'Teacher'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    role = models.CharField(max_length=20, choices=role_choices)
    
    def clean(self):
        # Enforce that publishers have an associated book.
        if self.role == 'publisher' and not self.book:
            raise ValidationError("Publishers must have an associated book.")

    def __str__(self):
        return f"{self.user.username} ({self.role})"


"""
COURSE MODEL
Represents a teacher-created course. Each course is linked to a textbook via a Book.
Teacher content (questions, tests, etc.) is tied to a Course.
"""
class Course(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    course_id = models.CharField(
        max_length=50,
        help_text='e.g: CS499',
        default='CS499'
    )
    name = models.CharField(
        max_length=250,
        help_text='e.g: SR PROJ:TEAM SOFTWARE DESIGN',
        default='Untitled Course'
    )
    crn = models.CharField(
        max_length=50,
        help_text='e.g: 54352',
        default='0000'
    )
    #semester
    sem = models.CharField( 
        max_length=50,
        help_text='e.g: Fall 2021',
        default='Fall 2021'
    ) 
    # Each course is associated with a textbook.
    textbook = models.ForeignKey(
        Textbook,
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
    published = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.course_id} - {self.name}"

    def get_publisher_questions(self):
        """
        For a given course, return publisher-created questions.
        This works by matching the course's textbook with publisher questions.
        """
        if self.textbook:
            return Question.objects.filter(
                textbook=self.textbook,
                owner__userprofile__role='publisher'
            )
        return Question.objects.none()


"""
QUESTION MODEL
This model stores various types of questions. It supports multiple question types:
- True/False, Multiple Choice, Short Answer, Essay, Matching, Multiple Selection, Fill in the Blank, Dynamic.
For publisher-created questions, set the 'book' field.
For teacher-created questions, set the 'course' field.
Common fields include text, graphics, point values, and grading instructions.
Type-specific fields include chapter, section, and a correct_answer.
The include_formula field is specific to fill in the blank questions.
"""
class Question(models.Model):
    question_type_options = [
        ('tf', 'True/False'),
        ('mc', 'Multiple Choice'),
        ('sa', 'Short Answer'),
        ('es', 'Essay'),
        ('ma', 'Matching'),
        ('ms', 'Multiple Selection'),
        ('fb', 'Fill in the Blank'),
        ('dy', 'Dynamic')  # For questions with dynamic data.
    ]
    # Teacher-created question: linked to a course.
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    # Publisher-created question: directly linked to a book.
    textbook = models.ForeignKey(
        Textbook,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="For publisher-created questions, associate with a book."
    )
    qtype = models.CharField(max_length=50, choices=question_type_options)
    text = models.TextField(help_text='Question prompt.', default='Question text.', null=True)
    
    # Common fields for visual elements and grading.
    img = models.ImageField(upload_to='graphics/', max_length=200, null=True, blank=True) #embedded graphic
    ansimg = models.ImageField(upload_to='answer_graphics/', null=True, blank=True) #answer graphic
    score = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    eta = models.IntegerField(default=1, help_text='Estimated time (in minutes) to answer the question.')
    directions = models.TextField(null=True, blank=True)
    reference = models.CharField(max_length=200, null=True, blank=True, help_text="Reference text (optional).")
    comments = models.TextField(null=True, blank=True)
    
    # Fields used across several types for categorization.
    chapter = models.PositiveIntegerField(default=0, help_text="Chapter number. Default is 0.")
    section = models.PositiveIntegerField(default=0, help_text="Section number. Default is 0.")
    # Used to store a single correct answer (e.g., for true/false, short answer, essay, fill in the blank).
    answer = models.TextField(null=True, blank=True, help_text="Correct answer for types needing a single answer.")
    
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """
        Custom validation: For publisher-created questions, ensure that the chapter field
        is set to a non-zero value (indicating that the question is categorized properly).
        """
        super().clean()
        if self.owner and hasattr(self.owner, 'userprofile'):
            if self.owner.userprofile.role == 'publisher' and self.chapter < 0:
                raise ValidationError("Publisher-created questions must include a chapter number (non-negative).")

    def __str__(self):
        return f"[{self.get_qtype_display()}] {self.text[:50]}"

    @property
    def publisher_average_rating(self):
        """
        Returns the average rating for a publisher-created question.
        Teachers can use this property to assess the aggregated feedback for such questions.
        """
        if self.owner and hasattr(self.owner, 'userprofile') and self.owner.userprofile.role == 'publisher':
            avg = self.feedbacks.aggregate(Avg('rating'))['rating__avg']
            return avg
        return None


"""
OPTION MODEL
Used for storing answer choices for questions such as Multiple Choice or Multiple Selection.
Each answer option can also include optional graphics or feedback.
"""
class Options(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="question_options"
    )
    text = models.TextField(help_text="Answer option text", null=True)

    def __str__(self):
        return self.text


"""
ANSWER MODEL
"""
class Answers(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="question_answers"
    )
    text = models.TextField(help_text="Correct answer text", null=True)
    answer_graphic = models.ImageField(upload_to='answer_graphics/', null=True, blank=True)
    response_feedback_text = models.TextField(null=True, blank=True)
    response_feedback_graphic = models.ImageField(null=True, blank=True)

    def __str__(self):
        return self.text



"""
DYNAMIC QUESTION PARAMETER MODEL
Used for questions that generate answers dynamically.
Holds a formula and acceptable range, plus any additional parameters.
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
    additional_params = models.JSONField(
        null=True,
        blank=True,
        help_text="Additional parameters for dynamic generation."
    )

    def __str__(self):
        return f"Dynamic Params for QID {self.question.id}"


"""
TEMPLATE MODEL
Stores templates for test formatting.
For teacher content, the template is linked to a Course.
For publisher content, the template is linked directly to a Book.
"""
class Template(models.Model):
    # Teacher-created template: linked to a course.
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Course associated with this template (teacher content)."
    )
    # Publisher-created template: linked directly to a book.
    textbook = models.ForeignKey(
        Textbook,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Book associated with this template (publisher content)."
    )
    name = models.CharField(max_length=200, unique=True, help_text="Template name.")
    titleFont = models.CharField(max_length=100, default="Arial")
    titleFontSize = models.IntegerField(default=48)
    subtitleFont = models.CharField(max_length=100, default="Arial")
    subtitleFontSize = models.IntegerField(default=24)
    bodyFont = models.CharField(max_length=100, default="Arial")
    bodyFontSize = models.IntegerField(default=12)
    pageNumbersInHeader = models.BooleanField(default=False)
    pageNumbersInFooter = models.BooleanField(default=False)
    headerText = models.TextField(null=True, blank=True)
    footerText = models.TextField(null=True, blank=True)
    coverPage = models.IntegerField(default=0)
    partStructure = models.JSONField(null=True, blank=True, help_text="JSON representation of the test part structure")
    def __str__(self):
        return self.name


"""
COVER PAGE MODEL
Stores cover page details.
Teacher cover pages are linked to a Course; publisher cover pages are linked to a Book.
"""
class CoverPage(models.Model):
    # Teacher-created cover page.
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Course associated with this cover page (teacher content)."
    )
    # Publisher-created cover page.
    textbook = models.ForeignKey(
        Textbook,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Book associated with this cover page (publisher content)."
    )
    name = models.CharField(max_length=200, help_text="Name of the cover page.")
    testNum = models.CharField(max_length=50, help_text="Test number displayed on the cover page.")
    date = models.DateField(help_text="Date of the test.")
    file = models.CharField(max_length=200, help_text="Filename displayed on the cover page.")
    showFilename = models.BooleanField(default=False, help_text="Is the filename present on the cover page?")
    STUDENT_NAME_CHOICES = [
        ('TL', 'Top Left'),
        ('TR', 'Top Right'),
        ('BT', 'Below Title'),
    ]
    blank = models.CharField(
        max_length=20,
        choices=STUDENT_NAME_CHOICES,
        default='top_left',
        help_text="Location for the student's name on the cover page."
    )
    instructions = models.TextField(blank=True, null=True, help_text="Grading instructions for the answer key.")
    published = models.BooleanField(default=False)


    def __str__(self):
        return f"{self.name} - {self.testNum}"


"""
ATTACHMENT MODEL
Stores a file attachment.
Teacher attachments are linked to a Course; publisher attachments are linked to a Book.
This model is designed for users to simply upload a file from their machine.
"""
class Attachment(models.Model):
    # Teacher-created attachment.
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Course associated with this attachment (teacher content)."
    )
    # Publisher-created attachment.
    textbook = models.ForeignKey(
        Textbook,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Book associated with this attachment (publisher content)."
    )
    name = models.CharField(max_length=300, help_text="attachment name")
    file = models.FileField(upload_to="attachments/")
    published = models.BooleanField(default=False)
    def __str__(self):
        return self.file.name


"""
TEST MODEL
Represents a test or quiz.
For teacher tests, link to a Course; for publisher tests, link directly to a Book.
Includes fields for title, date, finalization status, and instructions.
"""
class Test(models.Model):
    # Teacher test: linked to a course.
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='tests',
        help_text="Course associated with this test (teacher content)."
    )
    # Publisher test: linked directly to a book.
    textbook = models.ForeignKey(
        Textbook,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Book associated with this test (publisher content)."
    )
    name = models.CharField(max_length=200, help_text="e.g: Quiz 1, Test 1", default="Untitled Test.")
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        # Return a string based on the context: course for teacher tests or book for publisher tests.
        if self.course:
            return f"{self.name} - {self.course.course_id}"
        elif self.textbook:
            return f"{self.name} - {self.textbook.title}"
        return self.name

class TestPart(models.Model):
    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name='parts',
        help_text="Test this part belongs to"
    )
    part_number = models.IntegerField(default=1, help_text="Part number within the test")
    
    def __str__(self):
        return f"Part {self.part_number} of {self.test.name}"

class TestSection(models.Model):
    part = models.ForeignKey(
        TestPart,
        on_delete=models.CASCADE,
        related_name='sections',
        help_text="Part this section belongs to"
    )
    section_number = models.IntegerField(default=1, help_text="Section number within the part")
    question_type = models.CharField(max_length=50, help_text="Type of questions in this section")
    
    def __str__(self):
        return f"Section {self.section_number} in Part {self.part.part_number} of {self.part.test.name}"





"""
TEST QUESTION MODEL
Links a question to a test. Each question in a test is assigned points and order.
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
    section = models.ForeignKey(TestSection, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        unique_together = ('test', 'question')
        ordering = ['order']

    def __str__(self):
        return f"Q{self.order} in {self.test.name}"


"""
FEEDBACK MODEL
Stores feedback for questions and tests.
The rating is on a scale from 1 to 5.
"""
class Feedback(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
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
            return f"Feedback on Test {self.test.name}"
        return "General Feedback"