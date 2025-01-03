"""
    Defined routes:
      -
"""
from app.extensions import db, limiter
from app.models import (
    AnswerChoice, Category, Leaderboard, Notification,
    Question, Quiz, QuizHistory, User
)
from app.routes import (
    auth_required, full_bp, logger
)
from flask import (
    current_app, flash, jsonify,
    redirect, render_template, request,
    session, url_for
)


@full_bp.route('/dashboard')
@auth_required
def dashboard(current_user):
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

    return render_template(
        'dashboard.html',
        title='Dashboard',
        user=user,
        quizzes=quizzes,
        leaderboard=leaderboard,
        notifications=notifications
    )


@full_bp.route('/create_quiz')
@auth_required
def create_quiz(current_user):
    """Creates a new quiz"""
    limiter.limit("5 per minute")(lambda: None)()
    logger.debug(f"{request.method} - Create quiz attempt")
    try:
        new_quiz = Quiz(
            title="Untitled Quiz",
            created_by=current_user.id,
            duration=30
        )

        db.session.add(new_quiz)
        db.session.commit()

        new_question = Question(
            quiz_id=new_quiz.id,
            question_text="",
            question_type="multiple_choice",
            points=1
        )   

        db.session.add(new_question)
        db.session.commit()     

        return redirect(
            url_for(
                'full_bp.edit_question',
                quiz_id=new_quiz.id,
                question_id=new_question.id
            )
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error during quiz creation: {str(e)}")
        flash("An error occurred while creating the quiz. Please try again.", "error")
        return redirect(url_for('full_bp.dashboard'))

    # categories = Category.query.order_by(Category.name.asc()).all()
    # return render_template('create_quiz.html', categories=categories)



@full_bp.route('/quiz/<quiz_id>/question/<question_id>/edit', methods=['GET', 'POST'])
@auth_required
def edit_question(current_user, quiz_id, question_id):
    """Edit a question"""
    quiz = Quiz.query.get_or_404(quiz_id)
    question = Question.query.get_or_404(question_id)
    question.answer_choices = AnswerChoice.query.filter_by(question_id=question.id).all()

    logger.info(f"This is Question: {str(question)} and answer {question.answer_choices}")
    # Ensure the user is authorized to edit
    if quiz.created_by != current_user.id:
        flash("Unauthorized access.", "danger")
        logger.error("No owner")
        return redirect(url_for('full_bp.dashboard'))

    if request.method == 'POST':
        
        try:
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form

            question_text = data.get('question', '').strip()
            question_type = data.get('questionType', '').strip()
            is_multiple_response = data.get('multipleResponse', 'False')
            options = data['options']
            points = int(data['points'])

        except Exception as e:
            logger.error(f"Invalid form data: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Invalid form data",
                "error": str(e)
            })

        try:
            question.question_text = question_text
            question.question_type = question_type
            question.is_multiple_response = is_multiple_response
            question.points = points
            AnswerChoice.query.filter_by(question_id=question.id).delete()
            for option in options:
                answer_choice = AnswerChoice(
                    question_id=question.id,
                    text=option["text"],
                    is_correct=option['isCorrect'],
                )
                db.session.add(answer_choice)
            quiz.calculate_max_score()
            logger.info(f"Saved Options Successfully")
            db.session.commit()
            
            logger.info(f"Quiz max point now:---> {quiz.max_score}")

            db.session.commit()
        
        
            return redirect(url_for('full_bp.edit_quiz', quiz_id=quiz_id))
        except Exception as e:
            logger.error(f"Error editing question: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error editing question",
                "error": str(e)
            })

    return render_template('edit_question.html', quiz=quiz, question=question)


@full_bp.route('/quiz/<quiz_id>/edit', methods= ['GET', 'POST'])
@auth_required
def edit_quiz(current_user, quiz_id):
    logger.info(f"Editting quiz attempt")
    quiz = Quiz.query.get_or_404(quiz_id)

    if quiz.created_by != current_user.id:
        flash("You are not authorized to edit this quiz", "error")
        return redirect(url_for('full_bp.dashboard'))

    logger.info(f"Editting quiz: {quiz.id}")
    if request.method == 'POST':
        try:
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form
            
            question_text = data.get('question', '').strip()
            answer_choices = data.getlist('answer_choices', '') 
            question_type = data.get('question_type', '').strip()
            points = int(data.get('points', '0').strip())

            if question_type == 'multiple_choice' and len(answer_choices) < 2:
                flash('Multiple choice questions must have at least two options.', 
                    'danger')
                return redirect(url_for('full_bp.edit_quiz', quiz_id=quiz_id))

            new_question = Question(
                quiz_id = quiz_id,
                question_text = question_text,
                answer_choices = answer_choices,
                question_type = question_type 
            )

            db.session.add(new_question)
            quiz.calculate_max_score()
            db.session.commit()
            flash('Question added successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error adding question. Please try again.', 'danger')

    print(quiz.questions)
    for x in quiz.questions:
        print(x.answer_choices)

    return render_template('edit_quiz.html', quiz=quiz, title=quiz.title)

    
@full_bp.route('/quiz/<quiz_id>/question/new', methods=['GET', 'POST'])
@auth_required
def create_question(current_user, quiz_id):
    """Create a new question and redirect to edit page."""
    quiz = Quiz.query.get_or_404(quiz_id)

    if quiz.created_by != current_user.id:
        flash("Unauthorized access", "error")
        return redirect(url_for('full_bp.dashboard'))

    new_question = Question(
        quiz_id=quiz_id,
        question_text="",
        answer_choices={},
        question_type="multiple_choice"
    )

    db.session.add(new_question)
    db.session.commit()

    return redirect(
        url_for(
            'full_bp.edit_question', 
            quiz_id=quiz_id,
            question_id=new_question.id
        )
    )

