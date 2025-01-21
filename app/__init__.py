"""
This is the initialization module for the Quizzen Flask application.

The module sets up the Flask app instance, configures application settings,
and initializes essential extensions, including SQLAlchemy, Flask-Login,
Flask-Bcrypt and Flask-Session. It also registers blueprints for routing.

Key Features:
- Configuration of PostgreSQL as the database backend.
- Integration with Redis for session management.
- Custom application root and static file handling.
- Centralized initialization of extensions and blueprints.

Note:
Sensitive values such as secret keys and database credentials are managed
through environment variables for security.
"""

import os
from flask import Flask, render_template, request
from flask_login import LoginManager

from app import routes_dashboard, oauth
from app.api import v1
from app.extensions import (
    bcrypt, db, jwt,
    limiter, mail, migrate,
    session, timeago_filter
)
from app.extensions import api_v1, full_bp, oauth_bp
from config import config


def create_app(config_name=None):
    """Factory function to create and configure the Flask application."""
    app = Flask(__name__, static_folder='static',
                static_url_path='/quizzen/assets',
                template_folder='templates')
    app.url_map.strict_slashes = False
    app.jinja_env.globals.update(len=len)
    app.jinja_env.filters['timeago'] = timeago_filter

    @app.errorhandler(404)
    def page_not_found(e):
        requested_path = request.path.split('/quizzen', 1)[-1]
        return render_template('404.html', requested_url=requested_path), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        requested_path = request.path.split('/quizzen', 1)[-1]
        return render_template('405.html', method=request.method, requested_url=requested_path), 405

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500


    config_name = config_name or os.getenv('FLASK_ENV', 'default')
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    session.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    limiter.init_app(app)
    jwt.init_app(app)

    app.register_blueprint(full_bp)
    app.register_blueprint(api_v1)
    app.register_blueprint(oauth_bp)

    return app
