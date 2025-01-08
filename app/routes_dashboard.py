"""
    Defined routes:
      - '/dashboard' -> dashboard
      - '/quiz/new' -> create_quiz
      - '/quiz/<quiz_id>/edit' -> edit_quiz
      - '/quiz/<quiz_id>/question/new' -> create_question
      - '/quiz/<quiz_id>/question/<question_id>/edit' -> edit_question
"""

import ulid
from app.extensions import db, limiter
from app.models import (
    AnswerChoice, Category, Leaderboard, Notification,
    Question, Quiz, QuizHistory, User
)
from app.routes import (
    full_bp, logger, rate_limit_exceeded
)
from flask import (
    current_app, flash, jsonify,
    redirect, render_template, request,
    session, url_for
)
from flask_limiter.errors import RateLimitExceeded
from functools import wraps


def auth_required(f):
    """Auth required function"""
    @wraps(f)
    def decorated(*args, **kwargs):
        """Auth required decorator"""
        logger.info(f"Auth Attempt")
        if 'user_id' not in session:
            logger.error(f"Session token missing")
            flash("log in", "error")
            return redirect(url_for('full_bp.login'))

        try:
            user_id = session['user_id']
            current_user = User.query.get(user_id)

            if not current_user:
                logger.error("Invalid Token")
                flash("log in", "error")
                return redirect(url_for('full_bp.login'))

        except Exception as e:
            logger.error(f"Invalid Token, Error: {str(e)}")
            flash("log in", "error")
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
            flash("log in", "error")
            return redirect(url_for('full_bp.login'))
        try:
            if session['user_role'] != 'admin':
                return redirect(url_for('full_bp.dashboard'))        
        except Exception as e:
            logger.error(f"Invalid Token, Error: {str(e)}")
            flash("log in", "error")
            return redirect(url_for('full_bp.login'))
        return f(*args, **kwargs)
    return decorated


@full_bp.errorhandler(RateLimitExceeded)
def handle_rate_limit_exceeded(e):
    return rate_limit_exceeded(e)


@full_bp.route('/dashboard')
@auth_required
def user_dashboard(current_user):
    if current_user.role == 'admin':
        return redirect(url_for('full_bp.admin_dashboard'))
    return render_template('user_dashboard.html', user=current_user)



@full_bp.route('/admin/dashboard')
@auth_required
@admin_check
def admin_dashboard(current_user):
    """Admin-specific dashboard."""
    logger.debug(f"{request.method} - Dashboard")
    user = User.query.get(current_user.id)
    if not user:
        return redirect(url_for('full_bp.login'))

    quizzes = QuizHistory.query.filter_by(user_id=user.id).all()
    leaderboard = Leaderboard.query.order_by(
        Leaderboard.score.desc()
    ).limit(10).all()
    notifications = Notification.query.filter_by(
        user_id=user.id
    ).order_by(
        Notification.date_sent.desc()
    ).all()
    categories = Category.query.order_by(Category.name.asc()).all()

    return render_template(
        'dashboard_admin.html',
        title='Dashboard',
        user=user,
        quizzes=quizzes,
        categories=categories,
        leaderboard=leaderboard,
        notifications=notifications
    )


@full_bp.route('/quiz/new', methods=['POST'])
@auth_required
@admin_check
@limiter.limit("5 per minute")
def create_quiz(current_user):
    """Creates a new quiz"""
    try:
        logger.debug(f"{request.method} - Create quiz attempt")

        data = request.get_json() if request.is_json else request.form
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        category_id = data.get('category')
        duration = data.get('duration', 0)
        
        if not title:
            return jsonify({'success': False, 'message': 'Title is required.'}), 400
        if not category_id:
            return jsonify({'success': False, 'message': 'Category is required.'}), 400
        if not duration or int(duration) <= 0:
            return jsonify({'success': False, 'message': 'Invalid duration.'}), 400

       
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

        return jsonify({'success': True, 'redirect_url': url_for('full_bp.edit_question', quiz_id=quiz.id, question_id=question_id)})

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error during quiz creation: {str(e)}")
        return jsonify({'success': False, 'message': "An error occurred while creating the quiz. Please try again",
        "error": str(e)})
        flash(".", "error")
        return redirect(url_for('full_bp.admin_dashboard'))



@full_bp.route('/quiz/<quiz_id>', methods= ['GET', 'POST', 'PUT', 'DELETE'])
@full_bp.route('/quiz/<quiz_id>/edit', methods= ['GET', 'POST', 'PUT', 'DELETE'])
@auth_required
@admin_check
def edit_quiz(current_user, quiz_id):
    logger.info(f"Editting quiz attempt")
    quiz = Quiz.query.get_or_404(quiz_id)

    if quiz.created_by != current_user.id:
        # return jsonify({"success": False, "message": "Unauthorized to edit this quiz"}), 403
        flash("You are not authorized to edit this quiz", "error")
        return redirect(url_for('full_bp.dashboard'))

    logger.info(f"Editting quiz: {quiz.id}")
    if request.method == 'POST': # Adding a question
        try:
            limiter.limit("20 per minute")(lambda: None)()
            data = request.get_json() if request.is_json else request.form
            
            question_text = data.get('question', '').strip()
            question_type = data.get('question_type', '').strip()
            points = int(data.get('points', '0').strip())
            answer_choices = data.getlist('answer_choices', '') 

            if not all([question_text, question_type]):
                return jsonify({"success": False, "message": "Invalid question details."}), 400
            if question_type == 'multiple_choice' and len(answer_choices) < 2:
                return jsonify({"success": False, "message": "Multiple choice questions need at least two options."}), 400

            new_question = Question(
                quiz_id = quiz_id,
                question_text = question_text,
                question_type = question_type,
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
            return jsonify({"success": True, "message": "Question added successfully."}), 201
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during question addition: {str(e)}")
            return jsonify({"success": False, "message": "Error adding question.", "error": str(e)}), 500

    elif request.method == "PUT":
        try:
            limiter.limit("10 per minute")(lambda: None)()
            data = request.get_json() if request.is_json else request.form
            
            quiz.title = data.get("title", quiz.title) 
            quiz.description = data.get("description", quiz.description) 
            quiz.category_id = data.get("category", quiz.category_id) 
            quiz.duration = int(data.get("duration", quiz.duration)) 
            quiz.public = data.get("public", quiz.public)
    
            quiz.calculate_max_score()
            db.session.commit()

            return jsonify({"success": True, "message": "Quiz updated successfully."}), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating quiz: {str(e)}")
        
            return jsonify({
                "success": False,
                "message": "Error updating quiz",
                "error": str(e)
            }), 500

    elif request.method == "DELETE":
        try:
            db.session.delete(quiz)
            db.session.commit()
            return jsonify({"success": True, "message": "Quiz deleted successfully."}), 200 
        except Exception as e:
            logger.error(f"Error deleting quiz: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error deleting quiz",
                "error": str(e)
            }), 500

    return render_template('edit_quiz.html', quiz=quiz, title=f"Quiz: {quiz.title}")



@full_bp.route('/quiz/<quiz_id>/question/new')
@auth_required
@admin_check
def create_question(current_user, quiz_id):
    """Create a new question and redirect to edit page."""
    quiz = Quiz.query.get_or_404(quiz_id)

    if quiz.created_by != current_user.id:
        flash("Unauthorized access", "error")
        return redirect(url_for('full_bp.dashboard'))

    # OLD LOGIC
    # 
    # new_question = Question(
    #     quiz_id=quiz_id,
    #     question_text=""
    # )

    # db.session.add(new_question)
    # db.session.commit()

    # return redirect(
    #     url_for(
    #         'full_bp.edit_question', 
    #         quiz_id=quiz_id,
    #         question_id=new_question.id
    #     )
    # )

    # new logic

    question_id = str(ulid.new()).lower()[:16]

    return redirect(
        url_for(
            'full_bp.edit_question', 
            quiz_id=quiz_id,
            question_id=question_id
        )
    )

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

@full_bp.route('/quiz/<quiz_id>/question/<question_id>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@full_bp.route('/quiz/<quiz_id>/question/<question_id>/edit', methods=['GET', 'POST', 'PUT', 'DELETE'])
@auth_required
@admin_check
def edit_question(current_user, quiz_id, question_id):
    """Edit & manage a question"""
    limiter.limit("20 per minute")(lambda: None)()
    quiz = Quiz.query.get_or_404(quiz_id)

    # question.answer_choices = AnswerChoice.query.filter_by(question_id=question.id).all()

    # Ensure the user is authorized to edit
    if quiz.created_by != current_user.id:
        logger.error("User is not authorized to edit this quiz.")
        return redirect(url_for('full_bp.dashboard'))

    question = Question.query.filter_by(id=question_id, quiz_id=quiz_id).first()

    if request.method == 'POST':
        try:
            data = request.get_json() if request.is_json else request.form
            if not data:
                return jsonify({"message": "Invalid data format"}), 400

            question_text = data.get('question', '').strip()
            question_type = data.get('questionType', 'multiple_choice').strip()
            is_multiple_response = data.get('isMultipleResponse', False)
            points = int(data.get('points', 1))
            options = data.get('options', [])

            if not all([question_text, question_type, options]):
                return jsonify({"message": "Missing required fields"}), 400

            if not question:
                question = Question(
                    id = question_id,
                    quiz_id=quiz_id,
                    question_text = question_text,
                    question_type = question_type,
                    is_multiple_response = is_multiple_response,
                    points = points,
                )    
                db.session.add(question)
            else:
                question.question_text = question_text
                question.question_type = question_type
                question.is_multiple_response = is_multiple_response
                question.points = points
                
            update_answer_choices(question.id, options)
            quiz.calculate_max_score()
            db.session.commit()
            return jsonify(
                {"success": True, 
                "message": "Question saved successfully.",
                "redirect_url": url_for('full_bp.edit_quiz', quiz_id=quiz_id)}
            ), 201

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during question creation: {str(e)}")
            return jsonify({"success": False, "message": "Error saving question.", "error": str(e)}), 500
                 
    elif request.method == 'PUT':
        try:
            data = request.get_json() if request.is_json else request.form
            if not data:
                return jsonify({"message": "Invalid JSON data"}), 400

            question.question_text = data.get('question', question.question_text).strip()
            question.question_type = data.get('questionType', question.question_type).strip()
            question.is_multiple_response = data.get('isMultipleResponse', question.is_multiple_response)
            question.points = int(data.get('points', question.points))
            options = data.get('options', [])
            
            update_answer_choices(question.id, options)
            quiz.calculate_max_score()
            db.session.commit()
            return jsonify(
                {"success": True, 
                "message": "Question updated successfully.",
                "redirect_url": url_for('full_bp.edit_quiz', quiz_id=quiz_id)}
            ), 200

        except Exception as e:
            logger.error(f"Error editing question: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error editing question",
                "error": str(e)
            })

    elif request.method == 'DELETE':
        try:            
            if not question:
                    return jsonify({"success": False, "message": "Question not found."}), 404

            db.session.delete(question)
            quiz.calculate_max_score()
            db.session.commit()
            return jsonify(
                {"success": True, 
                "message": "Question deleted successfully",
                "redirect_url": url_for('full_bp.edit_quiz', quiz_id=quiz_id)}
            ), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting question: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error deleting question",
                "error": str(e)
            }), 500

    
    return render_template('edit_question.html', quiz=quiz, question=question)