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

Modules Imported:
- `os`, `secrets`: For environment variables and secure random key generation.
- `redis`: For managing session storage via a Redis backend.
- `datetime.timedelta`: For setting session expiration times.
- `flask.Flask`: To create the core Flask application instance.
- `flask_login.LoginManager`: To manage user authentication & session handling.
- `app.routes.full_bp`: The main application blueprint for routing.
- `app.extensions`: Custom application extensions for database (`db`),
  password hashing (`bcrypt`), session management (`session`),
  migration Object (`migrate`), mail Object (`mail`), rate limiter (`limiter`)

Note:
Sensitive values such as secret keys and database credentials are managed
through environment variables for security.
"""

import os
from flask import Flask
from flask_login import LoginManager
from app.extensions import db, bcrypt, session, migrate, mail, limiter
from app.routes import full_bp, logger
from config import config
from app import routes_dashboard


def create_app(config_name=None):
    """Factory function to create and configure the Flask application."""
    app = Flask(__name__, static_folder='static',
                static_url_path='/quizzen/assets',
                template_folder='templates')
    app.url_map.strict_slashes = False

    config_name = config_name or os.getenv('FLASK_ENV', 'default')
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    session.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    limiter.init_app(app)

    app.register_blueprint(full_bp)

    # print(app.url_map)
    logger.info("----- Quizzen app initialized -----")

    return app
