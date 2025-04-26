from models import Base, engine, QuestionType
from sqlalchemy.orm import sessionmaker

# Create all tables if they don't exist already.
Base.metadata.create_all(engine)

def insert_question_types():
    Session = sessionmaker(bind=engine)
    session = Session()

    # Define a list of question types. Adjust the names and descriptions as needed.
    question_types = [
        QuestionType(name="Multiple Choice", description="A question with several options, one of which is correct."),
        QuestionType(name="True/False", description="A question with two possible answers: True or False."),
        QuestionType(name="Short Answer", description="A question that requires a brief text response."),
        QuestionType(name="Essay", description="A question that requires a long, written answer."),
        QuestionType(name="Fill in the Blank", description="A question where a missing word or phrase must be supplied."),
        QuestionType(name="Matching", description="A question where items must be paired with corresponding items."),
        # Add any additional question types here.
    ]

    # Insert each question type into the database.
    for qt in question_types:
        session.add(qt)
    
    # Commit the session to persist changes.
    session.commit()
    session.close()
    print("Inserted question types successfully!")

if __name__ == "__main__":
    insert_question_types()
