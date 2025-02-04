"""
    Defined routes:
      - '/dashboard' GET -> user_dashboard
      - '/admin/dashboard' GET -> admin_dashboard
      - '/quiz/new' POST -> create_quiz
      - '/quiz/<quiz_id>/edit' GET -> get_quiz
      - '/quiz/<quiz_id>/edit' POST -> post_quiz
      - '/quiz/<quiz_id>/edit' PUT -> update_quiz
      - '/quiz/<quiz_id>/edit' DELETE -> delete_quiz
      - '/quiz/<quiz_id>/publish' POST -> publish_quiz
      - '/quiz/<quiz_id>/unpublish' POST -> unpublish_quiz

      - '/quiz/<quiz_id>/question/new' GET -> create_question
      - '/.../question/<question_id>/edit' DELETE -> get_question
      - '/.../question/<question_id>/edit' POST -> save_question
      - '/.../question/<question_id>/edit' PUT -> update_question
      - '/.../question/<question_id>/edit' DELETE -> delete_question

      - '/admin/library' GET -> admin_library
      - '/admin/profile' GET -> admin_profile
"""

import humanize
import json
import os
import re
import random
import requests
import smtplib
import ulid
from flask import (
    abort,
    current_app, flash, jsonify,
    redirect, render_template, request,
    send_from_directory, session, url_for
)
from flask_limiter.errors import RateLimitExceeded
from functools import wraps
from itsdangerous import (
    BadSignature, SignatureExpired,
    URLSafeTimedSerializer as Serializer
)
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename
from wtforms import Form, StringField, TextAreaField, validators

from app.extensions import db, full_bp, limiter
from app.models import (
    AnswerChoice, Category, Leaderboard, Notification,
    Question, Quiz, QuizHistory, User
)
from app.routes import (
    logger, rate_limit_exceeded
)


def auth_required(f):
    """Auth required function"""
    @wraps(f)
    def decorated(*args, **kwargs):
        """Auth required decorator"""
        logger.info(f"Auth Attempt")
        if 'user_id' not in session:
            logger.error(f"Session token missing")
            flash("You need to log in first", "error")
            return redirect(url_for('full_bp.login'))

        try:
            user_id = session['user_id']
            current_user = User.query.get(user_id)

            if not current_user:
                logger.error("Invalid Token")
                flash("You need to log in first", "error")
                return redirect(url_for('full_bp.login'))

        except Exception as e:
            logger.error(f"Invalid Token, Error: {str(e)}")
            flash("You need to log in first", "error")
            return redirect(url_for('full_bp.login'))

        return f(current_user, *args, **kwargs)
    return decorated


def admin_check(f):
    """Grants role privileges"""
    @wraps(f)
    def decorated(*args, **kwargs):
        """Auth required decorator"""
        logger.info(f"role-based checks")
        if 'user_role' not in session:
            logger.error(f"Session token missing")
            flash("You need to log in first", "error")
            return redirect(url_for('full_bp.login'))
        try:
            if session['user_role'] != 'admin':
                return redirect(url_for('full_bp.user_dashboard'))
        except Exception as e:
            logger.error(f"Invalid Token, Error: {str(e)}")
            flash("You need to log in first", "error")
            return redirect(url_for('full_bp.login'))
        return f(*args, **kwargs)
    return decorated


@full_bp.errorhandler(RateLimitExceeded)
def handle_rate_limit_exceeded(e):
    return rate_limit_exceeded(e)


@full_bp.route('/dashboard')
@auth_required
def user_dashboard(current_user):
    """User dashboard"""

    if current_user.role == "admin":
        base_template = "base_admin_dashboard.html"
        no_quiz = "no-quiz-admin2.html"
    else:
        base_template = "base_user_dashboard.html"
        no_quiz = "no-quiz-user.html"

    history = QuizHistory.query.filter_by(user_id=current_user.id).all()
    query = Quiz.query.filter_by(public=True)
    quizzes = query.order_by(Quiz.created_at.desc()).all()

    leaderboard = Leaderboard.query.order_by(
        Leaderboard.score.desc()
    ).limit(10).all()
    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Notification.date_sent.desc()
    ).all()
    categories = Category.query.order_by(Category.name.asc()).all()

    return render_template(
        'dashboard.html',
        title='Dashboard',
        base_template=base_template,
        no_quiz=no_quiz,
        user=current_user,
        quizzes=quizzes,
        history=history,
        categories=categories,
        leaderboard=leaderboard,
        notifications=notifications,
        user_authenticated = 'user_id' in session
    )

@full_bp.route('/quiz/new', methods=['POST'])
@auth_required
@admin_check
@limiter.limit("5 per minute")
def create_quiz(current_user):
    """Create a new quiz"""
    try:
        logger.debug(f"{request.method} - Create quiz attempt")

        try:
            data = request.get_json() if request.is_json else request.form
        except Exception as parse_error:
            return jsonify({
                "success": False,
                "error": "Failed to parse data",
                "details": str(parse_error)
            }), 400

        title = data.get('title', '').strip()
        description = data.get('description').strip()
        category_id = data.get('category').strip()
        duration = data.get('duration', '0')

        if not description:
            description = None
        if not title:
            return jsonify({
                'success': False,
                'message': 'Title is required'
            }), 400
        if not category_id:
            return jsonify({
                'success': False,
                'message': 'Category is required'
            }), 400

        try:
            category_id = int(category_id)
            if category_id <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'message': 'Category ID must be a positive integer'
            }), 400

        try:
            duration = int(duration)
            if duration <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'message': 'Duration must be a positive integer'
            }), 400


        quiz = Quiz(
            title=title,
            description=description,
            category_id=category_id,
            duration=int(duration),
            created_by=current_user.id
        )

        db.session.add(quiz)
        db.session.commit()

        question_id = str(ulid.new()).lower()[:16]

        return jsonify({
            'success': True,
            'redirect_url': url_for('full_bp.get_question',
                                    quiz_id=quiz.id,
                                    question_id=question_id)
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error during quiz creation: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred. Please try again'
        }), 500


@full_bp.route('/quiz/<quiz_id>', methods=['GET'])
@full_bp.route('/quiz/<quiz_id>/edit', methods=['GET'])
@auth_required
@admin_check
@limiter.limit("20 per minute")
def get_quiz(current_user, quiz_id):
    """Get a quiz for edit"""
    logger.info(f"Viewing a quiz attempt")
    quiz = Quiz.query.get_or_404(quiz_id)

    if quiz.created_by != current_user.id:
        # Test
        return redirect(url_for('full_bp.user_dashboard'))
    return render_template(
        'edit_quiz.html',
        quiz=quiz,
        title=f"Quiz: {quiz.title}",
        user_authenticated = 'user_id' in session
    )


@full_bp.route('/quiz/<quiz_id>', methods=['POST'])
@full_bp.route('/quiz/<quiz_id>/edit', methods=['POST'])
@auth_required
@admin_check
@limiter.limit("10 per minute")
def post_quiz(current_user, quiz_id):
    """Add question to a quiz"""
    try:
        quiz = Quiz.query.get_or_404(quiz_id)
        if quiz.created_by != current_user.id:
            return redirect(url_for('full_bp.user_dashboard'))
        try:
            data = request.get_json() if request.is_json else request.form
        except Exception as parse_error:
            return jsonify({
                "success": False,
                "error": "Failed to parse data",
                "details": str(parse_error)
            }), 400

        if not data:
            return jsonify({
                "success": False,
                "error": "Invalid input",
                "message": "Request body is missing or malformed"
            }), 400

        required_f = ['question_text', 'question_type', 'answer_choices']
        missing_fields = [field for field in required_f if field not in data]

        if missing_fields:
            x_fields = ', '.join(missing_fields)
            return jsonify({
                "success": False,
                "error": "Invalid question data",
                "message": f"Missing required fields: {x_fields}"
            }), 400

        question_text = data.get('question').strip()
        question_type = data.get('question_type').strip()
        answer_choices = data.getlist('answer_choices')
        points = data.get('points', '0')

        try:
            points = int(points)
            if points <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'message': 'Points must be a positive integer'
            }), 400

        if question_type == 'multiple_choice' and len(answer_choices) < 2:
            return jsonify({
                "success": False,
                "message": "Multiple choice questions need at least 2 options"
            }), 400

        new_question = Question(
            quiz_id=quiz_id,
            question_text=question_text,
            question_type=question_type,
            points=points
        )
        db.session.add(new_question)
        db.session.flush()

        for option in answer_choices:
            new_question.answer_choices.append(
                AnswerChoice(
                    question_id=new_question.id,
                    text=option["text"],
                    is_correct=option['isCorrect']
                )
            )
        quiz.calculate_max_score()
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Question added successfully"
        }), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error during question addition: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Error adding question"
        }), 500


@full_bp.route('/quiz/<quiz_id>', methods=['PUT'])
@full_bp.route('/quiz/<quiz_id>/edit', methods=['PUT'])
@auth_required
@admin_check
@limiter.limit("10 per minute")
def update_quiz(current_user, quiz_id):
    """Update a quiz"""
    try:
        quiz = Quiz.query.get_or_404(quiz_id)
        if quiz.created_by != current_user.id:
            return redirect(url_for('full_bp.user_dashboard'))
        try:
            data = request.get_json() if request.is_json else request.form
        except Exception as parse_error:
            return jsonify({
                "success": False,
                "error": "Failed to parse data",
                "details": str(parse_error)
            }), 400

        if not data:
            return jsonify({
                "success": False,
                "error": "Invalid input",
                "message": "Request body is missing or malformed"
            }), 400

        if 'title' in data:
            quiz.title = data['title']

        if 'description' in data:
            quiz.description = data['description']

        if 'duration' in data:
            try:
                quiz.duration = int(data['duration'])
                if quiz.duration <= 0:
                    raise ValueError("Duration must be a positive integer")
            except ValueError as ve:
                return jsonify({
                    "success": False,
                    "error": "Invalid input",
                    "message": "Duration must be a positive integer"
                }), 400

        if 'category' in data:
            try:
                quiz.category_id = int(data['category'])
                if quiz.category_id <= 0:
                    raise ValueError("Category ID must be a positive integer")
            except ValueError as ve:
                return jsonify({
                    "success": False,
                    "error": "Invalid input",
                    "message": "Category ID must be a positive integer"
                }), 400

        if 'public' in data:
            if not isinstance(data['public'], bool):
                return jsonify({
                    "success": False,
                    "error": "Invalid input",
                    "message": "Public must be a boolean"
                }), 400
            quiz.public = data['public']

        quiz.calculate_max_score()
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Quiz updated successfully"
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating quiz: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Error updating quiz"
        }), 500


@full_bp.route('/quiz/<quiz_id>', methods=['DELETE'])
@full_bp.route('/quiz/<quiz_id>/edit', methods=['DELETE'])
@auth_required
@admin_check
@limiter.limit("20 per minute")
def delete_quiz(current_user, quiz_id):
    """Delete a quiz"""
    logger.info(f"Editting quiz attempt")
    quiz = Quiz.query.get_or_404(quiz_id)

    if quiz.created_by != current_user.id:
        return redirect(url_for('full_bp.user_dashboard'))
    try:
        db.session.delete(quiz)
        db.session.commit()
        return '', 204
    except Exception as e:
        logger.error(f"Error deleting quiz: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Error deleting quiz"
        }), 500


def update_quiz_public_status(current_user, quiz_id, status):
    """Helper function to update quiz public status"""
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.created_by != current_user.id:
        return {
            "success": False,
            "message": "Unauthorized"
        }, 403
    quiz.public = status
    db.session.commit()
    return {
        "success": True,
        "message": f"Quiz {'published' if status else 'unpublished'}"
    }, 200


@full_bp.route('/quiz/<quiz_id>/publish', methods=['POST'])
@auth_required
@admin_check
@limiter.limit("10 per minute")
def publish_quiz(current_user, quiz_id):
    """Make a quiz public"""
    try:
        response, status_code =\
            update_quiz_public_status(current_user, quiz_id, True)
        return jsonify(response), status_code
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error publishing quiz: {str(e)}")
        return jsonify({
            "success": False,
            "error": "An error occured"
        }), 500


@full_bp.route('/quiz/<quiz_id>/unpublish', methods=['POST'])
@auth_required
@admin_check
@limiter.limit("10 per minute")
def unpublish_quiz(current_user, quiz_id):
    """Make a quiz private"""
    try:
        response, status_code =\
            update_quiz_public_status(current_user, quiz_id, False)
        return jsonify(response), status_code
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error unpublishing quiz: {str(e)}")
        return jsonify({
            "success": False,
            "error": "An error occured"
        }), 500


@full_bp.route('/api/quiz/<quiz_code>', methods=['GET'])
@auth_required
@limiter.limit("10 per minute")
def check_quiz(current_user, quiz_code):
    """
    Check if the quiz exists and is public, and return the quiz id if valid.
    """
    quiz = Quiz.query.filter_by(id=quiz_code, public=True).first()

    if not quiz:
        return jsonify({
            "success": False,
            "message": "Quiz not found"
        }), 404

    return jsonify({
        "success": True,
        "quiz_id": quiz.id
    })


@full_bp.route('/quiz/<quiz_id>/start')
@auth_required
@limiter.limit("20 per minute")
def start_quiz(current_user, quiz_id):
    """
    Start a quiz: Fetch quiz details and initialize user session for the quiz.
    """
    logger.info(f"Stating quiz attempt")
    #quiz = Quiz.query.filter_by(id=quiz_id, public=True).first()
    quiz = Quiz.query.options(joinedload(Quiz.questions).joinedload(Question.answer_choices)) \
                     .filter_by(id=quiz_id, public=True).first()

    if not quiz:
        return jsonify({
            "success": False,
            "message": "Quiz not found or not public"
        }), 404

     # Prepare quiz data
    questions = [
        {
            "id": q.id,
            "question_text": q.question_text,
            "question_type": q.question_type,
            "is_multiple_response": q.is_multiple_response,
            "points": q.points,
            "answer_choices": [{"id": ac.id, "text": ac.text} for ac in q.answer_choices]
        }
        for q in quiz.questions
    ]

    return jsonify({
        "duration": quiz.duration,
        "questions": questions
    }), 200


@full_bp.route('/take/quiz/<quiz_id>/')
@auth_required
@limiter.limit("20 per minute")
def take_quiz(current_user, quiz_id):
    """
    Start a quiz: Fetch quiz details and initialize user session for the quiz.
    """
    logger.info(f"Stating quiz attempt")
    #quiz = Quiz.query.filter_by(id=quiz_id, public=True).first()
    quiz = Quiz.query.options(joinedload(Quiz.questions).joinedload(Question.answer_choices)) \
                     .filter_by(id=quiz_id, public=True).first()

    if not quiz:
        return render_template(
            'start_quiz_404.html',
            user_authenticated = 'user_id' in session
        ), 404

    questions = [
        {
            "id": q.id,
            "question_text": q.question_text,
            "question_type": q.question_type,
            "is_multiple_response": q.is_multiple_response,
            "points": q.points,
            "answer_choices": [{"id": ac.id, "text": ac.text} for ac in q.answer_choices]
        }
        for q in quiz.questions
    ]

    # Pass the quiz data to the template
    return render_template('start_quiz.html',
        quiz_id=quiz.id,
        title=quiz.title,
        description=quiz.description,
        duration=quiz.duration,
        quiz=quiz,
        questions_json=json.dumps(questions),
        questions=questions,
        user_authenticated = 'user_id' in session
    )


def evaluate_answer(question_id, quiz_id, user_answers):
    """
    Evaluates the user's answer(s) against the correct answer(s) in the database.

    Args:
        question_id (str): The ID of the question being answered.
        quiz_id (str): The ID of the quiz the question belongs to.
        user_answers (list): List of user-selected answers or the user-provided answer (for short answer).

    Returns:
        int: Points awarded for the correct answer, or 0 if incorrect.
    """
    question = Question.query.filter_by(id=question_id, quiz_id=quiz_id).first()
    if not question:
        raise ValueError(f"Question with ID {question_id} and Quiz ID {quiz_id} not found.")

    answer_choices = AnswerChoice.query.filter_by(question_id=question_id).all()
    if not answer_choices:
        raise ValueError(f"No answer choices found for Question ID {question_id}.")

    if question.question_type == 'multiple_choice':
        return evaluate_multiple_choice(question, answer_choices, user_answers)

    elif question.question_type == 'short_answer':
        return evaluate_short_answer(question, answer_choices, user_answers)

    else:
        raise ValueError(f"Unsupported question type: {question.question_type}")


def evaluate_multiple_choice(question, answer_choices, user_answers):
    """
    Evaluates answers for multiple-choice questions.

    Args:
        question (Question): The question being evaluated.
        answer_choices (list): List of AnswerChoice objects.
        user_answers (list): User's selected answers.

    Returns:
        int: Points awarded for the correct answer(s), or 0 if incorrect.
    """
    if question.is_multiple_response:
        correct_answers = {choice.text for choice in answer_choices if choice.is_correct}
        user_answers_set = set(user_answers)
        logger.info(f"Answer is {correct_answers}, user chose {user_answers_set}")
        return question.points if user_answers_set == correct_answers else 0
    else:
        correct_answer = next((choice.text for choice in answer_choices if choice.is_correct), None)
        logger.info(f"Answer is {correct_answer}, user chose {user_answers}")
        return question.points if correct_answer and user_answers == [correct_answer] else 0


def evaluate_short_answer(question, answer_choices, user_answers):
    """
    Evaluates answers for short-answer questions.

    Args:
        answer_choices (list): List of AnswerChoice objects.
        user_answers (list): User's provided answer (assumes single-answer input).

    Returns:
        int: Points awarded for the correct answer, or 0 if incorrect.
    """
    correct_answers = {choice.text.lower() for choice in answer_choices if choice.is_correct}
    user_answer = user_answers.strip().lower()
    logger.info(f"Answer is {correct_answers}, user chose {user_answer}")
    return question.points if user_answer in correct_answers else 0

@full_bp.route('/quiz/<quiz_id>/submit', methods=['POST'])
@auth_required
@limiter.limit("20 per minute")
def submit_quiz(current_user, quiz_id):
    """
    Submit the user's quiz answers and calculate their score.
    """
    logger.info(f"Submitting quiz attempt")
    data = request.json
    answers = data.get('answers', [])

    quiz = Quiz.query.filter_by(id=quiz_id).first()
    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404

    total_score = 0
    correct_count = 0
    for answer in answers:
        question_id = answer.get('question_id')
        user_answers = answer.get('user_answer')

        if not question_id or user_answers is None:
            continue

        question = Question.query.filter_by(id=question_id, quiz_id=quiz_id).first()
        if not question:
            continue

        try:
            points = evaluate_answer(question_id, quiz_id, user_answers)
            if points == question.points:
                correct_count += 1
            logger.info(f"Scored {points}, out of {question.points}")
            total_score += points
        except ValueError as e:
            continue


    quiz_history = QuizHistory(user_id=current_user.id, quiz_id=quiz_id, score=total_score)
    db.session.add(quiz_history)

    leaderboard_entry = Leaderboard.query.filter_by(user_id=current_user.id, quiz_id=quiz_id).first()
    if leaderboard_entry:
        leaderboard_entry.score = max(leaderboard_entry.score, total_score)  # Update with max score
    else:
        leaderboard_entry = Leaderboard(user_id=current_user.id, quiz_id=quiz_id, score=total_score, rank=0)
        db.session.add(leaderboard_entry)

    db.session.commit()

    pass_threshold = 0.5
    passed = (total_score / quiz.max_score) >= pass_threshold

    s = Serializer(current_app.config['SECRET_KEY'])
    data = {
        "score": total_score,
        "max_score": quiz.max_score,
        "total_questions": len(quiz.questions),
        "correct_count": correct_count,
        "wrong_count": len(quiz.questions) - correct_count,
        "passed": passed
    }
    result_token = s.dumps(data)
    return redirect(url_for('full_bp.show_quiz_result', quiz_id=quiz_id, result_token=result_token))

    # _external=True, _scheme='https'
    # return redirect(url_for(
    #     'full_bp.show_quiz_result',
    #     quiz_id=quiz_id,
    #     score=total_score,
    #     max_score=quiz.max_score,
    #     total_questions=len(quiz.questions),
    #     correct_count=correct_count,
    #     wrong_count=wrong_count,
    #     passed=passed
    # ))
    # return render_template(
    #     "quiz_result.html",
    #     score=total_score,
    #     max_score=quiz.max_score,
    #     total_questions=len(quiz.questions),
    #     correct_count=correct_count,
    #     wrong_count=wrong_count,
    #     passed=passed,
    #     quiz_title=quiz.title,
    #     user_authenticated = 'user_id' in session
    # )
    # return jsonify({
    #     "message": "Quiz submitted",
    #     "score": total_score,
    #     "max_score": quiz.max_score,
    #     "total_questions": len(quiz.questions),
    #     "correct_count": correct_count,
    #     "wrong_count": wrong_count
    # }), 200


@full_bp.route('/quiz/<quiz_id>/result', methods=['GET'])
@auth_required
@limiter.limit("20 per minute")
def show_quiz_result(current_user, quiz_id):
    """
    Display the results page for the quiz.
    """
    token = request.args.get('result_token')
    if not token:
        return abort(404)

    quiz = Quiz.query.filter_by(id=quiz_id, public=True).first()
    if not quiz:
        return abort(404)

    try:
        s = Serializer(current_app.config['SECRET_KEY'])
        data = s.loads(token)
    except Exception as e:
        logger.error(f"Token Expired")
        if (
            request.accept_mimetypes['application/json'] >=
            request.accept_mimetypes['text/html']
        ):
            return jsonify({
                "success": False,
                "message": "Expired token."
            }), 400
        else:
            return abort(404)
    return render_template(
        "quiz_result.html",
        score=data["score"],
        max_score=data["max_score"],
        total_questions=data["total_questions"],
        correct_count=data["correct_count"],
        wrong_count=data["wrong_count"],
        passed=data["passed"],
        quiz_id = quiz.id,
        quiz_title=quiz.title,
        user_authenticated='user_id' in session
    )
    # return render_template(
    #     "quiz_result.html",
    #     score=score,
    #     max_score=max_score,
    #     total_questions=total_questions,
    #     correct_count=correct_count,
    #     wrong_count=wrong_count,
    #     passed=passed,
    #     quiz_title=quiz.title,
    #     user_authenticated='user_id' in session
    # )

@full_bp.route('/quiz/<quiz_id>/question/new')
@auth_required
@admin_check
@limiter.limit("20 per minute")
def create_question(current_user, quiz_id):
    """Create a new question and redirect to edit page."""
    quiz = Quiz.query.get_or_404(quiz_id)

    if quiz.created_by != current_user.id:
        return redirect(url_for('full_bp.user_dashboard'))
    question_id = str(ulid.new()).lower()[:16]

    return redirect(
        url_for(
            'full_bp.get_question',
            quiz_id=quiz_id,
            question_id=question_id
        )
    )


question_route = '/quiz/<quiz_id>/question/<question_id>'


def update_answer_choices(question_id, options):
    """helper function to handle Answer Choices"""
    AnswerChoice.query.filter_by(question_id=question_id).delete()
    for option in options:
        answer_choice = AnswerChoice(
            question_id=question_id,
            text=option["text"],
            is_correct=option['isCorrect']
        )
        db.session.add(answer_choice)


def is_valid_id(identifier):
    """
    Validates that an identifier matches our scheme:
        str(ulid.new()).lower()[:16]

    Args:
        identifier (str): The identifier to validate.

    Returns:
        bool: True if valid, False otherwise.
    """
    # Check if the identifier is a 16-character lowercase alphanumeric string
    return bool(re.fullmatch(r'[a-z0-9]{16}', identifier))


@full_bp.route(f'{question_route}', methods=['GET'])
@full_bp.route(f'{question_route}/edit', methods=['GET'])
@auth_required
@admin_check
@limiter.limit("20 per minute")
def get_question(current_user, quiz_id, question_id):
    """Get a question"""
    try:
        quiz = Quiz.query.get_or_404(quiz_id)
        if quiz.created_by != current_user.id:
            logger.error("User is not authorized to edit this quiz.")
            return redirect(url_for('full_bp.user_dashboard'))

        query = Question.query.filter_by(id=question_id, quiz_id=quiz_id)
        question = query.first()

        if not question:
            if not is_valid_id(question_id):
                return redirect(url_for('full_bp.user_dashboard'))
                # return jsonify({
                #     "success": False,
                #     "message": "Question not found"
                # }), 404
            return render_template(
                'edit_question.html',
                quiz=quiz,
                user_authenticated = 'user_id' in session
            )

        return render_template(
            'edit_question.html',
            quiz=quiz,
            question=question,
            user_authenticated = 'user_id' in session
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error getting question: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Error getting question"
        }), 500


@full_bp.route(f'{question_route}', methods=['POST'])
@full_bp.route(f'{question_route}/edit', methods=['POST'])
@auth_required
@admin_check
@limiter.limit("20 per minute")
def save_question(current_user, quiz_id, question_id):
    """Save a question"""
    try:
        quiz = Quiz.query.get_or_404(quiz_id)

        if quiz.created_by != current_user.id:
            logger.error("User is not authorized to edit this quiz.")
            return redirect(url_for('full_bp.user_dashboard'))

        query = Question.query.filter_by(id=question_id, quiz_id=quiz_id)
        question = query.first()

        try:
            data = request.get_json() if request.is_json else request.form
        except Exception as parse_error:
            return jsonify({
                "success": False,
                "error": "Failed to parse data",
                "details": str(parse_error)
            }), 400

        if not data:
            return jsonify({
                "success": False,
                "error": "Invalid input",
                "message": "Request body is missing or malformed"
            }), 400

        required_f = ['question', 'questionType', 'options']
        missing_fields = [field for field in required_f if field not in data]

        if missing_fields:
            x_fields = ', '.join(missing_fields)
            return jsonify({
                "success": False,
                "error": "Invalid question data",
                "message": f"Missing required fields: {x_fields}"
            }), 400

        question_text = data.get('question').strip()
        question_type = data.get('questionType').strip()
        is_multiple_response = data.get('isMultipleResponse', False)
        options = data.get('options')

        points = data.get('points', '1')
        if not points or not isinstance(points, int) or int(points) <= 0:
            return jsonify({
                'success': False,
                'message': 'Points must be a positive integer'
            }), 400

        question = Question(
            id=question_id,
            quiz_id=quiz_id,
            question_text=question_text,
            question_type=question_type,
            is_multiple_response=is_multiple_response,
            points=points,
        )
        db.session.add(question)

        update_answer_choices(question.id, options)
        quiz.calculate_max_score()
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Question saved successfully",
            "redirect_url": url_for('full_bp.get_quiz', quiz_id=quiz_id)
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error during question creation: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Error saving question",
        }), 500


@full_bp.route(f'{question_route}', methods=['PUT'])
@full_bp.route(f'{question_route}/edit', methods=['PUT'])
@auth_required
@admin_check
@limiter.limit("20 per minute")
def update_question(current_user, quiz_id, question_id):
    """Update a question"""
    try:
        quiz = Quiz.query.get_or_404(quiz_id)

        if quiz.created_by != current_user.id:
            logger.error("User is not authorized to edit this quiz.")
            return redirect(url_for('full_bp.user_dashboard'))

        query = Question.query.filter_by(id=question_id, quiz_id=quiz_id)
        question = query.first()

        if not question:
            return jsonify({
                "success": False,
                "message": "Question not found"
            }), 404

        try:
            data = request.get_json() if request.is_json else request.form
        except Exception as parse_error:
            return jsonify({
                "success": False,
                "error": "Failed to parse data",
                "details": str(parse_error)
            }), 400

        if not data:
            return jsonify({
                "success": False,
                "error": "Invalid input",
                "message": "Request body is missing or malformed"
            }), 400

        if 'question' in data:
            question.question_text = data['question']

        if 'questionType' in data:
            question.question_type = data['questionType']

        if 'points' in data:
            try:
                question.points = int(data['points'])
                if question.points <= 0:
                    raise ValueError("Points must be a positive integer")
            except ValueError as ve:
                return jsonify({
                    "success": False,
                    "error": "Invalid input",
                    "message": "Points must be a positive integer"
                }), 400

        if 'isMultipleResponse' in data:
            if not isinstance(data['isMultipleResponse'], bool):
                return jsonify({
                    "success": False,
                    "error": "Invalid input",
                    "message": "isMultipleResponse must be a boolean"
                }), 400
            question.is_multiple_response = data['isMultipleResponse']

        if 'options' in data:
            options = data.get('options')
            update_answer_choices(question.id, options)

        quiz.calculate_max_score()
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Quiz updated successfully",
            "redirect_url": url_for('full_bp.get_quiz', quiz_id=quiz_id)
        }), 201
    except Exception as e:
        logger.error(f"Error editing question: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Error editing question"
        })


@full_bp.route(f'{question_route}', methods=['DELETE'])
@full_bp.route(f'{question_route}/edit', methods=['DELETE'])
@auth_required
@admin_check
@limiter.limit("20 per minute")
def delete_question(current_user, quiz_id, question_id):
    """Delete a question"""
    try:
        quiz = Quiz.query.get_or_404(quiz_id)
        if quiz.created_by != current_user.id:
            logger.error("User is not authorized to edit this quiz.")
            return redirect(url_for('full_bp.user_dashboard'))

        query = Question.query.filter_by(id=question_id, quiz_id=quiz_id)
        question = query.first()

        if not question:
            return jsonify({
                "success": False,
                "message": "Question not found"
            }), 404

        db.session.delete(question)
        quiz.calculate_max_score()
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting question: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Error deleting question"
        }), 500


@full_bp.route('/library')
@auth_required
@admin_check
@limiter.limit("30 per minute")
def admin_library(current_user):
    """Admin-specific library"""
    logger.debug(f"{request.method} - Library")
    user = User.query.get(current_user.id)
    if not user:
        return redirect(url_for('full_bp.login'))

    query = Quiz.query.filter_by(created_by=user.id)
    quizzes = query.order_by(Quiz.created_at.desc()).all()
    categories = Category.query.order_by(Category.name.asc()).all()

    return render_template(
        'admin_library.html',
        title='My Library',
        user=user,
        quizzes=quizzes,
        categories=categories,
        user_authenticated = 'user_id' in session
    )


@full_bp.route('/profile')
@auth_required
@limiter.limit("30 per minute")
def profile(current_user):
    """Profile for all users"""
    logger.debug(f"{request.method} - Profile")

    if current_user.role == "admin":
        base_template = "base_admin_dashboard.html"

    else:
        base_template = "base_user_dashboard.html"

    categories = Category.query.order_by(Category.name.asc()).all()

    return render_template(
        'profile.html',
        base_template=base_template,
        title='My Profile',
        user=current_user,
        categories=categories,
        user_authenticated = 'user_id' in session
    )


@full_bp.route('/upload-profile-picture', methods=['POST'])
@auth_required
@limiter.limit("10 per minute")
def upload_profile_picture(current_user):
    try:
        if 'profile_picture' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No file part'
            })

        file = request.files['profile_picture']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No selected file'
            })

        if file:
            original_filename = secure_filename(file.filename)
            file_extension = os.path.splitext(original_filename)[1]
            unique_filename = f"{str(ulid.new()).lower()}{file_extension}"

            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)

            if current_user.profile_picture:
                old_image = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(current_user.profile_picture))
                if os.path.exists(old_image):
                    os.remove(old_image)

            current_user.profile_picture = f"/quizzen/uploads/{unique_filename}"
            db.session.commit()

            return jsonify({
                'success': True,
                'image_url': f"uploads/{unique_filename}"
            })

        return jsonify({
            'success': False,
            'message': 'File upload failed'
        })
    except Exception as e:
        logger.error(f"Error uploading ppf: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'File upload failed'
        })


@full_bp.route('/delete-profile-picture', methods=['POST'])
@auth_required
@limiter.limit("5 per minute")
def delete_profile_picture(current_user):
    try:
        if current_user.profile_picture:
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(current_user.profile_picture))
            if os.path.exists(image_path):
                os.remove(image_path)
            current_user.profile_picture = None

            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Image deleted successfully'
            })

        return jsonify({
            'success': False,
            'message': 'No image to delete'
        })
    except Exception as e:
        logger.error(f"Error deleting ppf: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'No image to delete'
        })

@full_bp.route('/admin/uploads/<filename>')
@full_bp.route('/uploads/<filename>')
@limiter.limit("30 per minute")
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)


@full_bp.route("/update-profile", methods=["POST"])
@auth_required
@limiter.limit("10 per minute")
def update_profile(current_user):
    try:
        data = request.json

        current_user.username = data.get("username", current_user.username).strip()
        current_user.first_name = data.get("first_name", current_user.first_name).strip()
        current_user.last_name = data.get("last_name", current_user.last_name).strip()

        db.session.add(current_user)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Profile updated successfully!"
        }), 200
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Server error",
        }), 500


@full_bp.route("/change-password", methods=["POST"])
@auth_required
@limiter.limit("10 per minute")
def change_password(current_user):
    try:
        data = request.json

        current_password = data.get("current_password")
        new_password = data.get("new_password")

        if current_user.has_password:
            logger.info(f"Changing password for user {current_user.id}")
            if current_user.check_password(current_password):
                current_user.set_password(new_password)
                db.session.add(current_user)
                db.session.commit()

                logger.info(f"Password for user {current_user.id} changed successfully")
                return jsonify({
                    "success": True,
                    "message": "Password changed successfully"
                }), 200

            return jsonify({
                "success": False,
                "message": "Invalid Credentials"
            }), 401
        else:
            current_user.set_password(new_password)
            db.session.add(current_user)
            db.session.commit()
            logger.warning(f"User with email {current_user.email} is an OAuth user")
            return jsonify({
                "success": "True",
                "message": "Successful"
            }), 400

    except Exception as e:
        logger.error(f"Error during password change: {e}")
        return jsonify({
            "success": False,
            "message": "Server error",
        }), 500


@full_bp.route("/check-username")
@limiter.limit("10 per minute")
def check_username():
    try:
        username = request.args.get("username", "").strip()
        if not username:
            return jsonify({"message": "Username is required"}), 400

        if User.query.filter_by(username=username).first():
            logger.error(f"Username '{username}' already exists")
            suggestions = []
            while len(suggestions) < 3:
                random_suffix = random.randint(1, 9999)
                suggestion = f"{username}-{random_suffix}"
                if not User.query.filter_by(username=suggestion).first():
                    suggestions.append(suggestion)
            return jsonify({
                "success": False,
                "suggestions": suggestions
            }), 200

        return jsonify({"success": True}), 200

    except Exception as e:
        logger.error(f"Error during check_username: {e}")
        return jsonify({
            "success": False,
            "message": "Server error",
        }), 500



# Form validation
class ContactForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50), validators.DataRequired()])
    email = StringField('Email', [validators.Email(), validators.Length(min=3, max=50), validators.DataRequired()])
    subject = StringField('Subject', [validators.Length(min=1, max=100), validators.DataRequired()])
    message = TextAreaField('Message', [validators.Length(min=1), validators.DataRequired()])


@full_bp.route("/contact", methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def contact():
    try:
        if request.method == 'GET':
            return render_template(
                'index.html',
                scroll_to_contact=True,
                user_authenticated = 'user_id' in session
            )

        form = ContactForm()

        if request.method == 'POST':
            form = ContactForm(request.form)
            scroll = True
            if form.validate():
                name = form.name.data
                email = form.email.data
                subject = form.subject.data
                message = form.message.data

                success, error_message = send_email(subject, message, name, email)
                if success:
                    scroll = False
                    flash(('Your message has been sent successfully.', 'success'))
                else:
                    flash((f'Failed to send email: {error_message}', 'error'))
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        flash((f"Error in {field}: {error}", 'error'))
        return render_template(
            'index.html',
            scroll_to_contact=scroll,
            user_authenticated = 'user_id' in session
        )
    except Exception as e:
        logger.error(f"Email not delivered {str(e)}")
        flash((f'Failed to send email: {e}', 'error'))
        return render_template(
            'index.html',
            scroll_to_contact=True,
            user_authenticated = 'user_id' in session
        )

def send_email(subject, message, user_name, user_email):
    """
    Sends an email using SMTP protocol with error handling.

    Args:
        subject (str): The subject of the email.
        message (str): The body content of the email.
        user_name (str): The user's name captured from the form.
        user_email (str): The user's email address captured from the form.

    Returns:
        bool: True if email sent successfully, False otherwise.
    """

    smtp_server = os.getenv('MAIL_SERVER', "out.dnsexit.com")
    port = int(os.getenv('MAIL_PORT', 587))
    sender_email = os.getenv('MAIL_DEFAULT_SENDER')
    sender_password = os.getenv('MAIL_PASSWORD')
    receiver_email = os.getenv('RECEIVER_EMAIL')

    if not (sender_email and sender_password and receiver_email):
        raise ValueError("Email credentials are not set in environment variables")

    email_content = f"Subject: {subject}\n\nFrom: {user_name} <{user_email}>\n\nMessage: {message}"

    try:
        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, email_content.encode('utf-8'))
            logger.info("Email delivered")
        return True, None
    except Exception as e:
        logger.error(f"Email not delivered {str(e)}")
        return False, str(e)

