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

import ulid
from app.extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.types import Enum


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

    id = db.Column(db.String(16), primary_key=True, 
                    default=lambda: str(ulid.new()).lower()[:16])
    username = db.Column(db.String(80), unique=True, nullable=True, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)
    has_password = db.Column(db.Boolean, default=False, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    profile_picture = db.Column(db.String(255))
    role = db.Column(Enum('user', 'admin',
                          name='role_types', create_type=True),
                     default='user')
    gender = db.Column(Enum('male', 'female', 'others',
                            name='gender_types', create_type=True),
                       default='others', nullable=False)
    quiz_history = db.relationship('QuizHistory', backref='user',
                                   cascade='all, delete-orphan', lazy=True)

    def set_password(self, password):
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
    id = db.Column(db.String(16), primary_key=True, 
                    default=lambda: str(ulid.new()).lower()[:16])
    title = db.Column(db.String(255), nullable=False,
                      default='Untitled Quiz')
    description = db.Column(db.Text, nullable=True, 
                        default='No description provided')
    category = db.Column(db.String(100), nullable=True, default=None)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id',
                                                      ondelete='SET NULL'),
                            nullable=True, index=True)
    created_by = db.Column(db.String(16), db.ForeignKey('user.id'),
                           nullable=False, index=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    max_score = db.Column(db.Integer, default=0)
    duration = db.Column(db.Integer, nullable=False)  # Duration in minutes
    public = db.Column(db.Boolean, default=False)  # Public or private quiz
    user = db.relationship('User', back_populates='quizzes')
    questions = db.relationship('Question',
                                backref=db.backref('quiz',
                                                   passive_deletes=True),
                                cascade='all, delete-orphan', lazy=True)
    quiz_history = db.relationship('QuizHistory',
                                   backref='quiz',
                                   cascade='all, delete-orphan', lazy=True)

    def __repr__(self):
        return f'<Quiz {self.id} - {self.title}>'
    
    def calculate_max_score(self):
        """Calculate the max_score by summing points of all related questions."""
        self.max_score = sum(question.points for question in self.questions)

class Question(db.Model):
    """Question Model"""
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.String(16),
                        db.ForeignKey('quiz.id', ondelete='CASCADE'),
                        nullable=False, index=True)
    question_text = db.Column(db.String(512), nullable=False)
    is_multiple_response = db.Column(db.Boolean, default=False, nullable=False)
    question_type = db.Column(Enum('multiple_choice', 'short_answer',
                                    name="question_type", create_type=True),
                              default='multiple_choice', nullable=False)
    points = db.Column(db.Integer, nullable=False, default=1)
    
    # Relationships
    quiz = db.relationship('Quiz', back_populates='questions')
    answer_choices = db.relationship('AnswerChoice', 
        back_populates='question', cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<Question {self.id} - {self.question_text}>'


class AnswerChoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    text = db.Column(db.String(255), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False, default=False)

    # Relationships
    question = db.relationship('Question', back_populates='answer_choices')

    def __repr__(self):
        return f'<AnswerChoice {self.id} - {self.text}>'


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
    id = db.Column(db.String(16), primary_key=True, 
                    default=lambda: str(ulid.new()).lower()[:16])
    user_id = db.Column(db.String(16),
                        db.ForeignKey('user.id', ondelete='CASCADE'),
                        nullable=False, index=True)
    quiz_id = db.Column(db.String(16),
                        db.ForeignKey('quiz.id', ondelete='CASCADE'),
                        nullable=False, index=True)
    score = db.Column(db.Integer, nullable=False)  # Store the total score
    date_taken = db.Column(db.DateTime, server_default=db.func.now())
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
    quiz_history_id = db.Column(db.String(16),
                                db.ForeignKey('quiz_history.id',
                                              ondelete='CASCADE'),
                                nullable=False, index=True)
    question_id = db.Column(db.Integer,
                            db.ForeignKey('question.id', ondelete='CASCADE'),
                            nullable=False, index=True)
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
                              backref=db.backref('related_category',
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
    id = db.Column(db.String(16), primary_key=True, 
                    default=lambda: str(ulid.new()).lower()[:16])
    user_id = db.Column(db.String(16),
                        db.ForeignKey('user.id', ondelete='CASCADE'),
                        nullable=False, index=True)
    quiz_id = db.Column(db.String(16),
                        db.ForeignKey('quiz.id', ondelete='CASCADE'),
                        nullable=False, index=True)
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
    user_id = db.Column(db.String(16),
                        db.ForeignKey('user.id', ondelete='CASCADE'),
                        nullable=False, index=True)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False, index=True)
    date_sent = db.Column(db.DateTime, server_default=db.func.now())


class UsedToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(256), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
