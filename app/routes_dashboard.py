"""
    Defined routes:
      -
"""
from app.extensions import db
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

    # if request.method == 'POST':
    #     limiter.limit("5 per minute")(lambda: None)()
    #     try:
    #         if request.is_json:
    #             data = request.get_json()
    #         else:
    #             data = request.form

    #         title = data.get('title', '').strip()
    #         duration = int(data.get('duration', '0'))
    #         description = data.get('description', '')
    #         category_id = data.get('category') 
    #         category = Category.query.get(category_id)

    #         if not all([title, duration]):
    #             flash("All fields are required!", "error")
    #             return redirect(url_for('full_bp.create_quiz'))

    #     except Exception as e:
    #         logger.error(f"Error during quiz creation: {e}")
    #         return jsonify({
    #             "success": False,
    #             "message": "Form data not valid",
    #             "error": str(e)
    #         }), 400
            

    # categories = Category.query.order_by(Category.name.asc()).all()
    # return render_template('create_quiz.html', categories=categories)



@full_bp.route('/quiz/<quiz_id>/question/<question_id>/edit', methods=['GET', 'POST'])
@auth_required
def edit_question(current_user, quiz_id, question_id):
    """Edit a question"""
    print(f'{request.method} - {request}')
    quiz = Quiz.query.get_or_404(quiz_id)
    question = Question.query.get_or_404(question_id)

    # Ensure the user is authorized to edit
    if quiz.created_by != current_user.id:
        flash("Unauthorized access.", "danger")
        logger.error("No owner")
        return redirect(url_for('full_bp.dashboard'))

    if request.method == 'POST':
        data = request.get_json()

        question_text = data.get('question')
        question_type = data.get('question_type')
        multiple_response = data.get('multipleResponse')
        options = data['options']
        points = int(data['points'])

        question.question_text = question_text
        question.question_type = question_type
        question.is_multiple_response = multiple_response
        question.points = points


        for option in options:
            answer_choice = AnswerChoice(
                text=option['text'],
                is_correct=option['isCorrect'],
                question_id=question.id
            )
            db.session.add(answer_choice)

        db.session.commit()
        
        quiz.calculate_max_score()
        db.session.commit()
        
        return redirect(url_for('full_bp.edit_quiz', quiz_id=quiz_id))

    return render_template('edit_question.html', quiz=quiz, question=question)




@full_bp.route('/quiz/<quiz_id>/edit', methods= ['GET', 'POST'])
@auth_required
def edit_quiz(current_user, quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)

    if quiz.created_by != current_user.id:
        flash("You are not authorized to edit this quiz", "error")
        return redirect(url_for('full_bp.dashboard'))

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

    return render_template('edit_quiz.html', quiz=quiz)

    
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

