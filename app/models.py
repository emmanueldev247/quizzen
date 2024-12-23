"""
This module defines the database models for the Quizzen application.

Classes:
    User: Represents a user in the system
    Quiz: Represents a quiz with relevant metadata
    QuizHistory: Tracks a user's quiz activity

Imports:
    - db: SQLAlchemy database instance from app.extensions.
    - datetime: Python's datetime module for handling date and time.
    - generate_password_hash, check_password_hash:
        Functions from werkzeug.security for password hashing and validation.
"""

from app.extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    """
    Represents a user in the system.

    Attributes:
        id (int): Primary key for the user.
        username (str): Unique username chosen by the user.
        email (str): Unique email address of the user.
        password_hash (str): Hashed password for authentication.
        first_name (str): First name of the user.
        last_name (str): Last name of the user.
        date_of_birth (date): Date of birth of the user.
        profile_picture (str): URL or file path of the user's profile picture.
        role (str): Role of the user
        quiz_history (list): List of quiz history associated with the user.

    Methods:
        set_password(password): Hashes and sets the user's password.
        check_password(password): Verifies the provided
                                  password against the hashed password.
    """

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    profile_picture = db.Column(db.String(255))
    role = db.Column(Enum('user', 'admin', name='role_types'), default='user')
    gender = db.Column(db.String(10), nullable=False)
    quiz_history = db.relationship('QuizHistory', backref='quiz',
                                   cascade='all, delete-orphan', lazy=True)

    def set_pasword(self, password):
        """
        Hashes and sets the user's password.

        Args:
            password (str): The plaintext password to be hashed.
        """
        if not password:
            raise ValueError("Password cannot be empty")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Verifies the provided password against the hashed password.

        Args:
            password (str): The plaintext password to verify.

        Returns:
            bool: True if the password matches, False otherwise.
        """
        if not password:
            return False
        return check_password_hash(self.password_hash, password)


class Quiz(db.Model):
    """
    Represents a quiz in the Quizzen application.

    Attributes:
        id (int): Primary key for the quiz.
        title (str): Title of the quiz.
        description (str): Description providing details about the quiz.
        category (str): Category or topic of the quiz.
        created_by (int): Foreign key linking the quiz to the creator.
        created_at (datetime): Timestamp of when the quiz was created.
        duration (int): Time limit for the quiz in minutes.
        public (bool): Indicates whether the quiz is public or private.
        questions (list): List of questions associated with the quiz.

    Relationships:
        - A quiz can have multiple questions,
          represented by the `questions` relationship.
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False,
                      default='No description provided')
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id',
                                                      ondelete='SET NULL'),
                            nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'),
                           nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    duration = db.Column(db.Integer, nullable=False)  # Duration in minutes
    public = db.Column(db.Boolean, default=True)  # Public or private quiz
    questions = db.relationship('Question',
                                backref=db.backref('quiz',
                                                   passive_deletes=True),
                                cascade='all, delete-orphan', lazy=True)
    quiz_history = db.relationship('QuizHistory',
                                   backref='quiz',
                                   cascade='all, delete-orphan', lazy=True)


class Question(db.Model):
    """
    Represents a question in a quiz.

    Attributes:
        id (int): Primary key for the question.
        quiz_id (int): Foreign key linking the question to its parent quiz.
        question_text (str): The text of the question.
        answer_choices (JSON): A list of answer options in JSON format.
        correct_answer (str): The correct answer for the question.
        question_type (str): Type of the question, e.g., 'multiple_choice'

    Relationships:
        - A question belongs to a single quiz,
          represented by the `quiz_id` foreign key.
    """
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer,
                        db.ForeignKey('quiz.id', ondelete='CASCADE'),
                        nullable=False, index=True)
    question_text = db.Column(db.String(512), nullable=False)
    """Store answer choices as a list in JSON format"""
    answer_choices = db.Column(db.JSON, nullable=False)
    correct_answer = db.Column(db.String(100), nullable=False)
    question_type = db.Column(db.String(50), default='multiple_choice')


class QuizHistory(db.Model):
    """
    Represents the history of a user's interaction with a quiz.

    Attributes:
        id (int): Primary key for the quiz history entry.
        user_id (int): Foreign key linking to the user who took the quiz.
        quiz_id (int): Foreign key linking to the quiz taken.
        score (int): Total score the user achieved in the quiz.
        date_taken (datetime): Timestamp of when the quiz was taken.
        answers (list): List of user's answers associated with quiz history.

    Relationships:
        - Links to the `UserAnswer` model to store
          individual answers for this quiz history.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer,
                        db.ForeignKey('user.id', ondelete='CASCADE'),
                        nullable=False)
    quiz_id = db.Column(db.Integer,
                        db.ForeignKey('quiz.id', ondelete='CASCADE'),
                        nullable=False)
    score = db.Column(db.Integer, nullable=False)  # Store the total score
    date_taken = db.Column(db.DateTime, default=datetime.utcnow)
    answers = db.relationship('UserAnswer', backref='quiz_history', 
                              cascade='all, delete-orphan', lazy=True)


class UserAnswer(db.Model):
    """
    Represents an individual answer provided by a user for a specific question.

    Attributes:
        id (int): Primary key for the user's answer entry.
        quiz_history_id (int): Foreign key linking to the quiz history.
        question_id (int): Foreign key linking to the question answered.
        user_answer (str): The user's submitted answer.
        is_correct (bool): Indicates whether the user's answer was correct.
    """
    id = db.Column(db.Integer, primary_key=True)
    quiz_history_id = db.Column(db.Integer,
                                db.ForeignKey('quiz_history.id',
                                              ondelete='CASCADE'),
                                nullable=False)
    question_id = db.Column(db.Integer,
                            db.ForeignKey('question.id', ondelete='CASCADE'),
                            nullable=False)
    user_answer = db.Column(db.String(100), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)


class Category(db.Model):
    """
    Represents a category of quizzes.

    Attributes:
        id (int): Primary key for the category.
        name (str): Unique name of the category.
        description (str): Optional description of the category.
        quizzes (list): List of quizzes associated with this category.

    Relationships:
        - Links to the `Quiz` model,
          associating multiple quizzes with the category.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    quizzes = db.relationship('Quiz',
                              backref=db.backref('category',
                                                 passive_deletes=True),
                              lazy=True)


class Leaderboard(db.Model):
    """
    Represents a leaderboard entry for tracking user scores and ranks.

    Attributes:
        id (int): Primary key for the leaderboard entry.
        user_id (int): Foreign key linking to the user.
        quiz_id (int): Foreign key linking to the quiz.
        score (int): User's score for the quiz.
        rank (int): User's rank based on their score in the quiz.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer,
                        db.ForeignKey('user.id', ondelete='CASCADE'),
                        nullable=False)
    quiz_id = db.Column(db.Integer,
                        db.ForeignKey('quiz.id', ondelete='CASCADE'),
                        nullable=False)
    score = db.Column(db.Integer, nullable=False)
    rank = db.Column(db.Integer, nullable=False)  # Rank based on score


class Notification(db.Model):
    """
    Represents a notification sent to a user.

    Attributes:
        id (int): Primary key for the notification.
        user_id (int): Foreign key linking to the recipient user.
        message (str): The notification message content.
        is_read (bool): Indicates if notification has been read by the user.
        date_sent (datetime): Timestamp of when the notification was sent.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer,
                        db.ForeignKey('user.id', ondelete='CASCADE'),
                        nullable=False)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False, index=True)
    date_sent = db.Column(db.DateTime, default=datetime.utcnow)
