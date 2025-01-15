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
from flask import Flask
from flask_login import LoginManager

from app import routes_dashboard, oauth
from app.api import v1
from app.extensions import (
    bcrypt, db, jwt,
    limiter, mail, migrate,
    session, timeago_filter
)
from app.extensions import api_v1, full_bp
from config import config


def create_app(config_name=None):
    """Factory function to create and configure the Flask application."""
    app = Flask(__name__, static_folder='static',
                static_url_path='/quizzen/assets',
                template_folder='templates')
    app.url_map.strict_slashes = False
    app.jinja_env.globals.update(len=len)
    app.jinja_env.filters['timeago'] = timeago_filter

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
    # oauth.init_app(app)

    app.register_blueprint(full_bp)
    app.register_blueprint(api_v1)

    return app
