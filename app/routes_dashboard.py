"""
    Defined routes:
      -
"""
from app.extensions import db
from app.models import User, QuizHistory, Leaderboard, Notification
from app.routes import (
    auth_required, full_bp
)


@full_bp.route('/dashboard')
@auth_required
def dashboard(current_user):
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
