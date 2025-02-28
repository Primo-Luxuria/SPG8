# from django.test import TestCase

# # Create your tests here.

import unittest
from django.test import TransactionTestCase
from django.db import transaction, IntegrityError
from django.contrib.auth.models import User
from welcome.models import Course, UserProfile, Question, Test, Feedback, Template


class TestQuizPressDBSchema(TransactionTestCase):
    
    def setUp(self):
        """Set up test database and user"""
        with transaction.atomic():
            self.user = User.objects.create(username="testuser", email="test@example.com")

    def tearDown(self):
        """Clean up test data after each test"""
        User.objects.filter(username="testuser").delete()
        Course.objects.filter(course_code="TEST123").delete()
        UserProfile.objects.filter(user=self.user).delete()

    def test_database_schema(self):
        """Ensure database has the required tables"""
        tables = set(self._get_existing_tables())
        required_tables = {
            "auth_group", "django_content_type", "auth_permission", "auth_group_permissions",
            "auth_user", "auth_user_groups", "auth_user_user_permissions", "django_admin_log",
            "django_migrations", "django_session", "welcome_attachment", "welcome_course",
            "welcome_question", "welcome_template", "welcome_test", "welcome_feedback",
            "welcome_test_attachments", "welcome_testquestion", "welcome_userprofile"
        }
        missing_tables = required_tables - tables
        self.assertFalse(missing_tables, f"Missing tables: {missing_tables}")

    def _get_existing_tables(self):
        """Helper function to get list of database tables"""
        with transaction.atomic():
            with self.connection.cursor() as cursor:
                cursor.execute("SHOW TABLES;")
                return [row[0] for row in cursor.fetchall()]

    def test_unique_constraints(self):
        """Ensure unique constraints on fields"""
        with transaction.atomic():
            Course.objects.create(course_code="TEST123", name="Sample Course")
        
        # Expect IntegrityError when inserting duplicate course_code
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Course.objects.create(course_code="TEST123", name="Duplicate Course")

    def test_foreign_key_constraints(self):
        """Ensure foreign key relationships exist"""
        foreign_keys = [
            ("welcome_question", "course_id", "welcome_course"),
            ("welcome_question", "owner_id", "auth_user"),
            ("welcome_test", "course_id", "welcome_course"),
            ("welcome_test", "template_id", "welcome_template"),
            ("welcome_feedback", "user_id", "auth_user"),
            ("welcome_feedback", "question_id", "welcome_question"),
            ("welcome_feedback", "test_id", "welcome_test"),
            ("welcome_userprofile", "user_id", "auth_user")
        ]
        with transaction.atomic():
            with self.connection.cursor() as cursor:
                for table, column, ref_table in foreign_keys:
                    cursor.execute(f"""
                        SELECT CONSTRAINT_NAME
                        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                        WHERE TABLE_NAME = '{table}'
                        AND COLUMN_NAME = '{column}'
                        AND REFERENCED_TABLE_NAME = '{ref_table}';
                    """)
                    result = cursor.fetchone()
                    self.assertIsNotNone(result, f"Foreign key constraint missing: {table}.{column} -> {ref_table}")

    def test_insert_sample_data(self):
        """Insert sample data and validate insertion"""
        with transaction.atomic():
            course = Course.objects.create(course_code="SAMPLE123", name="Test Course")
            self.assertIsNotNone(course)

            template = Template.objects.create(name="Sample Template")
            self.assertIsNotNone(template)

            test = Test.objects.create(course=course, template=template)
            self.assertIsNotNone(test)

            feedback = Feedback.objects.create(user=self.user, test=test)
            self.assertIsNotNone(feedback)

    def test_user_profile_creation(self):
        """Test user profile creation"""
        with transaction.atomic():
            profile = UserProfile.objects.create(user=self.user, role="Student")
            self.assertEqual(profile.user.username, "testuser")
            self.assertEqual(profile.role, "Student")


if __name__ == "__main__":
    unittest.main()


